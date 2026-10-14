"""Testes de integracao do loop do menu por dedos, sem webcam."""

from __future__ import annotations

import itertools
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import FakeExtractor, FakeFrameSource
from totem_aju.errors import CameraUnavailableError
from totem_aju.menu.selector import FingerHoldSelector
from totem_aju.menu.session import FrameUpdate, run_menu_session
from totem_aju.menu.state import GestureStatePublisher
from totem_aju.vision.extractor import VideoFrame
from totem_aju.vision.schema import FrameLandmarks


class ScriptedCounter:
    """``FingerCounter`` que devolve uma sequencia pre-definida de contagens."""

    def __init__(self, counts: Iterable[int | None]) -> None:
        self._counts = iter(counts)

    def count(self, landmarks: FrameLandmarks) -> int | None:  # noqa: ARG002
        return next(self._counts, None)


def read_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "gesture_state.json"


def two_frame_selector() -> FingerHoldSelector:
    """Seletor que confirma no segundo quadro igual (relogio avanca 1 s/quadro)."""
    return FingerHoldSelector(hold_seconds=0.5, clock=itertools.count().__next__)


def run(
    counts: list[int | None],
    state_path: Path,
    *,
    source: FakeFrameSource | None = None,
    on_frame: Any = None,
) -> int:
    return run_menu_session(
        source=source or FakeFrameSource(),
        extractor=FakeExtractor(),
        counter=ScriptedCounter(counts),
        selector=two_frame_selector(),
        publisher=GestureStatePublisher(state_path, min_interval_seconds=0.0),
        max_frames=len(counts),
        on_frame=on_frame,
    )


class TestSession:
    def test_held_count_becomes_selection_in_state_file(self, state_path: Path) -> None:
        assert run([3, 3, 3], state_path) == 1
        state = read_state(state_path)
        assert state["selection"]["fingers"] == 3

    def test_ends_with_stopped_status(self, state_path: Path) -> None:
        run([1], state_path)
        assert read_state(state_path)["status"] == "stopped"

    def test_respects_max_frames(self, state_path: Path) -> None:
        source = FakeFrameSource()
        run([None] * 4, state_path, source=source)
        assert source.read_calls == 4

    def test_counts_multiple_selections(self, state_path: Path) -> None:
        assert run([2, 2, None, 4, 4], state_path) == 2
        assert read_state(state_path)["selection"]["fingers"] == 4

    def test_on_frame_receives_updates_and_can_stop(self, state_path: Path) -> None:
        received: list[FrameUpdate] = []

        def on_frame(frame: VideoFrame, update: FrameUpdate) -> bool:  # noqa: ARG001
            received.append(update)
            return len(received) < 2

        run([1, 1, 1, 1], state_path, on_frame=on_frame)
        assert len(received) == 2
        assert received[0].status == "tracking"
        assert received[0].progress == 0.0
        assert received[1].selected == 1

    def test_frame_without_hand_reports_no_hand(self, state_path: Path) -> None:
        received: list[FrameUpdate] = []

        def on_frame(frame: VideoFrame, update: FrameUpdate) -> bool:  # noqa: ARG001
            received.append(update)
            return True

        run([None], state_path, on_frame=on_frame)
        assert received[0].status == "no_hand"
        assert received[0].fingers is None

    def test_camera_failure_publishes_error_and_reraises(
        self, state_path: Path
    ) -> None:
        with pytest.raises(CameraUnavailableError):
            run([1, 1, 1], state_path, source=FakeFrameSource(max_reads=1))
        state = read_state(state_path)
        assert state["status"] == "error"
        assert "camera" in state["message"]

    def test_rejects_non_positive_max_frames(self, state_path: Path) -> None:
        with pytest.raises(ValueError, match="max_frames"):
            run_menu_session(
                source=FakeFrameSource(),
                extractor=FakeExtractor(),
                counter=ScriptedCounter([]),
                selector=two_frame_selector(),
                publisher=GestureStatePublisher(state_path),
                max_frames=0,
            )
