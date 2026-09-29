"""Heurísticas geométricas 3D para avaliação de dedos e gestos estáticos.

Integra-se com o pipeline de FrameLandmarks do Totem Aju sem alterar
a arquitetura existente.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from totem_aju.vocabulary import is_known_sign

LandmarkArray = NDArray[np.float32]


def calcular_angulo_3d(p1: LandmarkArray, p2: LandmarkArray, p3: LandmarkArray) -> float:
    """Calcula o ângulo em graus na articulação p2 formada por (p1 -> p2 -> p3)."""
    v1 = np.array(p1, dtype=float) - np.array(p2, dtype=float)
    v2 = np.array(p3, dtype=float) - np.array(p2, dtype=float)

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-6 or norm2 < 1e-6:
        return 0.0

    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return float(np.degrees(angle))


def distancia(p1: LandmarkArray, p2: LandmarkArray, usar_z: bool = False) -> float:
    """Distância euclidiana entre dois landmarks."""
    a = np.array(p1, dtype=float)
    b = np.array(p2, dtype=float)
    if not usar_z:
        a, b = a[:2], b[:2]
    return float(np.linalg.norm(a - b))


def pistas_do_dedo(
    lm_list: LandmarkArray, mcp: int, pip: int, tip: int, tamanho_mao: float
) -> tuple[list[int], float]:
    """Retorna pistas independentes sobre o estado do dedo (aberto=1 / fechado=0)."""
    p0 = lm_list[0]
    p_mcp = lm_list[mcp]
    p_pip = lm_list[pip]
    p_tip = lm_list[tip]

    pistas = []

    # Pista 1: Ângulo na dobra (3D)
    angulo = calcular_angulo_3d(p_mcp, p_pip, p_tip)
    pistas.append(1 if angulo > 140 else 0)

    # Pista 2: Continuidade de direção do dedo (3D)
    v1 = p_pip - p_mcp
    v2 = p_tip - p_pip
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 > 1e-6 and n2 > 1e-6:
        cos = np.dot(v1, v2) / (n1 * n2)
        desvio = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
        pistas.append(1 if desvio < 55 else 0)
    else:
        pistas.append(0)

    # Pista 3: Distância ponta -> pulso
    d_ponta = float(np.linalg.norm(p_tip - p0) / (tamanho_mao + 1e-6))
    pistas.append(1 if d_ponta > 1.55 else 0)

    return pistas, d_ponta


def pistas_do_polegar(
    lm_list: LandmarkArray, tamanho_mao: float
) -> tuple[int, float, float, float]:
    """Avalia o polegar através de flexão, distância e abdução."""
    p0 = lm_list[0]
    p9 = lm_list[9]
    p_mcp = lm_list[2]
    p_ip = lm_list[3]
    p_tip = lm_list[4]
    p_idx = lm_list[5]

    pistas = []

    ang_pol = calcular_angulo_3d(p_mcp, p_ip, p_tip)
    pistas.append(1 if ang_pol > 150 else 0)

    d_pol = float(np.linalg.norm(p_tip - p_idx) / (tamanho_mao + 1e-6))
    pistas.append(1 if d_pol > 0.50 else 0)

    eixo = p9 - p0
    vetor_ponta = p_tip - p0
    norma_eixo = np.linalg.norm(eixo) + 1e-6
    dist_perp = np.linalg.norm(np.cross(eixo, vetor_ponta)) / norma_eixo
    abd_pol = float(dist_perp / (tamanho_mao + 1e-6))
    pistas.append(1 if abd_pol > 0.35 else 0)

    aberto = 1 if sum(pistas) >= 2 else 0
    return aberto, ang_pol, d_pol, abd_pol


def avaliar_dedos(lm_list: LandmarkArray) -> tuple[list[int], list[str]]:
    """Classifica cada dedo por votação de pistas 3D."""
    tamanho_mao = distancia(lm_list[0], lm_list[9], usar_z=True)
    if tamanho_mao < 1e-6:
        tamanho_mao = 1e-6

    fingers = []
    debug = []

    pol_aberto, ang_pol, d_pol, abd_pol = pistas_do_polegar(lm_list, tamanho_mao)
    fingers.append(pol_aberto)
    debug.append(f"Pol: ang={ang_pol:.0f} d={d_pol:.2f} abd={abd_pol:.2f}")

    juntas = [(5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)]
    nomes = ["Ind", "Med", "Anl", "Min"]

    for (base, dobra, ponta), nome in zip(juntas, nomes):
        pistas, d_ponta = pistas_do_dedo(lm_list, base, dobra, ponta, tamanho_mao)
        aberto = 1 if sum(pistas) >= 2 else 0
        fingers.append(aberto)
        debug.append(f"{nome}: {'-'.join(map(str, pistas))} d={d_ponta:.2f}")

    return fingers, debug


GESTOS_MAP = {
    (0, 0, 0, 0, 0): "Punho Fechado",
    (1, 1, 1, 1, 1): "Mao Aberta",
    (0, 1, 0, 0, 0): "Apontando",
    (0, 1, 1, 0, 0): "Paz e Amor",
    (1, 0, 0, 0, 1): "Hang Loose",
    (0, 1, 0, 0, 1): "Rock",
    (0, 0, 0, 0, 1): "Mindinho",
    (1, 1, 0, 0, 0): "Pistola",
}


def reconhecer_gesto(fingers: list[int], lm_list: LandmarkArray) -> str:
    """Classifica o gesto a partir dos dedos e landmarks."""
    thumb, index, middle, ring, pinky = fingers
    padrao = tuple(fingers)

    tamanho_mao = distancia(lm_list[0], lm_list[9], usar_z=True)
    dist_normalizada = distancia(lm_list[4], lm_list[8], usar_z=True) / (tamanho_mao + 1e-6)

    if dist_normalizada < 0.38 and middle == 1 and ring == 1 and pinky == 1:
        return "OK"

    if padrao == (1, 0, 0, 0, 0):
        if lm_list[4][1] < lm_list[2][1] - 0.02:
            return "Joinha (cima)"
        elif lm_list[4][1] > lm_list[2][1] + 0.02:
            return "Joinha (baixo)"
        return "Polegar"

    if padrao in GESTOS_MAP:
        return GESTOS_MAP[padrao]

    return f"Numero: {sum(fingers)}"


# Mapeamento opcional para integração direta com o vocabulary.py oficial
GESTOS_PARA_VOCABULARIO: dict[str, str] = {
    "Mao Aberta": "ola",
    "Joinha (cima)": "sim",
    "Punho Fechado": "nao",
}


def reconhecer_sinal_vocabulario(nome_gesto: str) -> str | None:
    """Converte o gesto reconhecido para um sinal válido do vocabulário do Totem."""
    sinal = GESTOS_PARA_VOCABULARIO.get(nome_gesto)
    if sinal and is_known_sign(sinal):
        return sinal
    return None