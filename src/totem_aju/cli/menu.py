"""CLI do menu por dedos: liga a webcam ao preview.

Responsabilidade unica: abrir camera e janela, desenhar o retorno visual e
traduzir erros em mensagens. A contagem, a confirmacao e a publicacao do
estado vivem no pacote :mod:`totem_aju.menu`.

Uso (com o preview aberto em ``python -m http.server`` dentro de ``preview/``):
    totem-menu
    totem-menu --camera 1 --hold-seconds 1.5
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from totem_aju.config import (
    DEFAULT_CAMERA_INDEX,
    GESTURE_STATE_FILENAME,
    MENU_HOLD_SECONDS,
    MENU_RELEASE_SECONDS,
    PREVIEW_DIR,
)
from totem_aju.errors import TotemAjuError
from totem_aju.menu.selector import FingerHoldSelector
from totem_aju.menu.session import FrameUpdate, run_menu_session
from totem_aju.menu.state import GestureStatePublisher, GestureStatus
from totem_aju.vision.camera import FrameSource
from totem_aju.vision.extractor import VideoFrame

_WINDOW_TITLE = "Totem Aju - Menu por dedos"
_QUIT_KEYS = frozenset({ord("q"), 27})  # q ou ESC
_GREEN = (80, 200, 120)
_YELLOW = (60, 200, 240)
_WHITE = (255, 255, 255)


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="totem-menu",
        description=(
            "Conta os dedos pela webcam e envia a escolha ao preview do Totem Aju."
        ),
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=DEFAULT_CAMERA_INDEX,
        help=f"Indice da camera (padrao: {DEFAULT_CAMERA_INDEX}).",
    )
    parser.add_argument(
        "--hold-seconds",
        type=float,
        default=MENU_HOLD_SECONDS,
        help=(
            "Tempo com a mao parada para confirmar a escolha "
            f"(padrao: {MENU_HOLD_SECONDS})."
        ),
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=PREVIEW_DIR / GESTURE_STATE_FILENAME,
        help=(
            "Arquivo lido pelo preview "
            f"(padrao: {PREVIEW_DIR / GESTURE_STATE_FILENAME})."
        ),
    )
    return parser


class MirroredFrameSource:
    """Espelha os quadros, como um espelho: a mao direita aparece a direita."""

    def __init__(
        self, source: FrameSource, flip: Callable[[VideoFrame], VideoFrame]
    ) -> None:
        self._source = source
        self._flip = flip

    def read(self) -> VideoFrame:
        return self._flip(self._source.read())

    def release(self) -> None:
        self._source.release()


def _overlay_text(update: FrameUpdate) -> tuple[str, tuple[int, int, int]]:
    # O OpenCV nao desenha acentos; os textos da janela ficam sem eles.
    if update.fingers is None:
        return "Mostre uma mao para a camera", _WHITE
    if update.awaiting_release:
        return f"{update.fingers} escolhido. Abaixe a mao para repetir", _GREEN
    return f"Dedos: {update.fingers}. Segure parado...", _YELLOW


def _draw_overlay(cv2: Any, frame: VideoFrame, update: FrameUpdate) -> None:
    text, color = _overlay_text(update)
    cv2.putText(frame, text, (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    bar_left, bar_top, bar_width, bar_height = 24, 64, 260, 14
    cv2.rectangle(
        frame,
        (bar_left, bar_top),
        (bar_left + bar_width, bar_top + bar_height),
        _WHITE,
        1,
    )
    filled = int(bar_width * update.progress)
    if filled > 0:
        cv2.rectangle(
            frame,
            (bar_left, bar_top),
            (bar_left + filled, bar_top + bar_height),
            color,
            -1,
        )
    cv2.putText(
        frame,
        "q ou ESC para sair",
        (24, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        _WHITE,
        1,
    )


def run_live_menu(
    *, camera_index: int, hold_seconds: float, publisher: GestureStatePublisher
) -> int:
    """Abre webcam, MediaPipe e janela e roda o menu ate o usuario sair.

    Os imports concretos ficam aqui, e nao no topo do modulo, para que
    ``--help`` e os testes funcionem sem OpenCV e MediaPipe instalados.
    """
    import cv2

    from totem_aju.menu.counter import HeuristicFingerCounter
    from totem_aju.vision.camera import OpenCVCamera
    from totem_aju.vision.mediapipe_extractor import MediaPipeHolisticExtractor

    def show(frame: VideoFrame, update: FrameUpdate) -> bool:
        _draw_overlay(cv2, frame, update)
        cv2.imshow(_WINDOW_TITLE, frame)
        if update.selected is not None:
            print(f"  escolha enviada ao preview: {update.selected} dedo(s)")
        key = cv2.waitKey(1) & 0xFF
        window_open = cv2.getWindowProperty(_WINDOW_TITLE, cv2.WND_PROP_VISIBLE) >= 1
        return key not in _QUIT_KEYS and window_open

    selector = FingerHoldSelector(
        hold_seconds=hold_seconds, release_seconds=MENU_RELEASE_SECONDS
    )
    try:
        with OpenCVCamera(camera_index) as camera, MediaPipeHolisticExtractor() as ext:
            print(
                "Pronto. Mostre de 1 a 4 dedos para escolher a categoria e "
                "segure parado.\nDentro da categoria, 1 a 5 escolhe o assunto e "
                "o punho fechado volta.\nq ou ESC encerra.\n"
            )
            return run_menu_session(
                source=MirroredFrameSource(camera, lambda f: cv2.flip(f, 1)),
                extractor=ext,
                counter=HeuristicFingerCounter(),
                selector=selector,
                publisher=publisher,
                on_frame=show,
            )
    finally:
        cv2.destroyAllWindows()


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada. Devolve o codigo de saida do processo."""
    args = build_parser().parse_args(argv)

    if args.hold_seconds <= 0:
        print("Erro: --hold-seconds deve ser positivo.", file=sys.stderr)
        return 2

    publisher = GestureStatePublisher(args.state_file)
    publisher.publish(GestureStatus.STARTING)
    print("Carregando camera e MediaPipe (pode levar alguns segundos)...")

    try:
        selections = run_live_menu(
            camera_index=args.camera,
            hold_seconds=args.hold_seconds,
            publisher=publisher,
        )
    except KeyboardInterrupt:
        publisher.publish(GestureStatus.STOPPED)
        print("\nMenu por dedos encerrado.")
        return 130
    except TotemAjuError as exc:
        publisher.publish(GestureStatus.ERROR, message=str(exc))
        print(f"\nErro: {exc}", file=sys.stderr)
        return 1

    print(f"Menu por dedos encerrado. {selections} escolha(s) enviada(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
