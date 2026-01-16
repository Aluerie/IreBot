from __future__ import annotations

from typing import TYPE_CHECKING

from .streamers import StreamerIndexManagement

if TYPE_CHECKING:
    from bot import IreBot


class Required(
    StreamerIndexManagement,
):
    """Components required for other bot components to work."""


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Required(bot))
