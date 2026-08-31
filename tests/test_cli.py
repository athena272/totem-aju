"""Testes do CLI de coleta.

Cobrem apenas a validacao de argumentos e a listagem do vocabulario, que sao os
caminhos que nao exigem camera nem MediaPipe. E justamente por isso que o import
dessas bibliotecas no CLI e feito dentro de ``run_capture_session``: sem essa
decisao, este arquivo de teste nem poderia importar o modulo.
"""

from __future__ import annotations

import pytest

from totem_aju.cli.capture import build_parser, main
from totem_aju.vocabulary import all_signs


class TestArgumentParsing:
    def test_parses_required_arguments(self) -> None:
        args = build_parser().parse_args(["--sign", "praia", "--signer", "ana"])
        assert args.sign == "praia"
        assert args.signer == "ana"

    def test_parser_does_not_demand_sign(self) -> None:
        """O parser aceita a ausencia; a exigencia e validada em main().

        Exigir --sign no argparse quebraria --list-signs, que existe para
        descobrir quais sinais existem.
        """
        assert build_parser().parse_args(["--list-signs"]).sign is None

    def test_repetitions_has_default(self) -> None:
        args = build_parser().parse_args(["--sign", "praia", "--signer", "ana"])
        assert args.repetitions > 0


class TestListSigns:
    def test_works_without_other_arguments(self) -> None:
        """Consultar o vocabulario nao pode exigir saber o sinal de antemao."""
        assert main(["--list-signs"]) == 0

    def test_prints_whole_vocabulary(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--list-signs"])
        output = capsys.readouterr().out
        for sign in all_signs():
            assert sign in output


class TestRequiredArguments:
    @pytest.mark.parametrize(
        ("argv", "expected_flag"),
        [
            (["--signer", "ana"], "--sign"),
            (["--sign", "praia"], "--signer"),
        ],
    )
    def test_missing_argument_returns_usage_error(
        self,
        argv: list[str],
        expected_flag: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        assert main(argv) == 2
        assert expected_flag in capsys.readouterr().err

    def test_reports_all_missing_arguments(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main([]) == 2
        error = capsys.readouterr().err
        assert "--sign" in error
        assert "--signer" in error


class TestValidation:
    def test_unknown_sign_returns_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["--sign", "inexistente", "--signer", "ana"])
        assert exit_code == 2
        assert "nao pertence ao vocabulario" in capsys.readouterr().err

    def test_non_positive_repetitions_returns_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["--sign", "praia", "--signer", "ana", "--repetitions", "0"])
        assert exit_code == 2
        assert "repetitions" in capsys.readouterr().err
