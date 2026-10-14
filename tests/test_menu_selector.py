"""Testes da confirmacao de escolhas por contagem de dedos."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from totem_aju.menu.selector import FingerHoldSelector

#: Intervalo simulado entre quadros, em segundos.
FRAME_SECONDS = 0.1


class FrameClock:
    """Relogio que avanca ``FRAME_SECONDS`` a cada leitura (uma por quadro)."""

    def __init__(self) -> None:
        self._now = -FRAME_SECONDS

    def __call__(self) -> float:
        self._now += FRAME_SECONDS
        return self._now


def make_selector(*, hold_frames: int, release_frames: int = 1) -> FingerHoldSelector:
    """Seletor cujos tempos equivalem a ``hold_frames`` e ``release_frames``.

    O primeiro quadro de uma contagem marca o inicio da espera; por isso a
    escolha sai no quadro ``hold_frames``, depois de ``hold_frames - 1``
    intervalos. Descontar meio intervalo coloca o limite entre dois quadros,
    longe do arredondamento de ponto flutuante.
    """
    if hold_frames < 2:
        raise ValueError("Use hold_frames >= 2: o primeiro quadro so inicia a espera.")
    return FingerHoldSelector(
        hold_seconds=(hold_frames - 1.5) * FRAME_SECONDS,
        release_seconds=max(release_frames - 1.5, 0.0) * FRAME_SECONDS,
        clock=FrameClock(),
    )


def feed(selector: FingerHoldSelector, counts: Iterable[int | None]) -> list[int]:
    """Alimenta o seletor e devolve apenas as escolhas emitidas."""
    emitted = []
    for count in counts:
        choice = selector.update(count)
        if choice is not None:
            emitted.append(choice)
    return emitted


class TestConfirmation:
    def test_emits_after_hold_time(self) -> None:
        selector = make_selector(hold_frames=3)
        assert selector.update(2) is None
        assert selector.update(2) is None
        assert selector.update(2) == 2

    def test_zero_fingers_is_a_valid_choice(self) -> None:
        """Punho fechado e o gesto de voltar no preview."""
        selector = make_selector(hold_frames=2)
        assert feed(selector, [0, 0]) == [0]

    def test_count_change_restarts_hold(self) -> None:
        selector = make_selector(hold_frames=3)
        assert feed(selector, [2, 2, 3, 3]) == []
        assert selector.update(3) == 3

    def test_hand_absence_restarts_hold(self) -> None:
        selector = make_selector(hold_frames=3)
        assert feed(selector, [4, 4, None, 4, 4]) == []
        assert selector.update(4) == 4

    def test_slow_frame_rate_needs_the_same_time(self) -> None:
        """Com poucos quadros por segundo, o tempo de espera nao muda."""
        ticks = iter([0.0, 0.5, 1.0])
        selector = FingerHoldSelector(hold_seconds=1.0, clock=lambda: next(ticks))
        assert feed(selector, [3, 3]) == []
        assert selector.update(3) == 3


class TestRearm:
    def test_does_not_repeat_while_hand_stays(self) -> None:
        selector = make_selector(hold_frames=2)
        assert feed(selector, [3] * 10) == [3]

    def test_brief_flicker_does_not_repeat_same_choice(self) -> None:
        """Categoria 3 escolhida nao pode virar assunto 3 por oscilacao."""
        selector = make_selector(hold_frames=2, release_frames=3)
        assert feed(selector, [3, 3, 2, 3, 3, None, 3, 3]) == [3]

    def test_different_count_can_be_chosen_without_release(self) -> None:
        selector = make_selector(hold_frames=2)
        assert feed(selector, [3, 3, 1, 1]) == [3, 1]

    def test_same_count_after_release(self) -> None:
        selector = make_selector(hold_frames=2, release_frames=2)
        assert feed(selector, [2, 2, None, None, 2, 2]) == [2, 2]

    def test_reset_releases_last_choice(self) -> None:
        selector = make_selector(hold_frames=2)
        assert feed(selector, [1, 1]) == [1]
        selector.reset()
        assert feed(selector, [1, 1]) == [1]


class TestFeedback:
    def test_progress_grows_until_choice(self) -> None:
        selector = make_selector(hold_frames=3)
        assert selector.progress == 0.0
        selector.update(1)
        assert selector.progress == 0.0
        selector.update(1)
        assert selector.progress == pytest.approx(0.1 / 0.15)

    def test_after_choice_progress_is_full_and_awaits_release(self) -> None:
        selector = make_selector(hold_frames=2)
        feed(selector, [5, 5])
        assert selector.progress == 1.0
        assert selector.awaiting_release
        assert selector.candidate == 5

    def test_without_hand_there_is_no_candidate(self) -> None:
        selector = make_selector(hold_frames=2)
        feed(selector, [2, None])
        assert selector.candidate is None
        assert selector.progress == 0.0
        assert not selector.awaiting_release


class TestValidation:
    @pytest.mark.parametrize("count", [-1, 6, 10])
    def test_out_of_range_counts_are_treated_as_absence(self, count: int) -> None:
        selector = make_selector(hold_frames=2)
        assert feed(selector, [count, count, count]) == []
        assert selector.candidate is None

    @pytest.mark.parametrize("hold_seconds", [0.0, -1.0])
    def test_rejects_non_positive_hold(self, hold_seconds: float) -> None:
        with pytest.raises(ValueError, match="hold_seconds"):
            FingerHoldSelector(hold_seconds=hold_seconds)

    def test_rejects_negative_release(self) -> None:
        with pytest.raises(ValueError, match="release_seconds"):
            FingerHoldSelector(hold_seconds=1.0, release_seconds=-0.1)
