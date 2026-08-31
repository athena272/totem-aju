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
