"""Excecoes de dominio do Totem Aju.

Todas herdam de :class:`TotemAjuError`, de modo que a camada de apresentacao
(CLI, futura API) possa capturar um unico tipo e traduzi-lo em mensagem
acionavel, sem expor stack trace ao operador.
"""

from __future__ import annotations


class TotemAjuError(Exception):
    """Erro base do projeto."""


class MediaPipeNotInstalledError(TotemAjuError):
    """MediaPipe nao esta disponivel no interpretador em uso."""

    def __init__(self) -> None:
        super().__init__(
            "MediaPipe nao esta instalado neste interpretador.\n"
            "O MediaPipe publica wheels apenas para Python 3.9 a 3.12.\n"
            "Configure o ambiente com:\n"
            "  py -3.12 -m venv .venv\n"
            "  .\\.venv\\Scripts\\Activate.ps1\n"
            "  pip install -r requirements.txt"
        )


class CameraUnavailableError(TotemAjuError):
    """A camera nao pode ser aberta ou parou de fornecer quadros."""

    def __init__(self, index: int) -> None:
        self.index = index
        super().__init__(
            f"Nao foi possivel usar a camera de indice {index}. "
            "Verifique se ela esta conectada, se outro programa a esta usando "
            "e se o Windows concedeu permissao de acesso a camera."
        )


class UnknownSignError(TotemAjuError):
    """O rotulo informado nao pertence ao vocabulario do projeto."""

    def __init__(self, sign: str) -> None:
        self.sign = sign
        super().__init__(
            f"O sinal '{sign}' nao pertence ao vocabulario do projeto. "
            "Consulte docs/vocabulario-sinais.md e, se o sinal deve existir, "
            "adicione-o em totem_aju.vocabulary antes de coletar."
        )


class EmptySequenceError(TotemAjuError):
    """Tentativa de processar uma sequencia sem nenhum quadro."""

    def __init__(self) -> None:
        super().__init__(
            "A sequencia esta vazia. Nenhum quadro foi capturado, "
            "provavelmente porque a camera nao entregou imagens."
        )


class DatasetEmptyError(TotemAjuError):
    """O manifest nao contem amostras para treinar."""

    def __init__(self, data_root: str) -> None:
        self.data_root = data_root
        super().__init__(
            f"Nenhuma amostra encontrada em '{data_root}'. "
            "Colete com totem-capture ou confira --data-root."
        )


class InsufficientSignersError(TotemAjuError):
    """Leave-one-signer-out exige pelo menos dois sinalizadores."""

    def __init__(self, n_signers: int) -> None:
        self.n_signers = n_signers
        super().__init__(
            f"Ha apenas {n_signers} sinalizador(es). "
            "A avaliacao leave-one-signer-out precisa de pelo menos 2."
        )


class InvalidSampleShapeError(TotemAjuError):
    """Um arquivo .npy nao tem o shape esperado pelo classificador."""

    def __init__(
        self,
        path: str,
        actual: tuple[int, ...],
        expected: tuple[int, int],
    ) -> None:
        self.path = path
        self.actual = actual
        self.expected = expected
        super().__init__(f"Amostra '{path}' tem shape {actual}, esperado {expected}.")
