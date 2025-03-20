from __future__ import annotations

from typing import TYPE_CHECKING

from .alerts import Alerts
from .counters import Counters
from .keywords import Keywords
from .timers import Timers

if TYPE_CHECKING:
    from bot import IreBot


class Chatter(
    Alerts,
    Counters,
    Keywords,
    Timers,
):
    """Chatter bot functionality.

    These features control how bot reacts/responds to certain messages/events in the chat.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Chatter(bot))
