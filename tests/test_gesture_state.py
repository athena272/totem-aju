"""Testes da publicacao do estado da camera de gestos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from totem_aju.menu.state import GestureStatePublisher, GestureStatus


class FakeClock:
    """Relogio controlado pelo teste, em segundos."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def read_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "preview" / "gesture_state.json"


@pytest.fixture
def publisher(state_path: Path, clock: FakeClock) -> GestureStatePublisher:
    return GestureStatePublisher(
        state_path,
        min_interval_seconds=0.15,
        clock=clock,
        wall_clock_ms=lambda: 1_000,
        sleep=lambda _seconds: None,
    )


class TestFormat:
    def test_creates_directory_and_writes_state(
        self, publisher: GestureStatePublisher, state_path: Path
    ) -> None:
        assert publisher.publish(GestureStatus.TRACKING, fingers=3, progress=0.5)
        assert read_state(state_path) == {
            "status": "tracking",
            "updated_at_ms": 1_000,
            "fingers": 3,
            "progress": 0.5,
            "awaiting_release": False,
            "selection": None,
            "message": None,
        }

    def test_leaves_no_temporary_file(
        self, publisher: GestureStatePublisher, state_path: Path
    ) -> None:
        publisher.publish(GestureStatus.STARTING)
        assert [p.name for p in state_path.parent.iterdir()] == [state_path.name]

    def test_error_carries_message(
        self, publisher: GestureStatePublisher, state_path: Path
    ) -> None:
        publisher.publish(GestureStatus.ERROR, message="camera ocupada")
        state = read_state(state_path)
        assert state["status"] == "error"
        assert state["message"] == "camera ocupada"


class TestSelection:
    def test_selection_is_written_and_kept(
        self, publisher: GestureStatePublisher, state_path: Path, clock: FakeClock
    ) -> None:
        publisher.publish(GestureStatus.TRACKING, fingers=2, selected=2)
        first = read_state(state_path)["selection"]
        assert first["fingers"] == 2

        clock.now += 1.0
        publisher.publish(GestureStatus.NO_HAND)
        assert read_state(state_path)["selection"] == first

    def test_event_ids_increase(
        self, publisher: GestureStatePublisher, state_path: Path
    ) -> None:
        publisher.publish(GestureStatus.TRACKING, fingers=1, selected=1)
        first_id = read_state(state_path)["selection"]["event_id"]
        publisher.publish(GestureStatus.TRACKING, fingers=4, selected=4)
        second = read_state(state_path)["selection"]
        assert second["fingers"] == 4
        assert second["event_id"] > first_id

    def test_selection_bypasses_throttle(
        self, publisher: GestureStatePublisher
    ) -> None:
        publisher.publish(GestureStatus.TRACKING, fingers=3)
        assert publisher.publish(GestureStatus.TRACKING, fingers=3, selected=3)


class TestThrottle:
    def test_same_status_within_interval_is_skipped(
        self, publisher: GestureStatePublisher, clock: FakeClock
    ) -> None:
        assert publisher.publish(GestureStatus.TRACKING, fingers=1)
        clock.now += 0.05
        assert not publisher.publish(GestureStatus.TRACKING, fingers=1)
        clock.now += 0.15
        assert publisher.publish(GestureStatus.TRACKING, fingers=1)

    def test_status_change_is_written_immediately(
        self, publisher: GestureStatePublisher, state_path: Path
    ) -> None:
        publisher.publish(GestureStatus.TRACKING, fingers=1)
        assert publisher.publish(GestureStatus.STOPPED)
        assert read_state(state_path)["status"] == "stopped"


class TestWriteFailure:
    def test_retries_while_file_is_briefly_locked(
        self,
        publisher: GestureStatePublisher,
        state_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regressao: no Windows, o servidor lendo o arquivo nega o replace."""
        original_replace = Path.replace
        failures = iter([True, True])

        def flaky(self: Path, target: Path) -> Path:
            if next(failures, False):
                raise PermissionError("[WinError 5] Acesso negado")
            return original_replace(self, target)

        monkeypatch.setattr(Path, "replace", flaky)
        assert publisher.publish(GestureStatus.STOPPED)
        assert read_state(state_path)["status"] == "stopped"

    def test_os_error_returns_false_without_raising(
        self,
        publisher: GestureStatePublisher,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def locked(self: Path, target: Path) -> Path:  # noqa: ARG001
            raise PermissionError("arquivo em uso")

        monkeypatch.setattr(Path, "replace", locked)
        assert not publisher.publish(GestureStatus.TRACKING, fingers=2, selected=2)

    def test_selection_survives_failed_write(
        self,
        publisher: GestureStatePublisher,
        state_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        original_replace = Path.replace

        def locked(self: Path, target: Path) -> Path:  # noqa: ARG001
            raise PermissionError("arquivo em uso")

        monkeypatch.setattr(Path, "replace", locked)
        publisher.publish(GestureStatus.TRACKING, fingers=2, selected=2)

        monkeypatch.setattr(Path, "replace", original_replace)
        assert publisher.publish(GestureStatus.TRACKING, fingers=2)
        assert read_state(state_path)["selection"]["fingers"] == 2
