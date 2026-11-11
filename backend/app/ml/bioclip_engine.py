"""
Motor de inferencia BioCLIP 2.5 para clasificación fitosanitaria extensible.

El motor es genérico respecto al catálogo: recibe un ``profile`` (trips, moscas,
aranas_rojas...) y clasifica sus objetivos y estadios. Incluye ensamble de
prompts, calibración por margen, votación suave de la galería y test-time
augmentation opcional.
"""

import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import open_clip
import torch
import torch.nn.functional as F
from PIL import Image, ImageOps

from backend.app.agronomy.registry import get_agronomy
from backend.app.config import (
    BIOCLIP_MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    ENABLE_TTA,
    FALLBACK_MODEL_NAME,
    GALLERY_MAX_BOOST,
    GALLERY_MIN_SIMILARITY,
    KNN_TOP_K,
)
from backend.app.domain.catalog import (
    DEFAULT_PROFILE_KEY,
    DetectionProfile,
    get_profile,
    get_target,
    list_profiles,
)
from backend.app.ml.gallery_index import gallery_manager
from backend.app.ml.prompt_bank import PromptBank


class BioCLIPEngine:
    def __init__(self):
        self.device = self._detect_device()
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.prompt_bank: Optional[PromptBank] = None

        self.is_loaded = False
        self.loaded_model_name = ""
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @staticmethod
    def _detect_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    # ------------------------------------------------------------------
    # Carga del modelo
    # ------------------------------------------------------------------
    def load_model(self) -> None:
        """Carga BioCLIP 2.5 y precalcula los prototipos de texto del catálogo."""

        with self._load_lock:
            if self.is_loaded:
                return

            print(f"[BioCLIPEngine] Inicializando en dispositivo: {self.device}")
            if self.device.type == "cpu":
                torch.set_num_threads(min(8, torch.get_num_threads()))

            model_name = BIOCLIP_MODEL_NAME
            try:
                print(f"[BioCLIPEngine] Cargando pesos de {model_name}...")
                self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    model_name, device=self.device
                )
                self.tokenizer = open_clip.get_tokenizer(model_name)
                self.loaded_model_name = model_name
            except Exception as exc:
                print(f"[BioCLIPEngine] No se pudo cargar {model_name}: {exc}")
                print(
                    f"[BioCLIPEngine] Intentando modelo alternativo "
                    f"{FALLBACK_MODEL_NAME}..."
                )
                self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    FALLBACK_MODEL_NAME, device=self.device
                )
                self.tokenizer = open_clip.get_tokenizer(FALLBACK_MODEL_NAME)
                self.loaded_model_name = FALLBACK_MODEL_NAME

            self.model.eval()
            self.prompt_bank = PromptBank(self.model, self.tokenizer, self.device)
            self._precompute_text_embeddings()

            stats = gallery_manager.get_gallery_stats()
            if stats["total_images"] > 0 and not stats["is_indexed"]:
                print("[BioCLIPEngine] Reindexando galería existente...")
                gallery_manager.rebuild_index(
                    self.model, self.preprocess, self.device
                )

            self.is_loaded = True
            print(f"[BioCLIPEngine] Modelo {self.loaded_model_name} listo.")

    def _precompute_text_embeddings(self) -> None:
        """Precalcula y valida los prototipos de texto de todos los perfiles."""

        if self.prompt_bank is None:
            return
        print("[BioCLIPEngine] Precalculando prototipos de texto del catálogo...")
        for profile in list_profiles():
            self.prompt_bank.target_embeddings(profile)
            self.prompt_bank.stage_embeddings(profile)
        print("[BioCLIPEngine] Prototipos de texto listos.")

    # ------------------------------------------------------------------
    # Embeddings de imagen
    # ------------------------------------------------------------------
    def _encode_image(self, image: Image.Image) -> torch.Tensor:
        if self.preprocess is None or self.model is None:
            raise RuntimeError("El modelo BioCLIP no está cargado.")

        rgb_image = ImageOps.exif_transpose(image).convert("RGB")
        tensor = self.preprocess(rgb_image).unsqueeze(0).to(self.device)
        with self._inference_lock, torch.inference_mode():
            embedding = self.model.encode_image(tensor)
            embedding = F.normalize(embedding, p=2, dim=-1)
        return embedding

    def extract_image_embedding(
        self, image: Image.Image, use_tta: Optional[bool] = None
    ) -> torch.Tensor:
        """Extrae el embedding normalizado; con TTA promedia original y espejo."""

        if not self.is_loaded:
            self.load_model()

        tta_enabled = ENABLE_TTA if use_tta is None else bool(use_tta)
        if not tta_enabled:
            return self._encode_image(image)

        views = [image, ImageOps.mirror(ImageOps.exif_transpose(image).convert("RGB"))]
        embeddings = [self._encode_image(view) for view in views]
        combined = torch.stack(embeddings, dim=0).mean(dim=0)
        return F.normalize(combined, p=2, dim=-1)

    # ------------------------------------------------------------------
    # Helpers de clasificación
    # ------------------------------------------------------------------
    @staticmethod
    def _softmax_tensor(similarities: torch.Tensor, logit_scale: float) -> List[float]:
        logits = similarities * logit_scale
        return F.softmax(logits, dim=0).cpu().tolist()

    def _logit_scale(self) -> float:
        if self.model is None:
            return 100.0
        scale_tensor = getattr(self.model, "logit_scale", None)
        if scale_tensor is None:
            return 100.0
        try:
            scale = float(torch.clamp(scale_tensor.detach().exp(), max=100.0).item())
            return max(1.0, scale)
        except Exception:
            return 100.0

    def _gallery_evidence(
        self, image_emb: torch.Tensor, profile: DetectionProfile
    ) -> Tuple[List[Any], float, Optional[str], Dict[str, float]]:
        """Consulta la galería y devuelve votos suaves por objetivo y estadio."""

        matches = gallery_manager.query_nearest(
            image_emb, top_k=KNN_TOP_K, profile=profile.key
        )
        if not matches:
            return [], 0.0, None, {}

        target_votes: Dict[str, float] = {}
        stage_votes: Dict[str, float] = {}
        total_weight = 0.0

        for match in matches:
            if match.similarity < GALLERY_MIN_SIMILARITY:
                continue
            weight = match.similarity - GALLERY_MIN_SIMILARITY + 0.05
            total_weight += weight
            if match.target:
                target_votes[match.target] = target_votes.get(match.target, 0.0) + weight
            if match.stage:
                stage_votes[match.stage] = stage_votes.get(match.stage, 0.0) + weight

        if total_weight <= 0:
            return matches, 0.0, None, {}

        top_target = max(target_votes, key=target_votes.get) if target_votes else None
        boost = 0.0
        if top_target and profile.is_positive_target(top_target):
            share = target_votes[top_target] / total_weight
            boost = min(GALLERY_MAX_BOOST, GALLERY_MAX_BOOST * share)

        return matches, boost, top_target, stage_votes

    # ------------------------------------------------------------------
    # Inferencia
    # ------------------------------------------------------------------
    def predict(
        self,
        image: Image.Image,
        temperature_c: float = 20.0,
        profile_key: str = "trips",
        use_tta: Optional[bool] = None,
        crop: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ejecuta el pipeline completo de inferencia para un perfil del catálogo."""

        started_at = time.perf_counter()
        if not self.is_loaded:
            self.load_model()
        if self.prompt_bank is None:
            raise RuntimeError("El banco de prompts no está inicializado.")

        profile = get_profile(profile_key)
        image_emb = self.extract_image_embedding(image, use_tta=use_tta)
        logit_scale = self._logit_scale()

        # 1. Clasificación de objetivos del perfil
        target_keys, target_embeddings = self.prompt_bank.target_embeddings(profile)
        target_sims = (image_emb @ target_embeddings.t()).squeeze(0)
        target_probs_list = self._softmax_tensor(target_sims, logit_scale)
        target_probs = {
            key: float(prob) for key, prob in zip(target_keys, target_probs_list)
        }

        positive_keys = [
            key for key in profile.positive_target_keys if key in target_probs
        ]
        negative_keys = [key for key in target_keys if key not in positive_keys]
        positive_prob = sum(target_probs.get(key, 0.0) for key in positive_keys)

        top_target_key = max(target_probs, key=target_probs.get)
        best_positive_key = (
            max(positive_keys, key=target_probs.get) if positive_keys else top_target_key
        )
        best_negative_key = (
            max(negative_keys, key=target_probs.get) if negative_keys else None
        )
        margin = target_probs.get(best_positive_key, 0.0)
        if best_negative_key:
            margin -= target_probs.get(best_negative_key, 0.0)

        # 2. Evidencia de la galería (few-shot)
        exemplar_matches, gallery_boost, gallery_target, gallery_stage_votes = (
            self._gallery_evidence(image_emb, profile)
        )
        confidence = min(1.0, positive_prob + gallery_boost)
        # En trips se respeta el umbral global histórico (CONFIDENCE_THRESHOLD).
        # Los perfiles nuevos usan su propio umbral calibrado.
        threshold = (
            CONFIDENCE_THRESHOLD
            if profile.key == DEFAULT_PROFILE_KEY
            else profile.min_confidence
        )
        is_positive = confidence >= threshold
        is_uncertain = (
            (not is_positive and confidence >= threshold - 0.10)
            or (is_positive and margin < profile.min_margin)
        )

        display_target_key = best_positive_key if is_positive else top_target_key
        display_target = get_target(display_target_key)
        top_target = get_target(top_target_key)

        # En modo auto, determinar el perfil biológico de la plaga ganadora
        effective_profile = profile
        if profile.key == "auto":
            if top_target_key.startswith("trips") or display_target_key.startswith("trips"):
                effective_profile = get_profile("trips")
            elif top_target_key.startswith("mosca_frutal") or display_target_key.startswith("mosca_frutal"):
                effective_profile = get_profile("moscas")
            elif top_target_key.startswith("arana_roja") or display_target_key.startswith("arana_roja"):
                effective_profile = get_profile("aranas_rojas")

        is_damage = (
            top_target.kind == "damage"
            or display_target.kind == "damage"
        )

        # 3. Estadio biológico o severidad
        stage_profile = effective_profile if effective_profile.key != "auto" else profile
        stage_keys, stage_embeddings = self.prompt_bank.stage_embeddings(stage_profile)
        stage_scores: Dict[str, float] = {}
        best_stage_key = ""
        best_stage_name = ""
        best_stage_confidence = 0.0

        if stage_keys and stage_embeddings.numel() > 0:
            stage_sims = (image_emb @ stage_embeddings.t()).squeeze(0)
            stage_probs_list = self._softmax_tensor(stage_sims, logit_scale)
            stage_scores = {
                key: float(prob)
                for key, prob in zip(stage_keys, stage_probs_list)
            }

            if gallery_stage_votes:
                vote_total = sum(gallery_stage_votes.values())
                if vote_total > 0:
                    for stage_key in stage_scores:
                        vote_share = gallery_stage_votes.get(stage_key, 0.0) / vote_total
                        stage_scores[stage_key] = (
                            stage_scores[stage_key] * 0.75 + vote_share * 0.25
                        )

            best_stage_key = max(stage_scores, key=stage_scores.get)
            best_stage_confidence = stage_scores[best_stage_key]
            best_stage_name = stage_profile.stages[best_stage_key].name
            if best_stage_key in stage_profile.damage_stage_keys:
                is_damage = True
        elif is_positive:
            best_stage_name = "Adulto / Colonia activa"

        # 4. Motor agronómico específico del perfil o plaga
        cycle_info = None
        recommendations = None
        if is_positive:
            cycle_info, recommendations = get_agronomy(
                profile_key=effective_profile.key,
                stage_key=best_stage_key,
                temperature_c=temperature_c,
                target_key=display_target_key,
                is_damage_only=is_damage,
            )

        # 5. Respuesta genérica + campos históricos para compatibilidad
        if display_target.scientific_name:
            detected_target = (
                f"{display_target.common_name} ({display_target.scientific_name})"
            )
        else:
            detected_target = display_target.common_name

        if is_positive:
            detected_stage = best_stage_name or display_target.common_name
        else:
            detected_stage = "N/A"

        is_thrips = bool(is_positive and (profile.key == "trips" or display_target_key.startswith("trips")))
        thrips_confidence = round(confidence, 4) if is_thrips else 0.0

        detection = {
            "profile": profile.key,
            "profile_name": profile.name,
            "detected_profile": effective_profile.key,
            "category": display_target.kind,
            "is_positive": bool(is_positive),
            "confidence": round(confidence, 4),
            "is_uncertain": bool(is_uncertain),
            "target_key": display_target.key,
            "target_name": display_target.common_name,
            "scientific_name": display_target.scientific_name,
            "target_description": display_target.description,
            "profile_experimental": profile.experimental,
            "scores": {
                key: round(value, 4) for key, value in target_probs.items()
            },
        }

        inference_time_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return {
            # Compatibilidad 1.x
            "is_thrips": is_thrips,
            "thrips_confidence": thrips_confidence,
            "detected_target": detected_target,
            "detected_stage": detected_stage,
            "stage_confidence": (
                round(best_stage_confidence, 4) if is_positive else 0.0
            ),
            "is_damage_manifestation": bool(is_damage and is_positive),
            "cycle_info": cycle_info,
            "recommendations": recommendations,
            "exemplar_matches": exemplar_matches,
            "inference_time_ms": inference_time_ms,
            # Contrato genérico 2.x
            "profile": profile.key,
            "crop": crop or profile.crop,
            "detection": detection,
            "diagnostics": {
                "model_used": self.loaded_model_name,
                "device": str(self.device),
                "profile": profile.key,
                "top_target_prompt_key": top_target_key,
                "best_positive_target_key": best_positive_key,
                "best_negative_target_key": best_negative_key,
                "positive_zero_shot_prob": round(positive_prob, 4),
                "margin": round(margin, 4),
                "confidence_threshold": threshold,
                "is_uncertain": bool(is_uncertain),
                "gallery_boost_applied": round(gallery_boost, 4),
                "gallery_target_vote": gallery_target,
                "gallery_stage_scores": {
                    key: round(value, 4)
                    for key, value in gallery_stage_votes.items()
                },
                "tta_enabled": bool(ENABLE_TTA if use_tta is None else use_tta),
                "temperature_input_c": temperature_c,
                "stage_scores": {
                    key: round(value, 4) for key, value in stage_scores.items()
                },
            },
        }


bioclip_engine = BioCLIPEngine()
