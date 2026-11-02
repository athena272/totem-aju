"""Testes das metricas de classificacao."""

from __future__ import annotations

import numpy as np

from totem_aju.ml.metrics import compute_confusion, compute_scores


class TestComputeScores:
    def test_perfect_predictions(self) -> None:
        y = np.array([0, 1, 2, 0, 1, 2], dtype=np.int64)
        scores = compute_scores(y, y)
        assert scores.accuracy == 1.0
        assert scores.f1_macro == 1.0
        assert scores.precision_macro == 1.0
        assert scores.recall_macro == 1.0

    def test_all_wrong_binary(self) -> None:
        y_true = np.array([0, 0, 1, 1], dtype=np.int64)
        y_pred = np.array([1, 1, 0, 0], dtype=np.int64)
        scores = compute_scores(y_true, y_pred)
        assert scores.accuracy == 0.0
        assert scores.f1_macro == 0.0


class TestComputeConfusion:
    def test_identity_matrix_when_perfect(self) -> None:
        y = np.array([0, 1, 2, 0, 1, 2], dtype=np.int64)
        matrix = compute_confusion(y, y, labels=[0, 1, 2])
        assert matrix.tolist() == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
