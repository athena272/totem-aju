"""Metricas de classificacao alinhadas a Aula 11 (matriz, P/R/F1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

LabelVector = NDArray[np.int64]
ConfusionMatrix = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class ClassificationScores:
    """Metricas de um conjunto de predicoes."""

    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float

    def to_dict(self) -> dict[str, float]:
        return {key: round(value, 6) for key, value in asdict(self).items()}


def compute_scores(
    y_true: LabelVector,
    y_pred: LabelVector,
) -> ClassificationScores:
    """Calcula accuracy e P/R/F1 macro (zero_division=0)."""
    return ClassificationScores(
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision_macro=float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        recall_macro=float(
            recall_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        f1_macro=float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    )


def compute_confusion(
    y_true: LabelVector,
    y_pred: LabelVector,
    *,
    labels: list[int],
) -> ConfusionMatrix:
    """Matriz de confusao com linhas/colunas na ordem de ``labels``."""
    return confusion_matrix(y_true, y_pred, labels=labels).astype(np.int64)
