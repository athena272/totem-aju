"""Normalizacao geometrica dos landmarks.

Funcoes puras, sem estado e sem efeito colateral: a mesma entrada sempre produz
a mesma saida, o que as torna diretamente verificaveis por testes.

Motivacao: o MediaPipe devolve coordenadas relativas ao quadro da imagem, de
modo que o *mesmo* sinal gera vetores muito diferentes se a pessoa estiver mais
a esquerda ou mais distante da camera. Sem normalizar, o modelo gastaria dados
aprendendo a ignorar posicao e distancia. Ver ``docs/arquitetura.md``.
"""

from __future__ import annotations

import numpy as np

from totem_aju.config import MIDDLE_FINGER_MCP_INDEX, WRIST_INDEX
from totem_aju.vision.schema import FrameLandmarks, LandmarkArray

#: Abaixo deste valor a escala e considerada degenerada (mao ausente ou
#: landmarks colapsados) e a normalizacao por escala e omitida.
_MIN_SCALE = 1e-6


def center_on_wrist(hand: LandmarkArray) -> LandmarkArray:
    """Translada a mao para que o pulso seja a origem.

    Torna a representacao invariante a posicao da mao no quadro.
    """
    return (hand - hand[WRIST_INDEX]).astype(np.float32, copy=False)


def hand_scale(hand: LandmarkArray) -> float:
    """Escala caracteristica da mao: distancia pulso -> base do dedo medio.

    Devolve ``0.0`` quando os landmarks estao colapsados, o que ocorre quando a
    mao nao foi detectada e o array e composto de zeros.
    """
    reference = hand[MIDDLE_FINGER_MCP_INDEX] - hand[WRIST_INDEX]
    return float(np.linalg.norm(reference))


def scale_to_unit(hand: LandmarkArray) -> LandmarkArray:
    """Divide a mao pela sua escala caracteristica.

    Torna a representacao invariante ao tamanho aparente da mao, isto e, a
    distancia da pessoa em relacao a camera. Quando a escala e degenerada, o
    array e devolvido inalterado, evitando divisao por zero.
    """
    scale = hand_scale(hand)
    if scale < _MIN_SCALE:
        return hand.astype(np.float32, copy=True)
    return (hand / scale).astype(np.float32, copy=False)


def normalize_hand(hand: LandmarkArray) -> LandmarkArray:
    """Aplica translacao e escala, nesta ordem.

    A ordem importa: centralizar antes de escalar mantem o pulso na origem,
    enquanto o inverso deslocaria a mao proporcionalmente a escala.
    """
    return scale_to_unit(center_on_wrist(hand))


def normalize_frame(frame: FrameLandmarks) -> FrameLandmarks:
    """Normaliza as duas maos de um quadro.

    A pose e preservada como esta: ela carrega a informacao de *onde*, em
    relacao ao corpo, o sinal e executado -- e Libras usa essa posicao como
    elemento distintivo. Normalizar a pose apagaria justamente essa informacao.
    """
    return FrameLandmarks(
        left_hand=normalize_hand(frame.left_hand),
        right_hand=normalize_hand(frame.right_hand),
        pose=frame.pose,
        left_hand_detected=frame.left_hand_detected,
        right_hand_detected=frame.right_hand_detected,
    )
