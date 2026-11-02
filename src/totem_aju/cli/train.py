"""CLI de treino e avaliacao do classificador baseline.

Responsabilidade unica: conversar com o operador. A regra de LOSO, metricas e
persistencia vive em :mod:`totem_aju.ml.train`.

Uso:
    totem-train --model random_forest --features mean
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from totem_aju.config import (
    DEFAULT_DATA_ROOT,
    DEFAULT_MODELS_ROOT,
    DEFAULT_TRAIN_SEED,
    FEATURE_MEAN,
    FEATURE_MODES,
    MODEL_ALL,
    MODEL_CHOICES,
    MODEL_RANDOM_FOREST,
)
from totem_aju.errors import TotemAjuError
from totem_aju.ml.models import resolve_model_names
from totem_aju.ml.train import run_training


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="totem-train",
        description=(
            "Treina e avalia o classificador baseline (K-NN / Random Forest) "
            "com leave-one-signer-out."
        ),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help=f"Diretorio raiz do dataset (padrao: {DEFAULT_DATA_ROOT}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_MODELS_ROOT,
        help=f"Diretorio raiz dos artefatos (padrao: {DEFAULT_MODELS_ROOT}).",
    )
    parser.add_argument(
        "--model",
        choices=MODEL_CHOICES,
        default=MODEL_RANDOM_FOREST,
        help=(
            "Modelo a treinar. Use 'all' para K-NN e Random Forest "
            f"(padrao: {MODEL_RANDOM_FOREST})."
        ),
    )
    parser.add_argument(
        "--features",
        choices=FEATURE_MODES,
        default=FEATURE_MEAN,
        help=f"Extracao de features (padrao: {FEATURE_MEAN}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_TRAIN_SEED,
        help=f"Semente para reproducibilidade (padrao: {DEFAULT_TRAIN_SEED}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada. Devolve o codigo de saida do processo."""
    args = build_parser().parse_args(argv)

    if args.seed < 0:
        print("Erro: --seed deve ser nao negativo.", file=sys.stderr)
        return 2

    try:
        model_names = resolve_model_names(args.model)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    try:
        results = []
        for model_name in model_names:
            if args.model == MODEL_ALL:
                print(f"\n=== Modelo: {model_name} ===")
            result = run_training(
                data_root=args.data_root,
                model_name=model_name,
                features=args.features,
                output_dir=args.output_dir,
                seed=args.seed,
                progress=print,
            )
            results.append(result)
    except TotemAjuError as exc:
        print(f"\nErro: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"\nErro: arquivo nao encontrado: {exc}", file=sys.stderr)
        return 1

    print("\nResumo:")
    for result in results:
        agg = result.aggregate
        print(
            f"  {result.model_name}/{result.features}: "
            f"acc={agg['accuracy_mean']:.4f}±{agg['accuracy_std']:.4f} "
            f"f1={agg['f1_macro_mean']:.4f}±{agg['f1_macro_std']:.4f} "
            f"-> {result.output_dir}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
