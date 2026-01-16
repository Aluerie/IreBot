from __future__ import annotations

from typing import TYPE_CHECKING

from .stable import StableCommands
from .temporary import TemporaryCommands

if TYPE_CHECKING:
    from bot import IreBot


class UncategorizedPersonalCommands(
    StableCommands,
    TemporaryCommands,
):
    """Uncategorized Personal Commands.

    These commands just do not belong to any specific "categorized" personal component
    so they found their place here.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(UncategorizedPersonalCommands(bot))
