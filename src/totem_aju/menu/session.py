"""Loop do menu por dedos: camera, contagem, confirmacao e publicacao.

Recebe todas as dependencias por parametro (fonte de quadros, extrator,
contador de dedos), por isso roda nos testes com dubles, sem webcam.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from totem_aju.errors import TotemAjuError
from totem_aju.menu.selector import FingerHoldSelector
from totem_aju.menu.state import GestureStatePublisher, GestureStatus
from totem_aju.vision.camera import FrameSource
from totem_aju.vision.extractor import LandmarkExtractor, VideoFrame
from totem_aju.vision.schema import FrameLandmarks


class FingerCounter(Protocol):
    """Conta os dedos abertos de um quadro, ou ``None`` se nao houver mao."""

    def count(self, landmarks: FrameLandmarks) -> int | None: ...


@dataclass(frozen=True, slots=True)
class FrameUpdate:
    """Resultado de um quadro, entregue ao ``on_frame`` para o overlay."""

    status: GestureStatus
    fingers: int | None
    progress: float
    awaiting_release: bool
    selected: int | None


#: Recebe o quadro e o resultado. Devolver ``False`` encerra a sessao.
FrameCallback = Callable[[VideoFrame, FrameUpdate], bool]


def run_menu_session(
    *,
    source: FrameSource,
    extractor: LandmarkExtractor,
    counter: FingerCounter,
    selector: FingerHoldSelector,
    publisher: GestureStatePublisher,
    max_frames: int | None = None,
    on_frame: FrameCallback | None = None,
) -> int:
    """Processa quadros ate ``max_frames``, o callback pedir parada ou erro.

    Devolve quantas escolhas foram confirmadas. Ao sair, publica ``stopped``
    ou, se a camera falhar, ``error`` com a mensagem, para o preview nunca
    ficar mostrando um estado que ja nao vale.

    Raises:
        TotemAjuError: repassado depois de publicado como ``error``.
    """
    if max_frames is not None and max_frames <= 0:
        raise ValueError(f"'max_frames' deve ser positivo, recebido {max_frames}.")

    selections = 0
    processed = 0
    error_message: str | None = None
    try:
        while max_frames is None or processed < max_frames:
            frame = source.read()
            update = _process_frame(frame, extractor, counter, selector)
            processed += 1
            if update.selected is not None:
                selections += 1

            publisher.publish(
                update.status,
                fingers=update.fingers,
                progress=update.progress,
                awaiting_release=update.awaiting_release,
                selected=update.selected,
            )
            if on_frame is not None and not on_frame(frame, update):
                break
    except TotemAjuError as exc:
        error_message = str(exc)
        raise
    finally:
        if error_message is None:
            publisher.publish(GestureStatus.STOPPED)
        else:
            publisher.publish(GestureStatus.ERROR, message=error_message)

    return selections


def _process_frame(
    frame: VideoFrame,
    extractor: LandmarkExtractor,
    counter: FingerCounter,
    selector: FingerHoldSelector,
) -> FrameUpdate:
    fingers = counter.count(extractor.extract(frame))
    selected = selector.update(fingers)
    return FrameUpdate(
        status=GestureStatus.NO_HAND if fingers is None else GestureStatus.TRACKING,
        fingers=selector.candidate,
        progress=selector.progress,
        awaiting_release=selector.awaiting_release,
        selected=selected,
    )
