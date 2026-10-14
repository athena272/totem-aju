"""Confirmacao de escolhas por contagem de dedos mantida parada.

Logica pura: recebe uma contagem por quadro e decide quando ela vira uma
escolha. O tempo vem de um relogio injetavel, e nao da contagem de quadros,
porque a taxa de quadros do MediaPipe varia muito entre computadores (de 7 a
20 por segundo em CPU) e a pessoa precisa segurar o mesmo tempo em qualquer um.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from totem_aju.config import MAX_FINGER_COUNT


class FingerHoldSelector:
    """Emite uma contagem quando ela fica estavel por ``hold_seconds``.

    Depois de emitir um numero, o mesmo numero so pode ser emitido de novo
    quando a mao sai do quadro por ``release_seconds``. Sem essa trava, quem
    escolhe a categoria 3 e continua com a mao parada escolheria em seguida o
    assunto 3 sem querer.
    """

    def __init__(
        self,
        *,
        hold_seconds: float,
        release_seconds: float = 0.0,
        max_count: int = MAX_FINGER_COUNT,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if hold_seconds <= 0:
            raise ValueError(
                f"'hold_seconds' deve ser positivo, recebido {hold_seconds}."
            )
        if release_seconds < 0:
            raise ValueError(
                f"'release_seconds' nao pode ser negativo, recebido {release_seconds}."
            )
        self._hold_seconds = hold_seconds
        self._release_seconds = release_seconds
        self._max_count = max_count
        self._clock = clock
        self._candidate: int | None = None
        self._candidate_since = 0.0
        self._last_update_at = 0.0
        self._absent_since: float | None = None
        self._last_emitted: int | None = None

    @property
    def candidate(self) -> int | None:
        """Contagem observada no ultimo quadro, ou ``None`` sem mao valida."""
        return self._candidate

    @property
    def awaiting_release(self) -> bool:
        """Indica que a contagem atual ja foi escolhida e espera a mao sair."""
        return self._candidate is not None and self._candidate == self._last_emitted

    @property
    def progress(self) -> float:
        """Fracao do tempo de espera cumprida no ultimo quadro, de 0 a 1."""
        if self._candidate is None:
            return 0.0
        if self.awaiting_release:
            return 1.0
        held = self._last_update_at - self._candidate_since
        return min(held / self._hold_seconds, 1.0)

    def update(self, count: int | None) -> int | None:
        """Registra a contagem do quadro e devolve a escolha, se houver.

        Contagens fora de ``0..max_count`` sao tratadas como mao ausente.
        """
        now = self._clock()
        self._last_update_at = now

        if count is None or not 0 <= count <= self._max_count:
            self._register_absence(now)
            return None

        self._absent_since = None
        if count != self._candidate:
            self._candidate = count
            self._candidate_since = now

        if count == self._last_emitted:
            return None
        if now - self._candidate_since < self._hold_seconds:
            return None

        self._last_emitted = count
        return count

    def reset(self) -> None:
        """Volta ao estado inicial, liberando qualquer escolha anterior."""
        self._candidate = None
        self._absent_since = None
        self._last_emitted = None

    def _register_absence(self, now: float) -> None:
        self._candidate = None
        if self._absent_since is None:
            self._absent_since = now
        if now - self._absent_since >= self._release_seconds:
            self._last_emitted = None
