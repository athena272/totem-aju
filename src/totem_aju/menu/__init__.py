"""Menu por dedos: transforma a contagem de dedos em escolhas para o preview.

O pacote so percebe a mao e publica o estado. O significado de cada numero
(categoria, assunto, voltar) e decidido pelo preview, que conhece o conteudo.
"""

from totem_aju.menu.selector import FingerHoldSelector
from totem_aju.menu.session import FingerCounter, FrameUpdate, run_menu_session
from totem_aju.menu.state import (
    GestureSelection,
    GestureState,
    GestureStatePublisher,
    GestureStatus,
)

__all__ = [
    "FingerCounter",
    "FingerHoldSelector",
    "FrameUpdate",
    "GestureSelection",
    "GestureState",
    "GestureStatePublisher",
    "GestureStatus",
    "run_menu_session",
]
