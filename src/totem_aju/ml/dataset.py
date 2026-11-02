"""Carregamento do dataset de landmarks a partir do manifest.

Nao conhece sklearn nem modelos: so le disco, valida shape e devolve arrays.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from totem_aju.config import (
    DEFAULT_DATA_ROOT,
    MANIFEST_FILENAME,
    SEQUENCE_LENGTH,
)
from totem_aju.data.manifest import SampleManifest, SampleRecord
from totem_aju.errors import DatasetEmptyError, InvalidSampleShapeError
from totem_aju.vision.schema import FRAME_VECTOR_SIZE
from totem_aju.vocabulary import SIGN_TO_INDEX

EXPECTED_SAMPLE_SHAPE = (SEQUENCE_LENGTH, FRAME_VECTOR_SIZE)

SampleArray = NDArray[np.float32]


@dataclass(frozen=True, slots=True)
class LabeledSample:
    """Uma amostra pronta para extracao de features."""

    sequence: SampleArray
    sign: str
    label: int
    signer_id: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class LoadedDataset:
    """Dataset completo em memoria."""

    samples: tuple[LabeledSample, ...]
    data_root: Path

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    @property
    def signs(self) -> frozenset[str]:
        return frozenset(sample.sign for sample in self.samples)

    @property
    def signers(self) -> frozenset[str]:
        return frozenset(sample.signer_id for sample in self.samples)


def _load_sequence(data_root: Path, record: SampleRecord) -> SampleArray:
    path = data_root / record.relative_path
    array = np.load(path)
    if array.shape != EXPECTED_SAMPLE_SHAPE:
        raise InvalidSampleShapeError(
            path=str(path),
            actual=tuple(int(dim) for dim in array.shape),
            expected=EXPECTED_SAMPLE_SHAPE,
        )
    return array.astype(np.float32, copy=False)


def load_dataset(data_root: Path | None = None) -> LoadedDataset:
    """Le o manifest e todos os ``.npy`` referenciados.

    Raises:
        DatasetEmptyError: se nao houver amostras.
        InvalidSampleShapeError: se algum ``.npy`` tiver shape inesperado.
        FileNotFoundError: se o arquivo da amostra nao existir.
    """
    root = Path(data_root) if data_root is not None else DEFAULT_DATA_ROOT
    records = SampleManifest(root / MANIFEST_FILENAME).read_all()
    if not records:
        raise DatasetEmptyError(str(root))

    samples: list[LabeledSample] = []
    for record in records:
        sequence = _load_sequence(root, record)
        samples.append(
            LabeledSample(
                sequence=sequence,
                sign=record.sign,
                label=SIGN_TO_INDEX[record.sign],
                signer_id=record.signer_id,
                relative_path=record.relative_path,
            )
        )
    return LoadedDataset(samples=tuple(samples), data_root=root)
