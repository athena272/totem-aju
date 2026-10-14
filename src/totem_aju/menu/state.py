"""Estado da camera de gestos, publicado num JSON lido pelo preview.

O preview e um site estatico servido por ``python -m http.server``; o jeito
mais simples de o processo da camera falar com ele e gravar um arquivo que o
site consulta por polling. Este modulo define o formato desse arquivo e como
grava-lo sem que o navegador leia um JSON pela metade.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from totem_aju.config import GESTURE_STATE_MIN_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

#: No Windows, substituir um arquivo que outro processo esta lendo (o servidor
#: do preview) falha com "Acesso negado" por alguns milissegundos. Algumas
#: tentativas curtas resolvem sem atrasar o loop da camera de forma perceptivel.
_REPLACE_ATTEMPTS = 4
_REPLACE_RETRY_DELAY_SECONDS = 0.01


class GestureStatus(StrEnum):
    """Situacao da camera de gestos, exibida no rodape do preview."""

    STARTING = "starting"
    TRACKING = "tracking"
    NO_HAND = "no_hand"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class GestureSelection:
    """Escolha confirmada. ``event_id`` permite ao site aplica-la uma vez so."""

    fingers: int
    event_id: int
    at_ms: int


@dataclass(frozen=True, slots=True)
class GestureState:
    """Fotografia do estado publicada a cada gravacao."""

    status: GestureStatus
    updated_at_ms: int
    fingers: int | None = None
    progress: float = 0.0
    awaiting_release: bool = False
    selection: GestureSelection | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["progress"] = round(self.progress, 3)
        return data


def _wall_clock_ms() -> int:
    return int(time.time() * 1000)


class GestureStatePublisher:
    """Grava o estado em disco com escrita atomica e limite de frequencia.

    A ultima escolha confirmada acompanha todas as gravacoes seguintes. Assim,
    se uma gravacao falhar (no Windows, o servidor pode estar lendo o arquivo
    naquele instante), a escolha chega ao site na gravacao seguinte.
    """

    def __init__(
        self,
        path: Path,
        *,
        min_interval_seconds: float = GESTURE_STATE_MIN_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        wall_clock_ms: Callable[[], int] = _wall_clock_ms,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._path = path
        self._min_interval = min_interval_seconds
        self._clock = clock
        self._wall_clock_ms = wall_clock_ms
        self._sleep = sleep
        self._selection: GestureSelection | None = None
        self._pending_selection = False
        self._last_status: GestureStatus | None = None
        self._last_written_at: float | None = None

    @property
    def path(self) -> Path:
        return self._path

    def publish(
        self,
        status: GestureStatus,
        *,
        fingers: int | None = None,
        progress: float = 0.0,
        awaiting_release: bool = False,
        selected: int | None = None,
        message: str | None = None,
    ) -> bool:
        """Publica o estado. Devolve ``True`` se o arquivo foi gravado.

        Mudanca de status e nova escolha gravam na hora; o restante respeita
        o intervalo minimo entre gravacoes.
        """
        now_ms = self._wall_clock_ms()
        if selected is not None:
            self._register_selection(selected, now_ms)

        if not self._should_write(status):
            return False

        state = GestureState(
            status=status,
            updated_at_ms=now_ms,
            fingers=fingers,
            progress=progress,
            awaiting_release=awaiting_release,
            selection=self._selection,
            message=message,
        )
        if not self._write(state):
            return False

        self._last_status = status
        self._last_written_at = self._clock()
        self._pending_selection = False
        return True

    def _register_selection(self, fingers: int, now_ms: int) -> None:
        previous_id = self._selection.event_id if self._selection else 0
        # O id usa o relogio de parede para nao repetir ids de uma execucao
        # anterior, que o site ainda pode ter em memoria.
        event_id = max(previous_id + 1, now_ms)
        self._selection = GestureSelection(
            fingers=fingers, event_id=event_id, at_ms=now_ms
        )
        self._pending_selection = True

    def _should_write(self, status: GestureStatus) -> bool:
        if self._pending_selection or status != self._last_status:
            return True
        if self._last_written_at is None:
            return True
        return self._clock() - self._last_written_at >= self._min_interval

    def _write(self, state: GestureState) -> bool:
        temporary = self._path.with_name(f"{self._path.name}.tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(
                json.dumps(state.to_dict(), ensure_ascii=False), encoding="utf-8"
            )
            self._replace_with_retry(temporary)
        except OSError as exc:
            logger.warning("Nao foi possivel gravar %s: %s", self._path, exc)
            return False
        return True

    def _replace_with_retry(self, temporary: Path) -> None:
        for attempt in range(1, _REPLACE_ATTEMPTS + 1):
            try:
                temporary.replace(self._path)
            except PermissionError:
                if attempt == _REPLACE_ATTEMPTS:
                    raise
                self._sleep(_REPLACE_RETRY_DELAY_SECONDS)
            else:
                return
