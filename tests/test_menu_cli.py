"""Testes do CLI do menu por dedos, sem webcam nem MediaPipe."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tests.conftest import FakeFrameSource
from totem_aju.cli import menu as menu_cli
from totem_aju.errors import CameraUnavailableError
from totem_aju.menu.session import FrameUpdate
from totem_aju.menu.state import GestureStatePublisher, GestureStatus


def read_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "gesture_state.json"


class TestMirroredFrameSource:
    def test_applies_flip_and_releases_inner_source(self) -> None:
        inner = FakeFrameSource()
        source = menu_cli.MirroredFrameSource(inner, lambda f: f + 1)
        assert np.all(source.read() == 1)
        source.release()
        assert inner.released


def make_update(**overrides: Any) -> FrameUpdate:
    values: dict[str, Any] = {
        "status": GestureStatus.TRACKING,
        "fingers": 3,
        "progress": 0.5,
        "awaiting_release": False,
        "selected": None,
    }
    values.update(overrides)
    return FrameUpdate(**values)


class TestOverlay:
    def test_text_without_hand(self) -> None:
        text, _ = menu_cli._overlay_text(make_update(fingers=None, progress=0.0))
        assert "Mostre uma mao" in text

    def test_text_while_holding(self) -> None:
        text, _ = menu_cli._overlay_text(make_update())
        assert "Dedos: 3" in text

    def test_text_after_choice(self) -> None:
        text, _ = menu_cli._overlay_text(make_update(awaiting_release=True))
        assert "Abaixe a mao" in text

    def test_draws_on_frame_with_real_opencv(self) -> None:
        cv2 = pytest.importorskip("cv2")
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        menu_cli._draw_overlay(cv2, frame, make_update(progress=1.0))
        assert frame.any()


class TestMain:
    def test_rejects_non_positive_hold(self, state_path: Path) -> None:
        argv = ["--hold-seconds", "0", "--state-file", str(state_path)]
        assert menu_cli.main(argv) == 2
        assert not state_path.exists()

    def test_publishes_starting_before_opening_camera(
        self, state_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def fake_run(*, publisher: GestureStatePublisher, **_: Any) -> int:
            seen.append(read_state(publisher.path)["status"])
            return 2

        monkeypatch.setattr(menu_cli, "run_live_menu", fake_run)
        assert menu_cli.main(["--state-file", str(state_path)]) == 0
        assert seen == ["starting"]

    def test_camera_error_is_published_and_exits_1(
        self, state_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_run(**_: Any) -> int:
            raise CameraUnavailableError(3)

        monkeypatch.setattr(menu_cli, "run_live_menu", fake_run)
        assert menu_cli.main(["--state-file", str(state_path)]) == 1
        state = read_state(state_path)
        assert state["status"] == "error"
        assert "indice 3" in state["message"]

    def test_ctrl_c_publishes_stopped(
        self, state_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_run(**_: Any) -> int:
            raise KeyboardInterrupt

        monkeypatch.setattr(menu_cli, "run_live_menu", fake_run)
        assert menu_cli.main(["--state-file", str(state_path)]) == 130
        assert read_state(state_path)["status"] == "stopped"
