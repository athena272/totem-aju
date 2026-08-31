"""Teste de fumaca da integracao com MediaPipe.

Fica fora de ``tests/`` de proposito: a suite de testes nao deve exigir
MediaPipe instalado, e este script exige. E executado pelo job de integracao
do CI e serve tambem para um integrante da equipe conferir rapidamente se o
ambiente completo ficou funcional::

    python scripts/smoke_mediapipe.py

Verifica o que testes com dubles nao conseguem verificar: que a biblioteca
nativa carrega, que a implementacao concreta satisfaz o contrato e que o
formato do vetor produzido e o esperado pelo classificador.
"""

from __future__ import annotations

import sys

import numpy as np

from totem_aju.vision.extractor import LandmarkExtractor
from totem_aju.vision.mediapipe_extractor import MediaPipeHolisticExtractor
from totem_aju.vision.normalization import normalize_frame
from totem_aju.vision.schema import FRAME_VECTOR_SIZE

FRAME_HEIGHT = 240
FRAME_WIDTH = 320


def main() -> int:
    import cv2
    import mediapipe

    print(f"mediapipe {mediapipe.__version__} | cv2 {cv2.__version__}")

    with MediaPipeHolisticExtractor() as extractor:
        if not isinstance(extractor, LandmarkExtractor):
            print("ERRO: a implementacao nao satisfaz LandmarkExtractor.")
            return 1

        blank = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        vector = normalize_frame(extractor.extract(blank)).to_vector()

    if vector.shape != (FRAME_VECTOR_SIZE,):
        print(f"ERRO: esperado ({FRAME_VECTOR_SIZE},), obtido {vector.shape}.")
        return 1
    if not np.isfinite(vector).all():
        print("ERRO: o vetor contem valores nao finitos.")
        return 1

    print(f"vetor do quadro: {vector.shape} | todos os valores finitos")
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
