"""Vocabulario fechado de sinais reconhecidos pelo totem.

Fonte da verdade para validacao de rotulos. A documentacao correspondente,
com a glosa e o uso de cada sinal, esta em ``docs/vocabulario-sinais.md``.

Os identificadores sao estaveis: acrescentar sinais e seguro, mas renomear ou
remover quebra a correspondencia com as amostras ja gravadas, cujo rotulo esta
persistido no manifest.
"""

from __future__ import annotations

from enum import StrEnum

from totem_aju.errors import UnknownSignError


class SignCategory(StrEnum):
    """Agrupamento usado pela interface para guiar o usuario."""

    INTERACTION = "interacao"
    QUESTION = "pergunta"
    SERVICE = "servico"
    TRANSPORT = "transporte"
    LANDMARK = "ponto_turistico"


#: Vocabulario canonico: identificador do sinal -> categoria.
VOCABULARY: dict[str, SignCategory] = {
    # Controle da interacao
    "ola": SignCategory.INTERACTION,
    "obrigado": SignCategory.INTERACTION,
    "sim": SignCategory.INTERACTION,
    "nao": SignCategory.INTERACTION,
    "ajuda": SignCategory.INTERACTION,
    "repetir": SignCategory.INTERACTION,
    # Perguntas
    "onde": SignCategory.QUESTION,
    "como_chegar": SignCategory.QUESTION,
    "quanto_custa": SignCategory.QUESTION,
    "que_horas": SignCategory.QUESTION,
    # Servicos e necessidades
    "banheiro": SignCategory.SERVICE,
    "comer": SignCategory.SERVICE,
    "agua": SignCategory.SERVICE,
    "hospital": SignCategory.SERVICE,
    "policia": SignCategory.SERVICE,
    "dinheiro": SignCategory.SERVICE,
    "hotel": SignCategory.SERVICE,
    # Transporte
    "onibus": SignCategory.TRANSPORT,
    "taxi": SignCategory.TRANSPORT,
    "aeroporto": SignCategory.TRANSPORT,
    # Pontos turisticos de Aracaju
    "praia": SignCategory.LANDMARK,
    "orla": SignCategory.LANDMARK,
    "mercado": SignCategory.LANDMARK,
    "museu": SignCategory.LANDMARK,
    "igreja": SignCategory.LANDMARK,
    "centro": SignCategory.LANDMARK,
}


def is_known_sign(sign: str) -> bool:
    """Informa se ``sign`` pertence ao vocabulario."""
    return sign in VOCABULARY


def ensure_known_sign(sign: str) -> str:
    """Valida ``sign`` e o devolve.

    Raises:
        UnknownSignError: se o sinal nao pertencer ao vocabulario.
    """
    if not is_known_sign(sign):
        raise UnknownSignError(sign)
    return sign


def signs_by_category(category: SignCategory) -> list[str]:
    """Lista os sinais de uma categoria, em ordem alfabetica."""
    return sorted(sign for sign, cat in VOCABULARY.items() if cat == category)


def all_signs() -> list[str]:
    """Lista todos os sinais do vocabulario, em ordem alfabetica."""
    return sorted(VOCABULARY)


#: Rotulo inteiro estavel por sinal, para uso no treino do classificador.
#: Derivado da ordem alfabetica para ser reproduzivel entre execucoes.
SIGN_TO_INDEX: dict[str, int] = {sign: i for i, sign in enumerate(all_signs())}

#: Mapeamento inverso, para traduzir a saida do classificador.
INDEX_TO_SIGN: dict[int, str] = {i: sign for sign, i in SIGN_TO_INDEX.items()}
