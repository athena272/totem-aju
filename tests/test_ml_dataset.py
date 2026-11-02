"""Testes do carregamento do dataset."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.ml_helpers import write_dataset_on_disk
from totem_aju.config import SEQUENCE_LENGTH
from totem_aju.errors import DatasetEmptyError, InvalidSampleShapeError
from totem_aju.ml.dataset import EXPECTED_SAMPLE_SHAPE, load_dataset
from totem_aju.vision.schema import FRAME_VECTOR_SIZE


class TestLoadDataset:
    def test_empty_manifest_raises(self, tmp_path: Path) -> None:
        (tmp_path / "manifest.jsonl").write_text("", encoding="utf-8")
        with pytest.raises(DatasetEmptyError):
            load_dataset(tmp_path)

    def test_missing_manifest_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetEmptyError):
            load_dataset(tmp_path)

    def test_loads_valid_samples(self, tmp_path: Path) -> None:
        write_dataset_on_disk(tmp_path)
        dataset = load_dataset(tmp_path)
        assert dataset.n_samples == 8
        assert dataset.signers == frozenset({"alice", "bruno"})
        assert dataset.samples[0].sequence.shape == EXPECTED_SAMPLE_SHAPE

    def test_invalid_shape_raises(self, tmp_path: Path) -> None:
        write_dataset_on_disk(tmp_path, signs=("ola",), signers=("alice",), reps=1)
        bad = tmp_path / "samples" / "ola" / "alice_0001.npy"
        np.save(
            bad, np.zeros((SEQUENCE_LENGTH, FRAME_VECTOR_SIZE - 1), dtype=np.float32)
        )
        with pytest.raises(InvalidSampleShapeError, match="shape"):
            load_dataset(tmp_path)
