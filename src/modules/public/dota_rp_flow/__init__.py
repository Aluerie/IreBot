from __future__ import annotations

from typing import TYPE_CHECKING

from .component import Dota2RichPresenceFlow

if TYPE_CHECKING:
    from core import IreBot


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Dota2RichPresenceFlow(bot))
