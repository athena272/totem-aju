"""Contagem de dedos baseada nas heuristicas geometricas da camada de visao."""

from __future__ import annotations

from totem_aju.vision.heuristics import avaliar_dedos
from totem_aju.vision.schema import FrameLandmarks
from totem_aju.vision.smoothing import TemporalGestureFilter


class HeuristicFingerCounter:
    """Soma os dedos abertos de uma mao, com a suavizacao temporal do filtro.

    Usa a mao direita quando ela aparece e a esquerda quando so ela aparece.
    Com as duas no quadro, contar so uma evita somas acidentais quando a outra
    mao entra parcialmente na imagem.
    """

    def __init__(self, gesture_filter: TemporalGestureFilter | None = None) -> None:
        self._filter = gesture_filter or TemporalGestureFilter()

    def count(self, landmarks: FrameLandmarks) -> int | None:
        if landmarks.right_hand_detected:
            key, hand = "right", landmarks.right_hand
        elif landmarks.left_hand_detected:
            key, hand = "left", landmarks.left_hand
        else:
            return None

        smoothed = self._filter.suavizar_landmarks(key, hand)
        fingers, _ = avaliar_dedos(smoothed)
        return sum(self._filter.dedos_estaveis(key, fingers))
