from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import DotaCommands

if TYPE_CHECKING:
    from bot import LueBot


async def setup(bot: LueBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(DotaCommands(bot))
