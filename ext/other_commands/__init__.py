from __future__ import annotations

from typing import TYPE_CHECKING

from .custom import CustomCommands
from .stable import StableCommands
from .temporary import TemporaryCommands

if TYPE_CHECKING:
    from bot import IreBot


class OtherCommands(
    CustomCommands,
    StableCommands,
    TemporaryCommands,
):
    """Other Commands.

    These aren't bound to any "big" feature.
    Mostly, it contains random commands for chatters.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(OtherCommands(bot))
