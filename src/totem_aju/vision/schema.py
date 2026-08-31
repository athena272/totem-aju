"""Estruturas de dados dos landmarks de um quadro.

Este modulo nao conhece webcam, MediaPipe nem disco: define apenas o formato
dos dados que circulam pelo pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from totem_aju.config import (
    COORDS_PER_LANDMARK,
    HAND_LANDMARK_COUNT,
    POSE_LANDMARK_COUNT,
)

#: Matriz de landmarks: uma linha por ponto, colunas (x, y, z).
LandmarkArray = NDArray[np.float32]

HAND_SHAPE = (HAND_LANDMARK_COUNT, COORDS_PER_LANDMARK)
POSE_SHAPE = (POSE_LANDMARK_COUNT, COORDS_PER_LANDMARK)

#: Dimensao do vetor achatado de um quadro (duas maos + pose).
FRAME_VECTOR_SIZE = (2 * HAND_LANDMARK_COUNT + POSE_LANDMARK_COUNT) * (
    COORDS_PER_LANDMARK
)


def empty_hand() -> LandmarkArray:
    """Mao ausente, representada por zeros."""
    return np.zeros(HAND_SHAPE, dtype=np.float32)


def empty_pose() -> LandmarkArray:
    """Pose ausente, representada por zeros."""
    return np.zeros(POSE_SHAPE, dtype=np.float32)


@dataclass(frozen=True, slots=True)
class FrameLandmarks:
    """Landmarks detectados em um unico quadro.

    Imutavel de proposito: instancias circulam por buffers e listas, e a
    mutacao acidental de um array compartilhado seria um bug dificil de
    rastrear. Maos nao detectadas sao representadas por zeros, com a flag
    correspondente em ``False``, e nao por ``None`` -- assim todo quadro tem o
    mesmo formato e o classificador nunca recebe entrada de tamanho variavel.
    """

    left_hand: LandmarkArray
    right_hand: LandmarkArray
    pose: LandmarkArray
    left_hand_detected: bool
    right_hand_detected: bool

    def __post_init__(self) -> None:
        self._validate("left_hand", self.left_hand, HAND_SHAPE)
        self._validate("right_hand", self.right_hand, HAND_SHAPE)
        self._validate("pose", self.pose, POSE_SHAPE)

    @staticmethod
    def _validate(name: str, array: LandmarkArray, expected: tuple[int, int]) -> None:
        if array.shape != expected:
            raise ValueError(
                f"'{name}' deve ter shape {expected}, recebido {array.shape}."
            )

    @classmethod
    def empty(cls) -> FrameLandmarks:
        """Quadro sem nenhuma deteccao."""
        return cls(
            left_hand=empty_hand(),
            right_hand=empty_hand(),
            pose=empty_pose(),
            left_hand_detected=False,
            right_hand_detected=False,
        )

    @property
    def has_any_hand(self) -> bool:
        """Indica se ao menos uma mao foi detectada."""
        return self.left_hand_detected or self.right_hand_detected

    def to_vector(self) -> LandmarkArray:
        """Achata o quadro em um vetor 1-D para alimentar o classificador."""
        return np.concatenate(
            (
                self.left_hand.ravel(),
                self.right_hand.ravel(),
                self.pose.ravel(),
            )
        ).astype(np.float32, copy=False)
