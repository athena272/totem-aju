"""Testes do CLI totem-train."""

from __future__ import annotations

from pathlib import Path

from tests.ml_helpers import write_dataset_on_disk
from totem_aju.cli.train import build_parser, main


class TestTrainCli:
    def test_help_exits_zero(self) -> None:
        parser = build_parser()
        assert parser.prog == "totem-train"

    def test_empty_dataset_returns_1(self, tmp_path: Path) -> None:
        code = main(
            [
                "--data-root",
                str(tmp_path),
                "--output-dir",
                str(tmp_path / "out"),
                "--model",
                "knn",
            ]
        )
        assert code == 1

    def test_negative_seed_returns_2(self, tmp_path: Path) -> None:
        code = main(
            [
                "--data-root",
                str(tmp_path),
                "--seed",
                "-1",
            ]
        )
        assert code == 2

    def test_happy_path_writes_artifacts(self, tmp_path: Path) -> None:
        data_root = write_dataset_on_disk(tmp_path / "data")
        output = tmp_path / "models"
        code = main(
            [
                "--data-root",
                str(data_root),
                "--output-dir",
                str(output),
                "--model",
                "random_forest",
                "--features",
                "mean",
                "--seed",
                "0",
            ]
        )
        assert code == 0
        runs = list(output.iterdir())
        assert len(runs) == 1
        assert (runs[0] / "metrics.json").exists()
        assert (runs[0] / "model.joblib").exists()
