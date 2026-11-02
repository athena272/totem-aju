"""Orquestracao do treino baseline com leave-one-signer-out."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from totem_aju.config import (
    DEFAULT_MODELS_ROOT,
    DEFAULT_TRAIN_SEED,
    FEATURE_MEAN,
)
from totem_aju.ml.dataset import LoadedDataset, load_dataset
from totem_aju.ml.features import samples_to_matrix
from totem_aju.ml.metrics import (
    ClassificationScores,
    compute_confusion,
    compute_scores,
)
from totem_aju.ml.models import build_model
from totem_aju.ml.split import leave_one_signer_out
from totem_aju.vocabulary import INDEX_TO_SIGN

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class FoldResult:
    """Resultado de um fold leave-one-signer-out."""

    held_out_signer: str
    n_train: int
    n_test: int
    scores: ClassificationScores


@dataclass(frozen=True, slots=True)
class TrainResult:
    """Resultado agregado de uma execucao de treino."""

    model_name: str
    features: str
    seed: int
    dataset: LoadedDataset
    folds: tuple[FoldResult, ...]
    aggregate: dict[str, float]
    confusion: list[list[int]]
    label_names: tuple[str, ...]
    output_dir: Path


def _noop_progress(_message: str) -> None:
    return None


def _aggregate_scores(folds: tuple[FoldResult, ...]) -> dict[str, float]:
    accuracies = np.array([fold.scores.accuracy for fold in folds], dtype=np.float64)
    f1s = np.array([fold.scores.f1_macro for fold in folds], dtype=np.float64)
    precisions = np.array(
        [fold.scores.precision_macro for fold in folds], dtype=np.float64
    )
    recalls = np.array([fold.scores.recall_macro for fold in folds], dtype=np.float64)
    return {
        "accuracy_mean": round(float(accuracies.mean()), 6),
        "accuracy_std": round(float(accuracies.std(ddof=0)), 6),
        "precision_macro_mean": round(float(precisions.mean()), 6),
        "precision_macro_std": round(float(precisions.std(ddof=0)), 6),
        "recall_macro_mean": round(float(recalls.mean()), 6),
        "recall_macro_std": round(float(recalls.std(ddof=0)), 6),
        "f1_macro_mean": round(float(f1s.mean()), 6),
        "f1_macro_std": round(float(f1s.std(ddof=0)), 6),
    }


def _make_run_dir(output_root: Path, model_name: str, features: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output_root / f"{stamp}_{model_name}_{features}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_report(result: TrainResult) -> None:
    lines = [
        f"# Relatorio de treino — {result.model_name} / {result.features}",
        "",
        f"- Amostras: **{result.dataset.n_samples}**",
        f"- Sinais: **{len(result.dataset.signs)}**",
        f"- Sinalizadores: **{len(result.dataset.signers)}**",
        f"- Split: leave-one-signer-out ({len(result.folds)} folds)",
        f"- Seed: `{result.seed}`",
        "",
        "## Agregado",
        "",
        f"- Accuracy: {result.aggregate['accuracy_mean']:.4f} "
        f"± {result.aggregate['accuracy_std']:.4f}",
        f"- Precision macro: {result.aggregate['precision_macro_mean']:.4f} "
        f"± {result.aggregate['precision_macro_std']:.4f}",
        f"- Recall macro: {result.aggregate['recall_macro_mean']:.4f} "
        f"± {result.aggregate['recall_macro_std']:.4f}",
        f"- F1 macro: {result.aggregate['f1_macro_mean']:.4f} "
        f"± {result.aggregate['f1_macro_std']:.4f}",
        "",
        "## Folds",
        "",
        "| Held-out | n_train | n_test | accuracy | F1 macro |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for fold in result.folds:
        lines.append(
            f"| {fold.held_out_signer} | {fold.n_train} | {fold.n_test} | "
            f"{fold.scores.accuracy:.4f} | {fold.scores.f1_macro:.4f} |"
        )
    lines.extend(["", "## Matriz de confusao (soma dos folds)", ""])
    header = "| | " + " | ".join(result.label_names) + " |"
    sep = "| --- | " + " | ".join("---:" for _ in result.label_names) + " |"
    lines.extend([header, sep])
    for name, row in zip(result.label_names, result.confusion, strict=True):
        cells = " | ".join(str(value) for value in row)
        lines.append(f"| {name} | {cells} |")
    lines.append("")
    (result.output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_artifacts(result: TrainResult, model: Any) -> None:
    metrics_payload = {
        "model": result.model_name,
        "features": result.features,
        "seed": result.seed,
        "n_samples": result.dataset.n_samples,
        "n_signs": len(result.dataset.signs),
        "n_signers": len(result.dataset.signers),
        "signers": sorted(result.dataset.signers),
        "split": "leave_one_signer_out",
        "folds": [
            {
                "held_out_signer": fold.held_out_signer,
                "n_train": fold.n_train,
                "n_test": fold.n_test,
                **fold.scores.to_dict(),
            }
            for fold in result.folds
        ],
        "aggregate": result.aggregate,
        "label_names": list(result.label_names),
    }
    (result.output_dir / "metrics.json").write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (result.output_dir / "confusion_matrix.json").write_text(
        json.dumps(
            {
                "labels": list(result.label_names),
                "matrix": result.confusion,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    joblib.dump(model, result.output_dir / "model.joblib")
    _write_report(result)


def run_training(
    *,
    data_root: Path | None = None,
    model_name: str,
    features: str = FEATURE_MEAN,
    output_dir: Path | None = None,
    seed: int = DEFAULT_TRAIN_SEED,
    progress: ProgressCallback | None = None,
    dataset: LoadedDataset | None = None,
) -> TrainResult:
    """Executa LOSO, treina o modelo final e grava artefatos.

    ``dataset`` pode ser injetado nos testes para evitar I/O real.
    """
    report = progress or _noop_progress
    report("Carregando dataset...")
    loaded = dataset if dataset is not None else load_dataset(data_root)
    report(
        f"Dataset: {loaded.n_samples} amostras, "
        f"{len(loaded.signs)} sinais, {len(loaded.signers)} sinalizadores."
    )

    # Restringe labels presentes no dataset (testes usam subset do vocabulario).
    present_labels = sorted({sample.label for sample in loaded.samples})
    label_names = tuple(INDEX_TO_SIGN[i] for i in present_labels)

    folds: list[FoldResult] = []
    y_true_all: list[int] = []
    y_pred_all: list[int] = []
    fold_list = list(leave_one_signer_out(loaded.samples))
    n_folds = len(fold_list)

    for index, fold in enumerate(fold_list, start=1):
        report(
            f"Avaliando leave-one-signer-out "
            f"(fold {index}/{n_folds}: teste={fold.held_out_signer})..."
        )
        x_train, y_train, _ = samples_to_matrix(fold.train, mode=features)
        x_test, y_test, _ = samples_to_matrix(fold.test, mode=features)

        report("Treinando...")
        model = build_model(model_name, seed=seed)
        model.fit(x_train, y_train)

        report("Avaliando...")
        y_pred = model.predict(x_test)
        scores = compute_scores(y_test, y_pred)
        folds.append(
            FoldResult(
                held_out_signer=fold.held_out_signer,
                n_train=len(fold.train),
                n_test=len(fold.test),
                scores=scores,
            )
        )
        y_true_all.extend(int(value) for value in y_test)
        y_pred_all.extend(int(value) for value in y_pred)

    fold_results = tuple(folds)
    aggregate = _aggregate_scores(fold_results)
    confusion = compute_confusion(
        np.asarray(y_true_all, dtype=np.int64),
        np.asarray(y_pred_all, dtype=np.int64),
        labels=present_labels,
    )

    output_root = Path(output_dir) if output_dir is not None else DEFAULT_MODELS_ROOT
    run_dir = _make_run_dir(output_root, model_name, features)
    report(f"Salvando artefatos em {run_dir}...")

    report("Treinando modelo final em todas as amostras...")
    x_all, y_all, _ = samples_to_matrix(loaded.samples, mode=features)
    final_model = build_model(model_name, seed=seed)
    final_model.fit(x_all, y_all)

    result = TrainResult(
        model_name=model_name,
        features=features,
        seed=seed,
        dataset=loaded,
        folds=fold_results,
        aggregate=aggregate,
        confusion=confusion.tolist(),
        label_names=label_names,
        output_dir=run_dir,
    )
    _write_artifacts(result, final_model)
    report(
        f"Pronto. Accuracy {aggregate['accuracy_mean']:.4f} "
        f"± {aggregate['accuracy_std']:.4f}; "
        f"F1 macro {aggregate['f1_macro_mean']:.4f} "
        f"± {aggregate['f1_macro_std']:.4f}."
    )
    return result
