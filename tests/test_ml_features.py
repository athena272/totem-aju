"""Testes da extracao de features."""

from __future__ import annotations

import pytest

from tests.ml_helpers import make_labeled_sample, make_sequence
from totem_aju.config import FEATURE_FLATTEN, FEATURE_MEAN, SEQUENCE_LENGTH
from totem_aju.ml.features import extract_features, feature_size, samples_to_matrix
from totem_aju.vision.schema import FRAME_VECTOR_SIZE


class TestExtractFeatures:
    def test_mean_shape(self) -> None:
        vector = extract_features(make_sequence(fill=0.5), FEATURE_MEAN)
        assert vector.shape == (FRAME_VECTOR_SIZE,)

    def test_flatten_shape(self) -> None:
        vector = extract_features(make_sequence(fill=0.5), FEATURE_FLATTEN)
        assert vector.shape == (SEQUENCE_LENGTH * FRAME_VECTOR_SIZE,)

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="desconhecido"):
            extract_features(make_sequence(fill=0.0), "pca")

    def test_feature_size_matches(self) -> None:
        assert feature_size(FEATURE_MEAN, SEQUENCE_LENGTH) == FRAME_VECTOR_SIZE
        assert (
            feature_size(FEATURE_FLATTEN, SEQUENCE_LENGTH)
            == SEQUENCE_LENGTH * FRAME_VECTOR_SIZE
        )


class TestSamplesToMatrix:
    def test_stacks_rows_and_labels(self) -> None:
        samples = (
            make_labeled_sample(sign="ola", signer_id="a", fill=0.0),
            make_labeled_sample(sign="sim", signer_id="b", fill=1.0),
        )
        x, y, signers = samples_to_matrix(samples, mode=FEATURE_MEAN)
        assert x.shape == (2, FRAME_VECTOR_SIZE)
        assert y.shape == (2,)
        assert signers == ("a", "b")
        assert y[0] != y[1]
