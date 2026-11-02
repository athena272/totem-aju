"""Divisao leave-one-signer-out para avaliacao sem vazamento por pessoa."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from totem_aju.errors import InsufficientSignersError
from totem_aju.ml.dataset import LabeledSample


@dataclass(frozen=True, slots=True)
class SignerFold:
    """Um fold: treino em todos os sinalizadores menos ``held_out_signer``."""

    held_out_signer: str
    train: tuple[LabeledSample, ...]
    test: tuple[LabeledSample, ...]


def leave_one_signer_out(
    samples: tuple[LabeledSample, ...] | list[LabeledSample],
) -> Iterator[SignerFold]:
    """Gera um fold por sinalizador, em ordem alfabetica do id.

    Raises:
        InsufficientSignersError: se houver menos de dois sinalizadores.
    """
    signers = sorted({sample.signer_id for sample in samples})
    if len(signers) < 2:
        raise InsufficientSignersError(len(signers))

    for held_out in signers:
        train = tuple(s for s in samples if s.signer_id != held_out)
        test = tuple(s for s in samples if s.signer_id == held_out)
        yield SignerFold(held_out_signer=held_out, train=train, test=test)
