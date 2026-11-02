"""Testes da divisao leave-one-signer-out."""

from __future__ import annotations

import pytest

from tests.ml_helpers import make_labeled_sample, make_separable_dataset
from totem_aju.errors import InsufficientSignersError
from totem_aju.ml.split import leave_one_signer_out


class TestLeaveOneSignerOut:
    def test_one_fold_per_signer(self) -> None:
        dataset = make_separable_dataset()
        folds = list(leave_one_signer_out(dataset.samples))
        assert [fold.held_out_signer for fold in folds] == [
            "alice",
            "bruno",
            "carla",
        ]

    def test_held_out_not_in_train(self) -> None:
        dataset = make_separable_dataset()
        for fold in leave_one_signer_out(dataset.samples):
            train_signers = {sample.signer_id for sample in fold.train}
            test_signers = {sample.signer_id for sample in fold.test}
            assert fold.held_out_signer not in train_signers
            assert test_signers == {fold.held_out_signer}
            assert len(fold.train) + len(fold.test) == dataset.n_samples

    def test_requires_two_signers(self) -> None:
        samples = (
            make_labeled_sample(sign="ola", signer_id="sozinho", fill=0.0),
            make_labeled_sample(sign="sim", signer_id="sozinho", fill=1.0),
        )
        with pytest.raises(InsufficientSignersError):
            list(leave_one_signer_out(samples))
