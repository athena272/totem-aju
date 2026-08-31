"""CLI de coleta de amostras de sinais.

Responsabilidade unica: conversar com o operador da coleta. Toda a regra de
captura, normalizacao e persistencia vive em
:class:`~totem_aju.data.recorder.SampleRecorder`.

Uso:
    totem-capture --sign banheiro --signer joao --repetitions 20
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from totem_aju.config import (
    CAPTURE_DURATION_SECONDS,
    DEFAULT_CAMERA_FPS,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_DATA_ROOT,
    MIN_REPETITIONS_PER_SIGN,
)
from totem_aju.data.recorder import SampleRecorder
from totem_aju.errors import TotemAjuError
from totem_aju.vocabulary import all_signs, is_known_sign

#: Pausa entre repeticoes, para o sinalizador voltar a posicao de repouso.
_PAUSE_BETWEEN_REPETITIONS_SECONDS = 1.5

#: Abaixo desta fracao de quadros com mao detectada, a amostra e sinalizada
#: como suspeita de enquadramento ruim.
_LOW_DETECTION_THRESHOLD = 0.5


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="totem-capture",
        description="Coleta amostras de sinais em Libras para o Totem Aju.",
    )
    parser.add_argument(
        "--sign",
        required=True,
        help="Identificador do sinal. Use --list-signs para ver o vocabulario.",
    )
    parser.add_argument(
        "--signer",
        required=True,
        help="Identificador de quem esta sinalizando (obrigatorio).",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=MIN_REPETITIONS_PER_SIGN,
        help=f"Numero de repeticoes a gravar (padrao: {MIN_REPETITIONS_PER_SIGN}).",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=DEFAULT_CAMERA_INDEX,
        help=f"Indice da camera (padrao: {DEFAULT_CAMERA_INDEX}).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help=f"Diretorio raiz do dataset (padrao: {DEFAULT_DATA_ROOT}).",
    )
    parser.add_argument(
        "--list-signs",
        action="store_true",
        help="Lista o vocabulario e encerra.",
    )
    return parser


def _print_vocabulary() -> None:
    print("Vocabulario do projeto (ver docs/vocabulario-sinais.md):\n")
    for sign in all_signs():
        print(f"  {sign}")


def _frames_per_sample() -> int:
    return max(1, int(CAPTURE_DURATION_SECONDS * DEFAULT_CAMERA_FPS))


def _countdown(seconds: float) -> None:
    remaining = int(seconds)
    for value in range(remaining, 0, -1):
        print(f"  {value}...", flush=True)
        time.sleep(1)
    time.sleep(seconds - remaining)


def run_capture_session(
    *,
    sign: str,
    signer_id: str,
    repetitions: int,
    camera_index: int,
    data_root: Path,
) -> int:
    """Executa a sessao de coleta e devolve o numero de amostras gravadas.

    Os imports concretos ficam aqui, e nao no topo do modulo, para que
    ``--list-signs`` e a validacao de argumentos funcionem mesmo em um ambiente
    sem MediaPipe instalado.
    """
    from totem_aju.vision.camera import OpenCVCamera
    from totem_aju.vision.mediapipe_extractor import MediaPipeHolisticExtractor

    frames = _frames_per_sample()
    recorded = 0

    with OpenCVCamera(camera_index) as camera, MediaPipeHolisticExtractor() as ext:
        recorder = SampleRecorder(source=camera, extractor=ext, data_root=data_root)
        print(
            f"Coletando '{sign}' com o sinalizador '{signer_id}'.\n"
            f"{repetitions} repeticoes, {CAPTURE_DURATION_SECONDS:.1f}s cada.\n"
            "Enquadre cabeca e tronco, com folga nas bordas para as maos.\n"
            "Ctrl+C encerra; as amostras ja gravadas sao preservadas.\n"
        )
        for repetition in range(1, repetitions + 1):
            print(f"Repeticao {repetition}/{repetitions} - prepare-se:")
            _countdown(_PAUSE_BETWEEN_REPETITIONS_SECONDS)
            print("  SINALIZE AGORA", flush=True)

            record = recorder.record_sample(
                sign=sign, signer_id=signer_id, n_frames=frames
            )
            recorded += 1

            if record.detection_ratio < _LOW_DETECTION_THRESHOLD:
                print(
                    f"  gravada, MAS so {record.detection_ratio:.0%} dos quadros "
                    "tiveram mao detectada. Revise o enquadramento e a "
                    "iluminacao; considere apagar esta amostra."
                )
            else:
                print(
                    f"  gravada ({record.detection_ratio:.0%} de deteccao) "
                    f"-> {record.relative_path}"
                )

    return recorded


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada. Devolve o codigo de saida do processo."""
    args = build_parser().parse_args(argv)

    if args.list_signs:
        _print_vocabulary()
        return 0

    if not is_known_sign(args.sign):
        print(
            f"Erro: o sinal '{args.sign}' nao pertence ao vocabulario.\n"
            "Use --list-signs para ver as opcoes.",
            file=sys.stderr,
        )
        return 2

    if args.repetitions <= 0:
        print("Erro: --repetitions deve ser positivo.", file=sys.stderr)
        return 2

    try:
        recorded = run_capture_session(
            sign=args.sign,
            signer_id=args.signer,
            repetitions=args.repetitions,
            camera_index=args.camera,
            data_root=args.data_root,
        )
    except KeyboardInterrupt:
        print("\nColeta interrompida. As amostras gravadas foram preservadas.")
        return 130
    except TotemAjuError as exc:
        print(f"\nErro: {exc}", file=sys.stderr)
        return 1

    print(f"\nConcluido: {recorded} amostra(s) de '{args.sign}' gravada(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
