"""Constantes de configuracao do pipeline de visao e de coleta.

Centralizadas aqui para que coleta, treino e inferencia compartilhem
exatamente os mesmos valores. Divergencia entre esses numeros na coleta e na
inferencia e uma fonte silenciosa de queda de acuracia.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# --- Topologia dos landmarks do MediaPipe Holistic ---------------------------

#: Quantidade de landmarks por mao no modelo de maos do MediaPipe.
HAND_LANDMARK_COUNT: Final[int] = 21

#: Quantidade de landmarks do modelo de pose do MediaPipe.
POSE_LANDMARK_COUNT: Final[int] = 33

#: Coordenadas por landmark (x, y, z).
COORDS_PER_LANDMARK: Final[int] = 3

#: Indice do pulso na mao. Usado como origem na normalizacao por translacao.
WRIST_INDEX: Final[int] = 0

#: Indice da base do dedo medio. Junto com o pulso, define a escala da mao.
MIDDLE_FINGER_MCP_INDEX: Final[int] = 9

# --- Janela temporal --------------------------------------------------------

#: Numero de quadros de uma amostra apos reamostragem. Todo tensor entregue ao
#: classificador tem exatamente este comprimento no eixo temporal.
SEQUENCE_LENGTH: Final[int] = 32

#: Duracao alvo da captura de uma repeticao, em segundos.
CAPTURE_DURATION_SECONDS: Final[float] = 2.5

# --- Camera -----------------------------------------------------------------

DEFAULT_CAMERA_INDEX: Final[int] = 0
DEFAULT_CAMERA_FPS: Final[int] = 30

# --- Persistencia -----------------------------------------------------------

#: Raiz dos dados de coleta. Ignorada pelo git (ver .gitignore).
DEFAULT_DATA_ROOT: Final[Path] = Path("data")

#: Nome do arquivo de indice das amostras, em formato JSON Lines.
MANIFEST_FILENAME: Final[str] = "manifest.jsonl"

#: Subdiretorio onde ficam os arrays de landmarks.
SAMPLES_DIRNAME: Final[str] = "samples"

# --- Numero minimo de repeticoes recomendado por sinal e sinalizador --------

MIN_REPETITIONS_PER_SIGN: Final[int] = 20
