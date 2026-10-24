"""
Gestor e indexador de la Galería de Referencia (Few-Shot Exemplar Gallery) para BioCLIP.
Permite almacenar embeddings de fotos reales del usuario y buscar vecinos más cercanos por similitud de cosenos.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import torch
import torch.nn.functional as F

from backend.app.config import GALLERY_DIR, GALLERY_INDEX_PATH, STAGES, KNN_TOP_K
from backend.app.schemas.prediction import ExemplarMatch

class GalleryManager:
    def __init__(self):
        self.embeddings: Optional[torch.Tensor] = None
        self.metadata: List[Dict[str, Any]] = []
        self._ensure_directories()
        self.load_index()

    def _ensure_directories(self):
        """Asegura que los directorios de la galería existan en disco."""
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        for stage in STAGES:
            (GALLERY_DIR / stage).mkdir(parents=True, exist_ok=True)

    def load_index(self) -> bool:
        """Carga el archivo de embeddings precomputados si existe."""
        if GALLERY_INDEX_PATH.exists():
            try:
                data = torch.load(GALLERY_INDEX_PATH, map_location="cpu", weights_only=False)
                self.embeddings = data.get("embeddings")
                self.metadata = data.get("metadata", [])
                return True
            except Exception as e:
                print(f"[GalleryManager] Error cargando índice existente: {e}")
        self.embeddings = None
        self.metadata = []
        return False

    def save_index(self):
        """Guarda los embeddings y metadatos en disco."""
        if self.embeddings is not None and len(self.metadata) > 0:
            torch.save({
                "embeddings": self.embeddings.cpu(),
                "metadata": self.metadata
            }, GALLERY_INDEX_PATH)

    def get_gallery_stats(self) -> Dict[str, Any]:
        """Devuelve el conteo de imágenes en disco y estado de indexación."""
        stats = {stage: 0 for stage in STAGES}
        total = 0
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        
        for stage in STAGES:
            stage_dir = GALLERY_DIR / stage
            if stage_dir.exists():
                count = sum(1 for f in stage_dir.iterdir() if f.suffix.lower() in valid_extensions and f.is_file())
                stats[stage] = count
                total += count

        return {
            "total_images": total,
            "by_stage": stats,
            "is_indexed": self.embeddings is not None and len(self.metadata) == total,
            "index_path": str(GALLERY_INDEX_PATH)
        }

    def list_items(self) -> List[Dict[str, Any]]:
        """Lista todas las imágenes existentes en la galería."""
        items = []
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        for stage in STAGES:
            stage_dir = GALLERY_DIR / stage
            if stage_dir.exists():
                for f in stage_dir.iterdir():
                    if f.suffix.lower() in valid_extensions and f.is_file():
                        items.append({
                            "filename": f.name,
                            "stage": stage,
                            "relative_path": f"{stage}/{f.name}",
                            "file_size_bytes": f.stat().st_size
                        })
        return items

    def rebuild_index(self, model, preprocess, device: torch.device) -> int:
        """
        Escanea todas las fotos en la galería, extrae embeddings con BioCLIP y guarda el índice.
        """
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        new_embeddings_list = []
        new_metadata_list = []

        model.eval()
        with torch.no_grad():
            for stage in STAGES:
                stage_dir = GALLERY_DIR / stage
                if not stage_dir.exists():
                    continue
                
                for f in stage_dir.iterdir():
                    if f.suffix.lower() in valid_extensions and f.is_file():
                        try:
                            img = Image.open(f).convert("RGB")
                            tensor = preprocess(img).unsqueeze(0).to(device)
                            emb = model.encode_image(tensor)
                            emb = F.normalize(emb, p=2, dim=-1)
                            
                            new_embeddings_list.append(emb.cpu())
                            new_metadata_list.append({
                                "filename": f.name,
                                "stage": stage,
                                "path": str(f)
                            })
                        except Exception as e:
                            print(f"[GalleryManager] Error indexando {f.name}: {e}")

        if new_embeddings_list:
            self.embeddings = torch.cat(new_embeddings_list, dim=0)
            self.metadata = new_metadata_list
            self.save_index()
            print(f"[GalleryManager] Índice reconstruido con {len(self.metadata)} imágenes.")
            return len(self.metadata)
        else:
            self.embeddings = None
            self.metadata = []
            if GALLERY_INDEX_PATH.exists():
                GALLERY_INDEX_PATH.unlink()
            return 0

    def query_nearest(self, query_embedding: torch.Tensor, top_k: int = KNN_TOP_K) -> List[ExemplarMatch]:
        """
        Calcula la similitud de cosenos entre el embedding de la foto consultada
        y todos los ejemplares de la galería. Retorna los top_k más parecidos.
        """
        if self.embeddings is None or len(self.metadata) == 0:
            return []

        query_emb = query_embedding.cpu()
        if query_emb.dim() == 1:
            query_emb = query_emb.unsqueeze(0)
        
        # Similitud de cosenos (asumiendo vectores normalizados en L2)
        sims = torch.mm(query_emb, self.embeddings.t()).squeeze(0)
        
        k = min(top_k, len(self.metadata))
        top_scores, top_indices = torch.topk(sims, k=k)
        
        results = []
        for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
            meta = self.metadata[idx]
            # Similitud de cosenos directa (vectores L2-normalizados → rango real ~[0, 1])
            clamped_score = max(0.0, min(score, 1.0))
            results.append(ExemplarMatch(
                filename=meta["filename"],
                stage=meta["stage"],
                similarity=round(clamped_score, 4)
            ))
            
        return results

gallery_manager = GalleryManager()
