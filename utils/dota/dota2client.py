from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from steam import PersonaState
from steam.ext.dota2 import Client

try:
    import config
except ImportError:
    import sys

    sys.path.append("D:/LAPTOP/AluBot")
    import config

if TYPE_CHECKING:
    from bot import LueBot

log = logging.getLogger(__name__)

__all__ = ("Dota2Client",)


class Dota2Client(Client):
    """Subclass for SteamIO's Client.

    Used to communicate with Dota 2 Game Coordinator in order to track information about my profile real-time.
    """

    def __init__(self, twitch_bot: LueBot) -> None:
        super().__init__(state=PersonaState.Online)  # .Invisible
        self.bot: LueBot = twitch_bot

    @override
    async def login(self) -> None:
        await super().login(config.STEAM_USERNAME, config.STEAM_PASSWORD)

    @override
    async def on_ready(self) -> None:
        log.info("Dota 2 Client: Ready - Successfully %s", self.user.name)
        await self.wait_until_gc_ready()
        log.info("Dota 2 Game Coordinator: Ready")
