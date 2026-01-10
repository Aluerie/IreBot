from __future__ import annotations

from typing import TYPE_CHECKING

from .gameflow import GameFlow

if TYPE_CHECKING:
    from bot import IreBot


class Dota(
    GameFlow,
):
    """Dota 2 Features."""


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Dota(bot))
