from __future__ import annotations

from typing import TYPE_CHECKING

from .control import Control
from .webhook_logs import LogsViaWebhook

if TYPE_CHECKING:
    from bot import IreBot


class DevTools(
    Control,
    LogsViaWebhook,
):
    """Developer functionality.

    These features are to be used by the developers only.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(DevTools(bot))
