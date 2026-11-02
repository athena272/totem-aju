"""Testes de integracao do orquestrador de treino."""

from __future__ import annotations

import json
from pathlib import Path

from tests.ml_helpers import make_separable_dataset
from totem_aju.config import FEATURE_MEAN, MODEL_KNN, MODEL_RANDOM_FOREST
from totem_aju.ml.train import run_training


class TestRunTraining:
    def test_separable_dataset_beats_chance(self, tmp_path: Path) -> None:
        dataset = make_separable_dataset()
        messages: list[str] = []
        result = run_training(
            model_name=MODEL_RANDOM_FOREST,
            features=FEATURE_MEAN,
            output_dir=tmp_path,
            seed=0,
            progress=messages.append,
            dataset=dataset,
        )
        # 3 classes -> chance ~0.33; dataset e linearmente separavel por media.
        assert result.aggregate["accuracy_mean"] > 0.8
        assert result.aggregate["f1_macro_mean"] > 0.8
        assert (result.output_dir / "metrics.json").exists()
        assert (result.output_dir / "confusion_matrix.json").exists()
        assert (result.output_dir / "model.joblib").exists()
        assert (result.output_dir / "report.md").exists()
        assert any("Carregando dataset" in message for message in messages)
        assert any("Salvando artefatos" in message for message in messages)

        payload = json.loads(
            (result.output_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert payload["split"] == "leave_one_signer_out"
        assert len(payload["folds"]) == 3
        assert payload["n_samples"] == dataset.n_samples

    def test_knn_also_runs(self, tmp_path: Path) -> None:
        result = run_training(
            model_name=MODEL_KNN,
            features=FEATURE_MEAN,
            output_dir=tmp_path,
            seed=0,
            dataset=make_separable_dataset(),
        )
        assert result.model_name == MODEL_KNN
        assert result.aggregate["accuracy_mean"] > 0.8
