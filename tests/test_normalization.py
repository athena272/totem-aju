"""Testes da normalizacao geometrica.

O valor destes testes esta em verificar as duas *propriedades* que justificam a
existencia do modulo -- invariancia a translacao e a escala -- e nao valores
numericos especificos.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import make_frame, make_hand
from totem_aju.config import WRIST_INDEX
from totem_aju.vision.normalization import (
    center_on_wrist,
    hand_scale,
    normalize_frame,
    normalize_hand,
    scale_to_unit,
)
from totem_aju.vision.schema import FrameLandmarks, empty_hand, empty_pose


class TestCenterOnWrist:
    def test_wrist_becomes_origin(self) -> None:
        centered = center_on_wrist(make_hand())
        assert np.allclose(centered[WRIST_INDEX], 0.0)

    def test_preserves_shape_and_dtype(self) -> None:
        hand = make_hand()
        centered = center_on_wrist(hand)
        assert centered.shape == hand.shape
        assert centered.dtype == np.float32

    def test_does_not_mutate_input(self) -> None:
        hand = make_hand()
        original = hand.copy()
        center_on_wrist(hand)
        assert np.array_equal(hand, original)


class TestHandScale:
    def test_positive_for_valid_hand(self) -> None:
        assert hand_scale(make_hand()) > 0.0

    def test_zero_for_absent_hand(self) -> None:
        assert hand_scale(empty_hand()) == pytest.approx(0.0)


class TestScaleToUnit:
    def test_reference_distance_becomes_one(self) -> None:
        scaled = scale_to_unit(center_on_wrist(make_hand()))
        assert hand_scale(scaled) == pytest.approx(1.0, abs=1e-5)

    def test_absent_hand_is_returned_unchanged(self) -> None:
        """Escala degenerada nao pode causar divisao por zero."""
        absent = empty_hand()
        scaled = scale_to_unit(absent)
        assert np.array_equal(scaled, absent)
        assert np.isfinite(scaled).all()


class TestNormalizeHandInvariance:
    """As propriedades que dao sentido ao modulo."""

    def test_invariant_to_translation(self) -> None:
        hand = make_hand()
        shifted = hand + np.array([0.3, -0.2, 0.05], dtype=np.float32)
        assert np.allclose(normalize_hand(hand), normalize_hand(shifted), atol=1e-5)

    def test_invariant_to_scale(self) -> None:
        """A mesma mao mais perto ou mais longe da camera gera o mesmo vetor."""
        hand = make_hand()
        farther = hand * np.float32(0.4)
        closer = hand * np.float32(2.5)
        assert np.allclose(normalize_hand(hand), normalize_hand(farther), atol=1e-5)
        assert np.allclose(normalize_hand(hand), normalize_hand(closer), atol=1e-5)

    def test_invariant_to_translation_and_scale_combined(self) -> None:
        hand = make_hand()
        transformed = hand * np.float32(1.7) + np.array(
            [-0.4, 0.6, 0.1], dtype=np.float32
        )
        assert np.allclose(normalize_hand(hand), normalize_hand(transformed), atol=1e-5)

    def test_distinguishes_different_hands(self) -> None:
        """Invariancia nao pode degenerar em apagar o sinal."""
        assert not np.allclose(
            normalize_hand(make_hand(1)), normalize_hand(make_hand(2))
        )


class TestNormalizeFrame:
    def test_normalizes_both_hands(self) -> None:
        normalized = normalize_frame(make_frame())
        assert np.allclose(normalized.left_hand[WRIST_INDEX], 0.0)
        assert np.allclose(normalized.right_hand[WRIST_INDEX], 0.0)

    def test_pose_is_preserved(self) -> None:
        """A pose carrega a posicao do sinal em relacao ao corpo."""
        pose = np.full_like(empty_pose(), 0.42)
        frame = FrameLandmarks(
            left_hand=make_hand(),
            right_hand=make_hand(5),
            pose=pose,
            left_hand_detected=True,
            right_hand_detected=True,
        )
        assert np.array_equal(normalize_frame(frame).pose, pose)

    def test_detection_flags_are_preserved(self) -> None:
        frame = FrameLandmarks(
            left_hand=make_hand(),
            right_hand=empty_hand(),
            pose=empty_pose(),
            left_hand_detected=True,
            right_hand_detected=False,
        )
        normalized = normalize_frame(frame)
        assert normalized.left_hand_detected is True
        assert normalized.right_hand_detected is False

    def test_absent_frame_produces_finite_values(self) -> None:
        normalized = normalize_frame(FrameLandmarks.empty())
        assert np.isfinite(normalized.to_vector()).all()
