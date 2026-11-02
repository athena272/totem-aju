"""Factories dos classificadores baseline (scikit-learn)."""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from totem_aju.config import (
    DEFAULT_TRAIN_SEED,
    MODEL_KNN,
    MODEL_RANDOM_FOREST,
)

#: Modelos individuais (sem o alias ``all``).
BASELINE_MODELS: tuple[str, ...] = (MODEL_KNN, MODEL_RANDOM_FOREST)


def build_model(name: str, *, seed: int = DEFAULT_TRAIN_SEED) -> Pipeline:
    """Constroi um ``Pipeline`` sklearn padronizado para o baseline.

    Raises:
        ValueError: se ``name`` nao for ``knn`` nem ``random_forest``.
    """
    if name == MODEL_KNN:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "clf",
                    KNeighborsClassifier(n_neighbors=5, weights="distance"),
                ),
            ]
        )
    if name == MODEL_RANDOM_FOREST:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=200,
                        random_state=seed,
                        n_jobs=1,
                        class_weight="balanced_subsample",
                    ),
                ),
            ]
        )
    raise ValueError(f"Modelo desconhecido: '{name}'. " f"Use um de {BASELINE_MODELS}.")


def resolve_model_names(choice: str) -> tuple[str, ...]:
    """Expande ``all`` na lista de modelos individuais."""
    from totem_aju.config import MODEL_ALL

    if choice == MODEL_ALL:
        return BASELINE_MODELS
    if choice in BASELINE_MODELS:
        return (choice,)
    raise ValueError(
        f"Modelo desconhecido: '{choice}'. "
        f"Use um de {(*BASELINE_MODELS, MODEL_ALL)}."
    )
