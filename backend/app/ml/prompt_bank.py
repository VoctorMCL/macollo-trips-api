"""
Banco de embeddings de texto con ensamble de prompts.

Cada objetivo y cada estadio pueden tener varios prompts. En lugar de usar un
único texto (frágil ante cambios de redacción), se codifican todos los prompts
y se promedia su embedding normalizado. El resultado es un prototipo textual
más estable para la comparación zero-shot con BioCLIP.

Los prototipos se persisten en ``data/prompt_embeddings.pt`` con una firma del
catálogo y del modelo: en el arranque en frío se cargan del disco (milisegundos)
en lugar de re-codificar ~100 prompts con el codificador de texto en CPU
(decenas de segundos). Si el catálogo o el modelo cambian, la firma no coincide
y se recalcula todo automáticamente.
"""

import hashlib
import threading
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F

from backend.app.config import PROMPT_CACHE_PATH
from backend.app.domain.catalog import DetectionProfile, get_target, list_profiles


class PromptBank:
    """Cachea y ensambla los embeddings de texto por perfil de detección."""

    CACHE_VERSION = 2

    def __init__(self, model, tokenizer, device: torch.device):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self._target_cache: Dict[str, Tuple[List[str], torch.Tensor]] = {}
        self._stage_cache: Dict[str, Tuple[List[str], torch.Tensor]] = {}
        self._lock = threading.RLock()

    def _encode(self, texts: List[str]) -> torch.Tensor:
        tokens = self.tokenizer(texts).to(self.device)
        with torch.no_grad():
            embeddings = self.model.encode_text(tokens)
        return F.normalize(embeddings, p=2, dim=-1)

    def _ensemble(self, prompts_list: List[Tuple[str, ...]]) -> torch.Tensor:
        """Promedia los prompts de cada clase y devuelve prototipos normalizados."""

        if not prompts_list:
            return torch.empty((0, 0), device=self.device)

        flat_prompts: List[str] = []
        class_sizes: List[int] = []
        for prompts in prompts_list:
            flat_prompts.extend(prompts)
            class_sizes.append(len(prompts))

        flat_embeddings = self._encode(flat_prompts)

        prototypes = []
        offset = 0
        for size in class_sizes:
            chunk = flat_embeddings[offset:offset + size]
            prototype = chunk.mean(dim=0)
            prototypes.append(F.normalize(prototype, p=2, dim=-1))
            offset += size
        return torch.stack(prototypes, dim=0)

    def target_embeddings(self, profile: DetectionProfile) -> Tuple[List[str], torch.Tensor]:
        with self._lock:
            cached = self._target_cache.get(profile.key)
            if cached is not None:
                return cached

            keys = list(profile.target_keys)
            prompts_list = [get_target(key).prompts for key in keys]
            embeddings = self._ensemble(prompts_list)
            self._target_cache[profile.key] = (keys, embeddings)
            return keys, embeddings

    def stage_embeddings(self, profile: DetectionProfile) -> Tuple[List[str], torch.Tensor]:
        with self._lock:
            cached = self._stage_cache.get(profile.key)
            if cached is not None:
                return cached

            keys = list(profile.stages.keys())
            prompts_list = [profile.stages[key].prompts for key in keys]
            embeddings = self._ensemble(prompts_list)
            self._stage_cache[profile.key] = (keys, embeddings)
            return keys, embeddings

    def invalidate(self) -> None:
        with self._lock:
            self._target_cache.clear()
            self._stage_cache.clear()

    # ------------------------------------------------------------------
    # Persistencia (evita re-codificar prompts en cada cold start)
    # ------------------------------------------------------------------
    @staticmethod
    def _catalog_signature(model_name: str) -> str:
        """Hash del modelo + todos los prompts del catálogo.

        Cualquier cambio de prompts, objetivos, estadios o perfiles produce
        una firma distinta y fuerza el recálculo de los prototipos.
        """

        digest = hashlib.sha256()
        digest.update(f"v{PromptBank.CACHE_VERSION}".encode())
        digest.update(model_name.encode())
        for profile in list_profiles():
            digest.update(f"\nprofile:{profile.key}".encode())
            for target_key in profile.target_keys:
                digest.update(f"\ntarget:{target_key}".encode())
                for prompt in get_target(target_key).prompts:
                    digest.update(prompt.encode())
            for stage_key, stage in profile.stages.items():
                digest.update(f"\nstage:{stage_key}".encode())
                for prompt in stage.prompts:
                    digest.update(prompt.encode())
        return digest.hexdigest()

    def load_cache(self, model_name: str) -> bool:
        """Carga los prototipos precacheados si la firma del catálogo coincide."""

        try:
            if not PROMPT_CACHE_PATH.exists():
                return False
            data = torch.load(
                PROMPT_CACHE_PATH, map_location="cpu", weights_only=True
            )
            if data.get("signature") != self._catalog_signature(model_name):
                print(
                    "[PromptBank] Caché de prompts desactualizada "
                    "(catálogo o modelo cambiado); recalculando..."
                )
                return False

            targets = data.get("targets") or {}
            stages = data.get("stages") or {}
            with self._lock:
                for profile_key, entry in targets.items():
                    keys = list(entry["keys"])
                    embeddings = entry["embeddings"].to(self.device)
                    self._target_cache[profile_key] = (keys, embeddings)
                for profile_key, entry in stages.items():
                    keys = list(entry["keys"])
                    embeddings = entry["embeddings"].to(self.device)
                    self._stage_cache[profile_key] = (keys, embeddings)
            total = len(targets) + len(stages)
            print(
                f"[PromptBank] {total} bancos de prototipos cargados desde caché "
                f"({PROMPT_CACHE_PATH.name})."
            )
            return True
        except Exception as exc:
            print(f"[PromptBank] No se pudo leer la caché de prompts: {exc}")
            return False

    def save_cache(self, model_name: str) -> bool:
        """Guarda los prototipos actuales con su firma para el próximo arranque."""

        with self._lock:
            if not self._target_cache and not self._stage_cache:
                return False
            payload = {
                "version": self.CACHE_VERSION,
                "signature": self._catalog_signature(model_name),
                "targets": {
                    profile_key: {
                        "keys": keys,
                        "embeddings": embeddings.detach().cpu(),
                    }
                    for profile_key, (keys, embeddings) in self._target_cache.items()
                },
                "stages": {
                    profile_key: {
                        "keys": keys,
                        "embeddings": embeddings.detach().cpu(),
                    }
                    for profile_key, (keys, embeddings) in self._stage_cache.items()
                },
            }
        try:
            PROMPT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = PROMPT_CACHE_PATH.with_suffix(".tmp")
            torch.save(payload, tmp_path)
            tmp_path.replace(PROMPT_CACHE_PATH)
            print(
                f"[PromptBank] Prototipos guardados en caché ({PROMPT_CACHE_PATH.name})."
            )
            return True
        except Exception as exc:
            print(f"[PromptBank] No se pudo guardar la caché de prompts: {exc}")
            return False
