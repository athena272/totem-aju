"""Testes do vocabulario.

Protegem o contrato de dados: os identificadores dos sinais estao gravados nas
amostras ja coletadas, portanto renomea-los quebraria o dataset.
"""

from __future__ import annotations

import pytest

from totem_aju.errors import UnknownSignError
from totem_aju.vocabulary import (
    INDEX_TO_SIGN,
    SIGN_TO_INDEX,
    VOCABULARY,
    SignCategory,
    all_signs,
    ensure_known_sign,
    is_known_sign,
    signs_by_category,
)


class TestVocabularyIntegrity:
    def test_identifiers_are_snake_case_ascii(self) -> None:
        """Sem acento e sem espaco: os rotulos viram nome de arquivo."""
        for sign in VOCABULARY:
            assert sign.isascii(), sign
            assert sign == sign.lower(), sign
            assert " " not in sign, sign
            assert "-" not in sign, sign

    def test_every_sign_has_a_valid_category(self) -> None:
        for category in VOCABULARY.values():
            assert isinstance(category, SignCategory)

    def test_all_categories_are_used(self) -> None:
        for category in SignCategory:
            assert signs_by_category(category), category

    def test_all_signs_is_sorted(self) -> None:
        assert all_signs() == sorted(all_signs())

    def test_all_signs_matches_vocabulary_size(self) -> None:
        assert len(all_signs()) == len(VOCABULARY)


class TestKnownSign:
    def test_recognizes_existing_sign(self) -> None:
        assert is_known_sign("banheiro")

    def test_rejects_unknown_sign(self) -> None:
        assert not is_known_sign("nao_existe")

    def test_rejects_sign_with_wrong_case(self) -> None:
        assert not is_known_sign("Banheiro")

    def test_ensure_returns_the_sign(self) -> None:
        assert ensure_known_sign("praia") == "praia"

    def test_ensure_raises_for_unknown_sign(self) -> None:
        with pytest.raises(UnknownSignError):
            ensure_known_sign("nao_existe")


class TestLabelIndices:
    def test_indices_are_contiguous_from_zero(self) -> None:
        assert sorted(SIGN_TO_INDEX.values()) == list(range(len(VOCABULARY)))

    def test_index_mapping_is_bijective(self) -> None:
        for sign, index in SIGN_TO_INDEX.items():
            assert INDEX_TO_SIGN[index] == sign

    def test_indices_follow_alphabetical_order(self) -> None:
        """Ordem derivada do alfabeto para ser reproduzivel entre execucoes."""
        assert [INDEX_TO_SIGN[i] for i in range(len(VOCABULARY))] == all_signs()
