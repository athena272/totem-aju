"""Testes da contagem de dedos sobre as heuristicas geometricas."""

from __future__ import annotations

from totem_aju.menu.counter import HeuristicFingerCounter
from totem_aju.vision.schema import (
    FrameLandmarks,
    LandmarkArray,
    empty_hand,
    empty_pose,
)

#: Base (MCP) de indicador, medio, anelar e minimo: indices e posicao x.
_FINGER_BASES = ((5, 0.42), (9, 0.50), (13, 0.58), (17, 0.66))


def _hand(*, open_fingers: bool) -> LandmarkArray:
    """Mao sintetica em coordenadas de imagem (y cresce para baixo).

    Aberta: dedos retos para cima e polegar esticado para o lado.
    Fechada: pontas dobradas de volta para a palma e polegar sobre ela.
    """
    hand = empty_hand()
    hand[0] = (0.50, 0.90, 0.0)  # pulso

    if open_fingers:
        hand[1:5] = [(0.40, 0.85, 0), (0.32, 0.80, 0), (0.26, 0.76, 0), (0.20, 0.72, 0)]
        finger_ys = (0.70, 0.60, 0.52, 0.45)
    else:
        hand[1:5] = [(0.42, 0.85, 0), (0.40, 0.80, 0), (0.42, 0.75, 0), (0.48, 0.76, 0)]
        finger_ys = (0.70, 0.62, 0.66, 0.72)

    for base, x in _FINGER_BASES:
        for offset, y in enumerate(finger_ys):
            hand[base + offset] = (x, y, 0.0)
    return hand


def _frame(
    *, right: LandmarkArray | None = None, left: LandmarkArray | None = None
) -> FrameLandmarks:
    return FrameLandmarks(
        left_hand=left if left is not None else empty_hand(),
        right_hand=right if right is not None else empty_hand(),
        pose=empty_pose(),
        left_hand_detected=left is not None,
        right_hand_detected=right is not None,
    )


class TestHeuristicFingerCounter:
    def test_no_hand_returns_none(self) -> None:
        assert HeuristicFingerCounter().count(FrameLandmarks.empty()) is None

    def test_open_hand_counts_five(self) -> None:
        assert (
            HeuristicFingerCounter().count(_frame(right=_hand(open_fingers=True))) == 5
        )

    def test_closed_hand_counts_zero(self) -> None:
        frame = _frame(right=_hand(open_fingers=False))
        assert HeuristicFingerCounter().count(frame) == 0

    def test_uses_left_hand_when_only_it_is_visible(self) -> None:
        frame = _frame(left=_hand(open_fingers=True))
        assert HeuristicFingerCounter().count(frame) == 5

    def test_prefers_right_hand_when_both_are_visible(self) -> None:
        frame = _frame(right=_hand(open_fingers=False), left=_hand(open_fingers=True))
        assert HeuristicFingerCounter().count(frame) == 0
