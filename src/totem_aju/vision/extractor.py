"""Contrato de extracao de landmarks.

A existencia deste modulo e o que permite que todo o restante do pipeline seja
testado sem MediaPipe e sem webcam. Consumidores (``data.recorder``, futura
inferencia) dependem deste ``Protocol``, nunca de uma implementacao concreta.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from totem_aju.vision.schema import FrameLandmarks

#: Quadro de video em BGR, no formato entregue pelo OpenCV.
VideoFrame = NDArray[np.uint8]


@runtime_checkable
class LandmarkExtractor(Protocol):
    """Extrai landmarks de quadros de video."""

    def extract(self, frame: VideoFrame) -> FrameLandmarks:
        """Detecta maos e pose em um quadro.

        Implementacoes devem devolver :meth:`FrameLandmarks.empty` quando nada
        for detectado, em vez de lancar excecao: a ausencia de deteccao e
        esperada durante a coleta e faz parte do sinal.
        """
        ...

    def close(self) -> None:
        """Libera os recursos do detector."""
        ...
