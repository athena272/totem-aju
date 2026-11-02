"""Extracao de features a partir de sequencias de landmarks."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from totem_aju.config import FEATURE_FLATTEN, FEATURE_MEAN, FEATURE_MODES
from totem_aju.ml.dataset import LabeledSample, SampleArray
from totem_aju.vision.schema import FRAME_VECTOR_SIZE

FeatureMatrix = NDArray[np.float32]
LabelVector = NDArray[np.int64]


def extract_features(sequence: SampleArray, mode: str) -> NDArray[np.float32]:
    """Converte uma sequencia ``(T, F)`` em um vetor 1-D.

    Raises:
        ValueError: se ``mode`` nao for reconhecido.
    """
    if mode == FEATURE_MEAN:
        return sequence.mean(axis=0).astype(np.float32, copy=False)
    if mode == FEATURE_FLATTEN:
        return sequence.reshape(-1).astype(np.float32, copy=False)
    raise ValueError(
        f"Modo de features desconhecido: '{mode}'. " f"Use um de {FEATURE_MODES}."
    )


def feature_size(mode: str, sequence_length: int) -> int:
    """Dimensao do vetor produzido por ``extract_features``."""
    if mode == FEATURE_MEAN:
        return FRAME_VECTOR_SIZE
    if mode == FEATURE_FLATTEN:
        return sequence_length * FRAME_VECTOR_SIZE
    raise ValueError(
        f"Modo de features desconhecido: '{mode}'. " f"Use um de {FEATURE_MODES}."
    )


def samples_to_matrix(
    samples: tuple[LabeledSample, ...] | list[LabeledSample],
    *,
    mode: str,
) -> tuple[FeatureMatrix, LabelVector, tuple[str, ...]]:
    """Empilha features e rotulos de varias amostras.

    Returns:
        ``(X, y, signer_ids)`` com ``X`` de shape ``(n, d)``.
    """
    if not samples:
        empty_x = np.zeros((0, feature_size(mode, 1)), dtype=np.float32)
        empty_y = np.zeros(0, dtype=np.int64)
        return empty_x, empty_y, ()

    rows = [extract_features(sample.sequence, mode) for sample in samples]
    labels = [sample.label for sample in samples]
    signers = tuple(sample.signer_id for sample in samples)
    return (
        np.stack(rows, axis=0).astype(np.float32, copy=False),
        np.asarray(labels, dtype=np.int64),
        signers,
    )
