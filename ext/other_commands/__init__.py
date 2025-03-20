from __future__ import annotations

from typing import TYPE_CHECKING

from .custom import CustomCommands
from .stable import SimpleCommands
from .temporary import MiscellaneousCommands
from .translation import Translations

if TYPE_CHECKING:
    from bot import IreBot


class OtherCommands(
    CustomCommands,
    SimpleCommands,
    MiscellaneousCommands,
    Translations,
):
    """Other Commands.

    These aren't bound to any "big" feature.
    Mostly, it contains random commands for chatters.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(OtherCommands(bot))
