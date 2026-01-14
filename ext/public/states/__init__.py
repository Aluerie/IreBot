from __future__ import annotations

from typing import TYPE_CHECKING

from .online import Online

if TYPE_CHECKING:
    from bot import IreBot


class States(
    Online,
):
    """# TODO."""


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(States(bot))
