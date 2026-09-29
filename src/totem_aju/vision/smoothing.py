"""Filtro temporal e histerese para estabilização de gestos."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import numpy as np
from numpy.typing import NDArray

LandmarkArray = NDArray[np.float32]


class TemporalGestureFilter:
    """Aplica filtro EMA nos landmarks e histerese no histórico de dedos e gestos."""

    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha = alpha
        self.landmarks_suavizados: dict[str, LandmarkArray | None] = defaultdict(lambda: None)
        self.historico_dedos: dict[str, deque[tuple[int, ...]]] = defaultdict(
            lambda: deque(maxlen=6)
        )
        self.historico_gestos: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=8))
        self.historico_contagem: deque[int] = deque(maxlen=5)

    def suavizar_landmarks(self, chave: str, lm_list: LandmarkArray) -> LandmarkArray:
        atual = np.array(lm_list, dtype=np.float32)
        anterior = self.landmarks_suavizados[chave]

        if anterior is None or anterior.shape != atual.shape:
            suavizado = atual
        else:
            suavizado = (self.alpha * atual + (1 - self.alpha) * anterior).astype(np.float32)

        self.landmarks_suavizados[chave] = suavizado
        return suavizado

    def dedos_estaveis(self, chave: str, fingers: list[int]) -> list[int]:
        self.historico_dedos[chave].append(tuple(fingers))
        hist = list(self.historico_dedos[chave])
        n = len(hist)

        estaveis = []
        for i in range(5):
            abertos = sum(h[i] for h in hist)
            if abertos >= n * 0.6:
                estaveis.append(1)
            elif abertos <= n * 0.4:
                estaveis.append(0)
            else:
                estaveis.append(fingers[i])
        return estaveis

    def gesto_estavel(self, chave: str, gesto_atual: str) -> str:
        self.historico_gestos[chave].append(gesto_atual)
        contagem = Counter(self.historico_gestos[chave])
        gesto_mais_comum, freq = contagem.most_common(1)[0]

        if freq / len(self.historico_gestos[chave]) >= 0.6:
            return gesto_mais_comum
        return "..."