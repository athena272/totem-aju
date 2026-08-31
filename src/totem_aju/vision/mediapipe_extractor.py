"""Implementacao de :class:`LandmarkExtractor` baseada no MediaPipe Holistic.

Este e o unico modulo do projeto que conhece o MediaPipe. O import e feito
**dentro do construtor**, nao no topo do arquivo, para que importar qualquer
outro modulo do pacote -- inclusive em uma maquina sem MediaPipe ou em um
Python 3.13+ -- continue funcionando.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import numpy as np

from totem_aju.config import COORDS_PER_LANDMARK, HAND_LANDMARK_COUNT
from totem_aju.errors import MediaPipeNotInstalledError
from totem_aju.vision.extractor import VideoFrame
from totem_aju.vision.schema import (
    FrameLandmarks,
    LandmarkArray,
    empty_hand,
    empty_pose,
)


def _to_array(landmark_list: Any | None, count: int) -> tuple[LandmarkArray, bool]:
    """Converte um ``LandmarkList`` do MediaPipe em array e flag de deteccao.

    Devolve zeros quando a lista e ausente, mantendo o formato do quadro
    constante independentemente da deteccao.
    """
    if landmark_list is None:
        return np.zeros((count, COORDS_PER_LANDMARK), dtype=np.float32), False
    points = np.array(
        [(lm.x, lm.y, lm.z) for lm in landmark_list.landmark],
        dtype=np.float32,
    )
    if points.shape != (count, COORDS_PER_LANDMARK):
        return np.zeros((count, COORDS_PER_LANDMARK), dtype=np.float32), False
    return points, True


class MediaPipeHolisticExtractor:
    """Extrai maos e pose usando o modelo Holistic do MediaPipe.

    Satisfaz o ``Protocol`` :class:`~totem_aju.vision.extractor.LandmarkExtractor`
    estruturalmente, sem heranca.

    Suporta uso como gerenciador de contexto, garantindo a liberacao dos
    recursos nativos mesmo em caso de excecao::

        with MediaPipeHolisticExtractor() as extractor:
            landmarks = extractor.extract(frame)
    """

    def __init__(
        self,
        *,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1,
    ) -> None:
        """
        Raises:
            MediaPipeNotInstalledError: se o MediaPipe nao estiver disponivel.
        """
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise MediaPipeNotInstalledError() from exc

        self._holistic = mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._closed = False

    def extract(self, frame: VideoFrame) -> FrameLandmarks:
        """Detecta maos e pose em um quadro BGR do OpenCV."""
        if self._closed:
            raise RuntimeError("O extractor ja foi fechado.")

        # O MediaPipe espera RGB; o OpenCV entrega BGR.
        rgb_frame = frame[:, :, ::-1]
        results = self._holistic.process(rgb_frame)

        left_hand, left_detected = _to_array(
            getattr(results, "left_hand_landmarks", None), HAND_LANDMARK_COUNT
        )
        right_hand, right_detected = _to_array(
            getattr(results, "right_hand_landmarks", None), HAND_LANDMARK_COUNT
        )
        pose_landmarks = getattr(results, "pose_landmarks", None)
        pose = (
            empty_pose()
            if pose_landmarks is None
            else np.array(
                [(lm.x, lm.y, lm.z) for lm in pose_landmarks.landmark],
                dtype=np.float32,
            )
        )
        if pose.shape != empty_pose().shape:
            pose = empty_pose()

        return FrameLandmarks(
            left_hand=left_hand if left_detected else empty_hand(),
            right_hand=right_hand if right_detected else empty_hand(),
            pose=pose,
            left_hand_detected=left_detected,
            right_hand_detected=right_detected,
        )

    def close(self) -> None:
        """Libera os recursos nativos. Idempotente."""
        if not self._closed:
            self._holistic.close()
            self._closed = True

    def __enter__(self) -> MediaPipeHolisticExtractor:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
