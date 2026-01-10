from __future__ import annotations

from typing import TYPE_CHECKING

from .meta import MetaCommands

if TYPE_CHECKING:
    from bot import IreBot


class DefaultCommands(
    MetaCommands,
):
    """Default Commands."""


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(DefaultCommands(bot))
