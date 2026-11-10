"""
Gestor e indexador de la Galería de Referencia (Few-Shot Exemplar Gallery).

La galería se organiza mediante el catálogo de perfiles. Las carpetas históricas
de trips (huevo, larva, pupa, adulto, dano_gulupa) se conservan, y los perfiles
nuevos usan ``perfil/objetivo/estadio``. Esto permite añadir moscas o arañas
rojas sin cambiar el indexador ni la API.
"""

import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torch.nn.functional as F
from PIL import Image, ImageOps

from backend.app.config import GALLERY_DIR, GALLERY_INDEX_PATH, KNN_TOP_K
from backend.app.domain.catalog import (
    GALLERY_LABELS,
    GalleryLabel,
)
from backend.app.schemas.prediction import ExemplarMatch

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class GalleryManager:
    def __init__(self):
        self.embeddings: Optional[torch.Tensor] = None
        self.metadata: List[Dict[str, Any]] = []
        self.file_signature: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._ensure_directories()
        self.load_index()

    # ------------------------------------------------------------------
    # Estructura en disco
    # ------------------------------------------------------------------
    def _ensure_directories(self) -> None:
        """Crea la raíz y todas las carpetas del catálogo de galería."""

        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        for label in GALLERY_LABELS.values():
            (GALLERY_DIR / label.key).mkdir(parents=True, exist_ok=True)

    def _label_dir(self, label: GalleryLabel) -> Path:
        return GALLERY_DIR / label.key

    def _iter_files(self) -> List[tuple]:
        """Devuelve (label, ruta) para cada imagen registrada en el catálogo."""

        found: List[tuple] = []
        for label in GALLERY_LABELS.values():
            directory = self._label_dir(label)
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
                    found.append((label, path))
        return found

    def _current_file_signature(self) -> Dict[str, Dict[str, Any]]:
        signature: Dict[str, Dict[str, Any]] = {}
        for label, path in self._iter_files():
            relative_path = str(path.relative_to(GALLERY_DIR))
            stat = path.stat()
            signature[relative_path] = {
                "size": int(stat.st_size),
                "mtime_ns": int(stat.st_mtime_ns),
                "label": label.key,  # type: ignore[dict-item]
            }
        return signature

    # ------------------------------------------------------------------
    # Persistencia del índice
    # ------------------------------------------------------------------
    def load_index(self) -> bool:
        """Carga el índice de embeddings precomputados si existe."""

        with self._lock:
            if not GALLERY_INDEX_PATH.exists():
                self.embeddings = None
                self.metadata = []
                self.file_signature = {}
                return False
            try:
                try:
                    data = torch.load(
                        GALLERY_INDEX_PATH, map_location="cpu", weights_only=True
                    )
                except Exception:
                    # Compatibilidad con índices creados por versiones anteriores.
                    data = torch.load(
                        GALLERY_INDEX_PATH, map_location="cpu", weights_only=False
                    )
                self.embeddings = data.get("embeddings")
                self.metadata = data.get("metadata", []) or []
                self.file_signature = data.get("file_signature", {}) or {}
                if self.embeddings is not None and self.embeddings.dim() == 1:
                    self.embeddings = self.embeddings.unsqueeze(0)
                return True
            except Exception as exc:
                print(f"[GalleryManager] Error cargando índice existente: {exc}")
                self.embeddings = None
                self.metadata = []
                self.file_signature = {}
                return False

    def save_index(self) -> None:
        """Guarda embeddings, metadatos y firma de archivos de forma atómica."""

        with self._lock:
            if self.embeddings is None or not self.metadata:
                if GALLERY_INDEX_PATH.exists():
                    GALLERY_INDEX_PATH.unlink()
                return

            GALLERY_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "embeddings": self.embeddings.cpu(),
                "metadata": self.metadata,
                "file_signature": self.file_signature,
            }
            tmp_path = GALLERY_INDEX_PATH.with_suffix(".tmp")
            torch.save(payload, tmp_path)
            tmp_path.replace(GALLERY_INDEX_PATH)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def get_gallery_stats(self) -> Dict[str, Any]:
        """Conteo por carpeta/perfil y estado de frescura del índice."""

        with self._lock:
            by_label: Dict[str, int] = {label_key: 0 for label_key in GALLERY_LABELS}
            by_profile: Dict[str, int] = {}
            by_target: Dict[str, int] = {}

            for label, _path in self._iter_files():
                by_label[label.key] = by_label.get(label.key, 0) + 1
                by_profile[label.profile] = by_profile.get(label.profile, 0) + 1
                by_target[label.target] = by_target.get(label.target, 0) + 1

            total = sum(by_label.values())
            current_signature = self._current_file_signature()
            signature_matches = current_signature == self.file_signature
            # Los índices antiguos no tenían firma; se valida por conteo.
            if not self.file_signature:
                signature_matches = (
                    self.embeddings is not None and len(self.metadata) == total
                )
            is_indexed = (
                self.embeddings is not None
                and len(self.metadata) == total
                and signature_matches
            )

            return {
                "total_images": total,
                "by_stage": by_label,
                "by_label": by_label,
                "by_profile": by_profile,
                "by_target": by_target,
                "is_indexed": bool(is_indexed),
                "is_stale": not bool(is_indexed),
                "indexed_images": len(self.metadata),
                "index_path": str(GALLERY_INDEX_PATH),
            }

    def list_items(self) -> List[Dict[str, Any]]:
        """Lista las imágenes existentes con su perfil, objetivo y estadio."""

        with self._lock:
            items: List[Dict[str, Any]] = []
            for label, path in self._iter_files():
                items.append(
                    {
                        "filename": path.name,
                        "stage": label.stage or label.key,
                        "label": label.key,
                        "label_key": label.key,
                        "target": label.target,
                        "profile": label.profile,
                        "display_name": label.display_name,
                        "relative_path": str(path.relative_to(GALLERY_DIR)),
                        "file_size_bytes": path.stat().st_size,
                    }
                )
            return items

    # ------------------------------------------------------------------
    # Indexación
    # ------------------------------------------------------------------
    def rebuild_index(self, model, preprocess, device: torch.device) -> int:
        """Escanea todas las fotos del catálogo y reconstruye el índice."""

        with self._lock:
            new_embeddings: List[torch.Tensor] = []
            new_metadata: List[Dict[str, Any]] = []
            new_signature: Dict[str, Dict[str, Any]] = {}

            model.eval()
            with torch.no_grad():
                for label, path in self._iter_files():
                    try:
                        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
                        tensor = preprocess(image).unsqueeze(0).to(device)
                        embedding = model.encode_image(tensor)
                        embedding = F.normalize(embedding, p=2, dim=-1)

                        relative_path = str(path.relative_to(GALLERY_DIR))
                        stat = path.stat()
                        new_embeddings.append(embedding.cpu())
                        new_metadata.append(
                            {
                                "filename": path.name,
                                "stage": label.stage or label.key,
                                "label": label.key,
                                "target": label.target,
                                "profile": label.profile,
                                "relative_path": relative_path,
                                "path": str(path),
                            }
                        )
                        new_signature[relative_path] = {
                            "size": int(stat.st_size),
                            "mtime_ns": int(stat.st_mtime_ns),
                            "label": label.key,  # type: ignore[dict-item]
                        }
                    except Exception as exc:
                        print(f"[GalleryManager] Error indexando {path.name}: {exc}")

            if new_embeddings:
                self.embeddings = torch.cat(new_embeddings, dim=0)
                self.metadata = new_metadata
                self.file_signature = new_signature
                self.save_index()
                print(
                    f"[GalleryManager] Índice reconstruido con "
                    f"{len(self.metadata)} imágenes."
                )
                return len(self.metadata)

            self.embeddings = None
            self.metadata = []
            self.file_signature = {}
            if GALLERY_INDEX_PATH.exists():
                GALLERY_INDEX_PATH.unlink()
            return 0

    # ------------------------------------------------------------------
    # Búsqueda k-NN
    # ------------------------------------------------------------------
    def query_nearest(
        self,
        query_embedding: torch.Tensor,
        top_k: int = KNN_TOP_K,
        profile: Optional[str] = None,
    ) -> List[ExemplarMatch]:
        """Busca los ejemplares más similares, opcionalmente dentro de un perfil."""

        with self._lock:
            if self.embeddings is None or not self.metadata:
                return []
            if self.embeddings.shape[0] != len(self.metadata):
                return []

            indices = list(range(len(self.metadata)))
            if profile:
                indices = [
                    idx
                    for idx in indices
                    if self.metadata[idx].get("profile", "trips") == profile
                ]
            if not indices:
                return []

            query_emb = query_embedding.cpu()
            if query_emb.dim() == 1:
                query_emb = query_emb.unsqueeze(0)

            selected_embeddings = self.embeddings[indices]
            similarities = torch.mm(query_emb, selected_embeddings.t()).squeeze(0)

            k = min(top_k, len(indices))
            top_scores, top_positions = torch.topk(similarities, k=k)

            results: List[ExemplarMatch] = []
            for score, position in zip(top_scores.tolist(), top_positions.tolist()):
                meta = self.metadata[indices[position]]
                results.append(
                    ExemplarMatch(
                        filename=meta.get("filename", "desconocido"),
                        stage=meta.get("stage", "desconocido"),
                        similarity=round(max(0.0, min(float(score), 1.0)), 4),
                        target=meta.get("target"),
                        profile=meta.get("profile"),
                        label=meta.get("label"),
                    )
                )
            return results


gallery_manager = GalleryManager()
