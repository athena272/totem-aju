"""Testes da reamostragem temporal e do buffer de sequencia."""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import make_frame
from totem_aju.errors import EmptySequenceError
from totem_aju.vision.schema import FRAME_VECTOR_SIZE, FrameLandmarks
from totem_aju.vision.sequence import SequenceBuffer, resample_sequence


def ramp(n_frames: int, n_features: int = 3) -> np.ndarray:
    """Sequencia crescente, cujo comportamento sob interpolacao e previsivel."""
    column = np.linspace(0.0, 1.0, num=n_frames, dtype=np.float32)
    return np.tile(column[:, None], (1, n_features))


class TestResampleSequence:
    @pytest.mark.parametrize("n_frames", [1, 2, 5, 32, 75, 200])
    def test_output_length_is_canonical(self, n_frames: int) -> None:
        assert resample_sequence(ramp(n_frames), length=32).shape == (32, 3)

    def test_preserves_first_and_last_frame(self) -> None:
        """Inicio e fim marcam os limites do movimento do sinal."""
        sequence = ramp(9)
        resampled = resample_sequence(sequence, length=32)
        assert np.allclose(resampled[0], sequence[0])
        assert np.allclose(resampled[-1], sequence[-1])

    def test_upsampling_stays_monotonic(self) -> None:
        resampled = resample_sequence(ramp(5), length=40)[:, 0]
        assert np.all(np.diff(resampled) >= -1e-6)

    def test_identity_when_length_matches(self) -> None:
        sequence = ramp(32)
        assert np.allclose(resample_sequence(sequence, length=32), sequence)

    def test_single_frame_is_replicated(self) -> None:
        sequence = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        resampled = resample_sequence(sequence, length=8)
        assert resampled.shape == (8, 3)
        assert np.allclose(resampled, sequence[0])

    def test_output_dtype_is_float32(self) -> None:
        assert resample_sequence(ramp(10), length=16).dtype == np.float32

    def test_empty_sequence_raises(self) -> None:
        with pytest.raises(EmptySequenceError):
            resample_sequence(np.empty((0, 3), dtype=np.float32))

    def test_non_positive_length_raises(self) -> None:
        with pytest.raises(ValueError, match="positivo"):
            resample_sequence(ramp(4), length=0)

    def test_wrong_dimensionality_raises(self) -> None:
        with pytest.raises(ValueError, match="2-D"):
            resample_sequence(np.zeros((4, 3, 2), dtype=np.float32))


class TestSequenceBuffer:
    def test_starts_empty(self) -> None:
        buffer = SequenceBuffer(max_frames=10)
        assert buffer.is_empty
        assert len(buffer) == 0

    def test_append_increases_length(self) -> None:
        buffer = SequenceBuffer(max_frames=10)
        buffer.append(make_frame())
        assert len(buffer) == 1
        assert not buffer.is_empty

    def test_window_discards_oldest_frames(self) -> None:
        buffer = SequenceBuffer(max_frames=3)
        for seed in range(10):
            buffer.append(make_frame(seed))
        assert len(buffer) == 3

    def test_clear_empties_the_buffer(self) -> None:
        buffer = SequenceBuffer(max_frames=5)
        buffer.append(make_frame())
        buffer.clear()
        assert buffer.is_empty

    def test_to_array_has_canonical_shape(self) -> None:
        buffer = SequenceBuffer(max_frames=50, sequence_length=32)
        for seed in range(50):
            buffer.append(make_frame(seed))
        assert buffer.to_array().shape == (32, FRAME_VECTOR_SIZE)

    def test_to_array_on_empty_buffer_raises(self) -> None:
        with pytest.raises(EmptySequenceError):
            SequenceBuffer(max_frames=5).to_array()

    def test_max_frames_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="max_frames"):
            SequenceBuffer(max_frames=0)

    def test_sequence_length_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="sequence_length"):
            SequenceBuffer(max_frames=5, sequence_length=-1)


class TestDetectionRatio:
    def test_zero_when_empty(self) -> None:
        assert SequenceBuffer(max_frames=5).detection_ratio == 0.0

    def test_one_when_all_detected(self) -> None:
        buffer = SequenceBuffer(max_frames=4)
        for seed in range(4):
            buffer.append(make_frame(seed))
        assert buffer.detection_ratio == pytest.approx(1.0)

    def test_zero_when_none_detected(self) -> None:
        buffer = SequenceBuffer(max_frames=4)
        for _ in range(4):
            buffer.append(FrameLandmarks.empty())
        assert buffer.detection_ratio == pytest.approx(0.0)

    def test_half_when_half_detected(self) -> None:
        buffer = SequenceBuffer(max_frames=4)
        buffer.append(make_frame(0))
        buffer.append(FrameLandmarks.empty())
        buffer.append(make_frame(1))
        buffer.append(FrameLandmarks.empty())
        assert buffer.detection_ratio == pytest.approx(0.5)
