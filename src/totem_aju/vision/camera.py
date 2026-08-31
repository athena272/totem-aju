"""Fonte de quadros de video.

Mesma estrategia adotada para o MediaPipe: um ``Protocol`` na frente, e o
``import cv2`` feito preguicosamente na implementacao concreta. Assim o
``data.recorder`` pode ser exercitado com uma fonte sintetica, sem webcam.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, runtime_checkable

from totem_aju.config import DEFAULT_CAMERA_INDEX
from totem_aju.errors import CameraUnavailableError
from totem_aju.vision.extractor import VideoFrame


@runtime_checkable
class FrameSource(Protocol):
    """Fornece quadros de video sob demanda."""

    def read(self) -> VideoFrame:
        """Devolve o proximo quadro.

        Raises:
            CameraUnavailableError: se a fonte deixar de entregar quadros.
        """
        ...

    def release(self) -> None:
        """Libera a fonte."""
        ...


class OpenCVCamera:
    """Webcam acessada via OpenCV.

    Suporta uso como gerenciador de contexto para garantir a liberacao do
    dispositivo, que no Windows permanece travado se nao for liberado.
    """

    def __init__(self, index: int = DEFAULT_CAMERA_INDEX) -> None:
        """
        Raises:
            CameraUnavailableError: se a camera nao puder ser aberta.
        """
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - ambiente incompleto
            raise CameraUnavailableError(index) from exc

        self._index = index
        self._capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            self._capture.release()
            raise CameraUnavailableError(index)

    def read(self) -> VideoFrame:
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise CameraUnavailableError(self._index)
        return frame

    def release(self) -> None:
        """Libera o dispositivo. Idempotente."""
        if self._capture is not None:
            self._capture.release()

    def __enter__(self) -> OpenCVCamera:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
