"""
Banco de embeddings de texto con ensamble de prompts.

Cada objetivo y cada estadio pueden tener varios prompts. En lugar de usar un
único texto (frágil ante cambios de redacción), se codifican todos los prompts
y se promedia su embedding normalizado. El resultado es un prototipo textual
más estable para la comparación zero-shot con BioCLIP.
"""

import threading
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F

from backend.app.domain.catalog import DetectionProfile, get_target


class PromptBank:
    """Cachea y ensambla los embeddings de texto por perfil de detección."""

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
