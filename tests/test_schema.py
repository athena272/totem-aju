"""Testes das estruturas de dados dos landmarks."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from tests.conftest import make_frame, make_hand
from totem_aju.vision.schema import (
    FRAME_VECTOR_SIZE,
    FrameLandmarks,
    empty_hand,
    empty_pose,
)


class TestFrameLandmarksValidation:
    def test_accepts_correct_shapes(self) -> None:
        assert make_frame() is not None

    @pytest.mark.parametrize("field", ["left_hand", "right_hand"])
    def test_rejects_wrong_hand_shape(self, field: str) -> None:
        kwargs = {
            "left_hand": make_hand(),
            "right_hand": make_hand(1),
            "pose": empty_pose(),
            "left_hand_detected": True,
            "right_hand_detected": True,
        }
        kwargs[field] = np.zeros((5, 3), dtype=np.float32)
        with pytest.raises(ValueError, match=field):
            FrameLandmarks(**kwargs)  # type: ignore[arg-type]

    def test_rejects_wrong_pose_shape(self) -> None:
        with pytest.raises(ValueError, match="pose"):
            FrameLandmarks(
                left_hand=empty_hand(),
                right_hand=empty_hand(),
                pose=np.zeros((10, 3), dtype=np.float32),
                left_hand_detected=False,
                right_hand_detected=False,
            )


class TestFrameLandmarksImmutability:
    def test_is_frozen(self) -> None:
        frame = make_frame()
        with pytest.raises(dataclasses.FrozenInstanceError):
            frame.left_hand = empty_hand()  # type: ignore[misc]


class TestEmptyFrame:
    def test_all_arrays_are_zeros(self) -> None:
        frame = FrameLandmarks.empty()
        assert not frame.left_hand.any()
        assert not frame.right_hand.any()
        assert not frame.pose.any()

    def test_detection_flags_are_false(self) -> None:
        frame = FrameLandmarks.empty()
        assert frame.left_hand_detected is False
        assert frame.right_hand_detected is False
        assert frame.has_any_hand is False


class TestHasAnyHand:
    @pytest.mark.parametrize(
        ("left", "right", "expected"),
        [
            (True, True, True),
            (True, False, True),
            (False, True, True),
            (False, False, False),
        ],
    )
    def test_combinations(self, left: bool, right: bool, expected: bool) -> None:
        frame = FrameLandmarks(
            left_hand=empty_hand(),
            right_hand=empty_hand(),
            pose=empty_pose(),
            left_hand_detected=left,
            right_hand_detected=right,
        )
        assert frame.has_any_hand is expected


class TestToVector:
    def test_has_expected_size(self) -> None:
        assert make_frame().to_vector().shape == (FRAME_VECTOR_SIZE,)

    def test_is_float32(self) -> None:
        assert make_frame().to_vector().dtype == np.float32

    def test_is_one_dimensional(self) -> None:
        assert make_frame().to_vector().ndim == 1

    def test_concatenation_order_is_stable(self) -> None:
        """A ordem e contrato com o classificador e nao pode mudar."""
        frame = make_frame()
        vector = frame.to_vector()
        assert np.allclose(vector[: frame.left_hand.size], frame.left_hand.ravel())
