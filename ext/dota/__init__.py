from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import DotaCommands

if TYPE_CHECKING:
    from bot import IreBot


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(DotaCommands(bot))
