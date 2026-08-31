"""Acumulacao e reamostragem temporal dos quadros.

Duas pessoas executam o mesmo sinal em duracoes diferentes, e a mesma pessoa
varia entre repeticoes. O classificador, porem, exige tensores de formato fixo.
Este modulo resolve essa tensao.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from totem_aju.config import SEQUENCE_LENGTH
from totem_aju.errors import EmptySequenceError
from totem_aju.vision.schema import FrameLandmarks, LandmarkArray


def resample_sequence(
    sequence: LandmarkArray, length: int = SEQUENCE_LENGTH
) -> LandmarkArray:
    """Reamostra uma sequencia para ``length`` quadros por interpolacao linear.

    Args:
        sequence: matriz ``(n_frames, n_features)``.
        length: comprimento canonico de saida.

    O primeiro e o ultimo quadro sao preservados exatamente, porque marcam o
    inicio e o fim do movimento do sinal. Uma sequencia de um unico quadro e
    replicada, caso degenerado mas valido.

    Raises:
        EmptySequenceError: se a sequencia nao tiver quadros.
        ValueError: se ``length`` nao for positivo.
    """
    if length <= 0:
        raise ValueError(f"'length' deve ser positivo, recebido {length}.")
    if sequence.ndim != 2:
        raise ValueError(
            f"A sequencia deve ser 2-D (quadros, features), "
            f"recebido ndim={sequence.ndim}."
        )
    n_frames = sequence.shape[0]
    if n_frames == 0:
        raise EmptySequenceError()
    if n_frames == 1:
        return np.repeat(sequence, length, axis=0).astype(np.float32, copy=False)
    if n_frames == length:
        return sequence.astype(np.float32, copy=False)

    source_positions = np.linspace(0.0, 1.0, num=n_frames)
    target_positions = np.linspace(0.0, 1.0, num=length)
    resampled = np.empty((length, sequence.shape[1]), dtype=np.float32)
    for feature in range(sequence.shape[1]):
        resampled[:, feature] = np.interp(
            target_positions, source_positions, sequence[:, feature]
        )
    return resampled


class SequenceBuffer:
    """Janela deslizante de quadros de landmarks.

    Responsabilidade unica: acumular quadros e entrega-los como um tensor de
    comprimento canonico. Nao sabe o que e um sinal, uma camera ou um arquivo.
    """

    def __init__(self, max_frames: int, sequence_length: int = SEQUENCE_LENGTH):
        """
        Args:
            max_frames: capacidade da janela. Quadros mais antigos sao
                descartados quando ela transborda.
            sequence_length: comprimento da sequencia produzida por
                :meth:`to_array`.
        """
        if max_frames <= 0:
            raise ValueError(f"'max_frames' deve ser positivo, recebido {max_frames}.")
        if sequence_length <= 0:
            raise ValueError(
                f"'sequence_length' deve ser positivo, recebido {sequence_length}."
            )
        self._frames: deque[FrameLandmarks] = deque(maxlen=max_frames)
        self._sequence_length = sequence_length

    def append(self, frame: FrameLandmarks) -> None:
        """Adiciona um quadro ao fim da janela."""
        self._frames.append(frame)

    def clear(self) -> None:
        """Descarta todos os quadros acumulados."""
        self._frames.clear()

    def __len__(self) -> int:
        return len(self._frames)

    @property
    def is_empty(self) -> bool:
        return not self._frames

    @property
    def max_frames(self) -> int:
        return self._frames.maxlen or 0

    @property
    def detection_ratio(self) -> float:
        """Fracao de quadros com ao menos uma mao detectada.

        Serve como indicador de qualidade: uma amostra com razao baixa
        provavelmente registrou um enquadramento ruim e deve ser refeita.
        """
        if not self._frames:
            return 0.0
        detected = sum(1 for frame in self._frames if frame.has_any_hand)
        return detected / len(self._frames)

    def to_array(self) -> LandmarkArray:
        """Devolve a janela como tensor ``(sequence_length, n_features)``.

        Raises:
            EmptySequenceError: se nenhum quadro foi acumulado.
        """
        if not self._frames:
            raise EmptySequenceError()
        stacked = np.stack([frame.to_vector() for frame in self._frames])
        return resample_sequence(stacked, self._sequence_length)
