"""
Motor de inferencia BioCLIP 2.5 (ViT-H/14) para discriminación taxonómica de Trips,
clasificación de estadios biológicos y calibración con la Galería de Referencia.
"""

import time
from typing import Dict, Any, Tuple, Optional
from PIL import Image
import torch
import torch.nn.functional as F
import open_clip

from backend.app.config import (
    BIOCLIP_MODEL_NAME,
    FALLBACK_MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    settings
)
from backend.app.ml.taxonomy_prompts import (
    TAXONOMIC_TARGET_PROMPTS,
    BIOLOGICAL_STAGE_PROMPTS,
    POSITIVE_TRIPS_KEYS
)
from backend.app.ml.gallery_index import gallery_manager
from backend.app.agronomy.gulupa_cycle import get_gulupa_cycle_estimate
from backend.app.agronomy.gulupa_mip import get_gulupa_mip_recommendations

class BioCLIPEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        
        # Cache de embeddings de texto precalculados
        self.target_keys = []
        self.cached_target_text_embs = None
        self.stage_keys = []
        self.cached_stage_text_embs = None
        
        self.is_loaded = False
        self.loaded_model_name = ""

    def load_model(self):
        """Carga el modelo BioCLIP 2.5 y precalcula los embeddings de texto."""
        if self.is_loaded:
            return

        print(f"[BioCLIPEngine] Inicializando en dispositivo: {self.device}")
        # En CPUs multinúcleo como Intel Core i9-13900H, optimizar hilos
        if self.device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))

        # Intentar cargar BioCLIP 2.5
        model_name_to_try = BIOCLIP_MODEL_NAME
        try:
            print(f"[BioCLIPEngine] Descargando/Cargando pesos de {model_name_to_try}...")
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name_to_try,
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer(model_name_to_try)
            self.loaded_model_name = model_name_to_try
        except Exception as e:
            print(f"[BioCLIPEngine] Advertencia: No se pudo cargar {model_name_to_try}: {e}")
            print(f"[BioCLIPEngine] Intentando con modelo alternativo {FALLBACK_MODEL_NAME}...")
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                FALLBACK_MODEL_NAME,
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer(FALLBACK_MODEL_NAME)
            self.loaded_model_name = FALLBACK_MODEL_NAME

        self.model.eval()
        self._precompute_text_embeddings()
        
        # Si la galería tiene imágenes pero no ha sido indexada, indexar
        gallery_stats = gallery_manager.get_gallery_stats()
        if gallery_stats["total_images"] > 0 and not gallery_stats["is_indexed"]:
            print("[BioCLIPEngine] Reindexando galería existente con BioCLIP...")
            gallery_manager.rebuild_index(self.model, self.preprocess, self.device)

        self.is_loaded = True
        print(f"[BioCLIPEngine] Modelo {self.loaded_model_name} cargado y listo.")

    def _precompute_text_embeddings(self):
        """Precalcula los vectores de texto normalizados para inferencia en tiempo real."""
        print("[BioCLIPEngine] Precalculando embeddings de texto taxonómicos y de estadios...")
        
        # 1. Target Prompts (Trips vs Plagas / Vegetación)
        self.target_keys = list(TAXONOMIC_TARGET_PROMPTS.keys())
        target_texts = [TAXONOMIC_TARGET_PROMPTS[k] for k in self.target_keys]
        target_tokens = self.tokenizer(target_texts).to(self.device)
        
        with torch.no_grad():
            target_embs = self.model.encode_text(target_tokens)
            self.cached_target_text_embs = F.normalize(target_embs, p=2, dim=-1)

        # 2. Stage Prompts (Adulto, Ninfas, Pupa, Daño)
        self.stage_keys = list(BIOLOGICAL_STAGE_PROMPTS.keys())
        stage_texts = [BIOLOGICAL_STAGE_PROMPTS[k]["prompt"] for k in self.stage_keys]
        stage_tokens = self.tokenizer(stage_texts).to(self.device)
        
        with torch.no_grad():
            stage_embs = self.model.encode_text(stage_tokens)
            self.cached_stage_text_embs = F.normalize(stage_embs, p=2, dim=-1)

    def extract_image_embedding(self, image: Image.Image) -> torch.Tensor:
        """Extrae el embedding normalizado de una imagen PIL."""
        if not self.is_loaded:
            self.load_model()

        tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.model.encode_image(tensor)
            emb = F.normalize(emb, p=2, dim=-1)
        return emb

    def predict(self, image: Image.Image, temperature_c: float = 20.0) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de inferencia:
        1. Extracción de vector de la foto con BioCLIP 2.5
        2. Discriminación de Trips vs Falsos Positivos
        3. Identificación del estadio biológico
        4. Búsqueda en Galería de Referencia (Few-Shot k-NN)
        5. Cálculo térmico de ciclo de vida en Gulupa
        6. Recomendaciones agronómicas de Manejo Integrado de Plagas (MIP)
        """
        t0 = time.perf_counter()
        if not self.is_loaded:
            self.load_model()

        # 1. Extraer vector de características de la imagen
        image_emb = self.extract_image_embedding(image)
        
        # Logit scale (temperatura de contraste de CLIP)
        logit_scale = getattr(self.model, "logit_scale", torch.tensor(100.0)).exp().item()
        logit_scale = min(logit_scale, 100.0)

        # 2. Comparación taxonómica (Trips vs No-Trips)
        target_sims = (image_emb @ self.cached_target_text_embs.t()).squeeze(0)
        target_logits = target_sims * logit_scale
        target_probs = F.softmax(target_logits, dim=0).cpu().tolist()
        
        prob_dict = {k: target_probs[i] for i, k in enumerate(self.target_keys)}
        
        # Calcular probabilidad combinada de ser trips
        positive_prob = sum(prob_dict[k] for k in POSITIVE_TRIPS_KEYS if k in prob_dict)
        top_target_idx = int(torch.argmax(target_sims).item())
        top_target_key = self.target_keys[top_target_idx]

        # 3. Consulta a la Galería de Referencia de fotos reales
        exemplar_matches = gallery_manager.query_nearest(image_emb, top_k=3)
        gallery_boost = 0.0
        gallery_voted_stage = None
        
        if exemplar_matches:
            top_match = exemplar_matches[0]
            # Si el ejemplar más cercano supera similitud 0.65, aporta soporte empírico
            if top_match.similarity > 0.65:
                gallery_boost = (top_match.similarity - 0.65) * 0.4
                gallery_voted_stage = top_match.stage

        # Ajuste de confianza global de Trips con el voto de la galería
        thrips_confidence = min(1.0, positive_prob + gallery_boost)
        is_thrips = thrips_confidence >= CONFIDENCE_THRESHOLD

        # 4. Clasificación de Estadio Biológico
        stage_sims = (image_emb @ self.cached_stage_text_embs.t()).squeeze(0)
        stage_logits = stage_sims * logit_scale
        stage_probs = F.softmax(stage_logits, dim=0).cpu().tolist()
        
        # Si la galería votó con alta similitud, ponderar ligeramente el estadio correspondiente
        stage_scores = {}
        for i, sk in enumerate(self.stage_keys):
            score = stage_probs[i]
            if gallery_voted_stage == sk and exemplar_matches:
                score = (score * 0.7) + (exemplar_matches[0].similarity * 0.3)
            stage_scores[sk] = score

        best_stage_key = max(stage_scores, key=stage_scores.get)
        best_stage_conf = stage_scores[best_stage_key]
        stage_metadata = BIOLOGICAL_STAGE_PROMPTS.get(best_stage_key, {})
        detected_stage_name = stage_metadata.get("name", best_stage_key.capitalize())
        is_damage = (best_stage_key == "dano_gulupa" or top_target_key == "trips_dano_fruto_gulupa")

        # 5. Motor Agronómico para Gulupa
        if is_thrips:
            cycle_info = get_gulupa_cycle_estimate(best_stage_key, temperature_c)
            recommendations = get_gulupa_mip_recommendations(best_stage_key, is_damage_only=is_damage)
            detected_target = "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)"
        else:
            cycle_info = None
            recommendations = None
            # Describir qué se detectó si no fue trips
            labels_map = {
                "neg_mosca_blanca": "Mosca Blanca (Bemisia tabaci)",
                "neg_pulgon": "Pulgón (Aphididae)",
                "neg_arana_roja": "Araña Roja (Tetranychus urticae)",
                "neg_acaro_plano": "Ácaro Plano de Pasifloras (Brevipalpus)",
                "neg_mosca_minadora": "Mosca Minadora (Liriomyza)",
                "neg_hoja_sana_gulupa": "Hoja Sana de Gulupa",
                "neg_flor_sana_gulupa": "Flor Sana de Gulupa",
                "neg_zarcillo_tallo": "Estructura Vegetal / Tallo / Zarcillo",
                "neg_mancha_polvo_caldo": "Mancha de Caldo / Polvo / Gotas de Agua"
            }
            detected_target = labels_map.get(top_target_key, "No corresponde a Trips")

        t1 = time.perf_counter()
        inference_time_ms = round((t1 - t0) * 1000, 2)

        return {
            "is_thrips": is_thrips,
            "thrips_confidence": round(thrips_confidence, 4),
            "detected_target": detected_target,
            "detected_stage": detected_stage_name if is_thrips else "N/A",
            "stage_confidence": round(best_stage_conf, 4) if is_thrips else 0.0,
            "is_damage_manifestation": is_damage,
            "cycle_info": cycle_info,
            "recommendations": recommendations,
            "exemplar_matches": exemplar_matches,
            "diagnostics": {
                "model_used": self.loaded_model_name,
                "device": str(self.device),
                "top_target_prompt_key": top_target_key,
                "positive_zero_shot_prob": round(positive_prob, 4),
                "gallery_boost_applied": round(gallery_boost, 4),
                "temperature_input_c": temperature_c
            },
            "inference_time_ms": inference_time_ms
        }

bioclip_engine = BioCLIPEngine()
