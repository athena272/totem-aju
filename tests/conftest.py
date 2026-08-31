"""Fixtures e dublês compartilhados pelos testes.

Nenhum teste desta suite exige MediaPipe, OpenCV ou webcam: os dublês abaixo
implementam os ``Protocol`` do pacote, o que e exatamente o beneficio pratico
da inversao de dependencia adotada na arquitetura.
"""

from __future__ import annotations

import numpy as np
import pytest

from totem_aju.config import (
    COORDS_PER_LANDMARK,
    HAND_LANDMARK_COUNT,
    MIDDLE_FINGER_MCP_INDEX,
    WRIST_INDEX,
)
from totem_aju.errors import CameraUnavailableError
from totem_aju.vision.extractor import VideoFrame
from totem_aju.vision.schema import FrameLandmarks, LandmarkArray, empty_pose


def make_hand(seed: int = 0) -> LandmarkArray:
    """Mao sintetica deterministica, com escala nao degenerada.

    Garante que o pulso e a base do dedo medio nao coincidam, para que
    ``hand_scale`` seja positiva.
    """
    rng = np.random.default_rng(seed)
    hand = rng.uniform(
        0.1, 0.9, size=(HAND_LANDMARK_COUNT, COORDS_PER_LANDMARK)
    ).astype(np.float32)
    hand[WRIST_INDEX] = np.array([0.5, 0.8, 0.0], dtype=np.float32)
    hand[MIDDLE_FINGER_MCP_INDEX] = np.array([0.5, 0.6, 0.0], dtype=np.float32)
    return hand


def make_frame(seed: int = 0, *, detected: bool = True) -> FrameLandmarks:
    """Quadro sintetico com ambas as maos detectadas."""
    if not detected:
        return FrameLandmarks.empty()
    return FrameLandmarks(
        left_hand=make_hand(seed),
        right_hand=make_hand(seed + 100),
        pose=empty_pose(),
        left_hand_detected=True,
        right_hand_detected=True,
    )


class FakeExtractor:
    """``LandmarkExtractor`` que devolve quadros sinteticos deterministicos."""

    def __init__(self, *, detected: bool = True) -> None:
        self._detected = detected
        self.extract_calls = 0
        self.closed = False

    def extract(self, frame: VideoFrame) -> FrameLandmarks:  # noqa: ARG002
        result = make_frame(self.extract_calls, detected=self._detected)
        self.extract_calls += 1
        return result

    def close(self) -> None:
        self.closed = True


class FakeFrameSource:
    """``FrameSource`` que entrega quadros preenchidos com zeros.

    Se ``max_reads`` for atingido, lanca ``CameraUnavailableError``, permitindo
    testar o comportamento do recorder diante de uma camera que falha.
    """

    def __init__(self, *, max_reads: int | None = None) -> None:
        self._max_reads = max_reads
        self.read_calls = 0
        self.released = False

    def read(self) -> VideoFrame:
        if self._max_reads is not None and self.read_calls >= self._max_reads:
            raise CameraUnavailableError(0)
        self.read_calls += 1
        return np.zeros((48, 64, 3), dtype=np.uint8)

    def release(self) -> None:
        self.released = True


@pytest.fixture
def fake_extractor() -> FakeExtractor:
    return FakeExtractor()


@pytest.fixture
def fake_source() -> FakeFrameSource:
    return FakeFrameSource()
