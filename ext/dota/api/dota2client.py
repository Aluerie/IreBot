from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING, override

from steam import PersonaState
from steam.ext.dota2 import Client

from config import config

from .pulsefire_clients import SteamWebAPIClient, StratzClient
from .storage import Items

if TYPE_CHECKING:
    from steam.ext.dota2 import PartialUser

    from bot import IreBot

log = logging.getLogger(__name__)

__all__ = ("Dota2Client",)


class Dota2Client(Client):
    """Subclass for SteamIO's Client.

    Used to communicate with Dota 2 Game Coordinator in order to track information about my profile real-time.
    """

    def __init__(self, twitch_bot: IreBot) -> None:
        super().__init__(state=PersonaState.Online)  # .Invisible
        self.bot: IreBot = twitch_bot
        self.started: bool = False

        self.steam_web_api = SteamWebAPIClient()
        self.stratz = StratzClient()
        self.items = Items(twitch_bot)

    def irene(self) -> PartialUser:
        return self.instantiate_partial_user(config["STEAM"]["IRENE_ID64"])

    async def start_helpers(self) -> None:
        if not self.started:
            await self.steam_web_api.__aenter__()  # noqa: PLC2801
            await self.stratz.__aenter__()  # noqa: PLC2801
            self.items.start()

    @override
    async def login(self) -> None:
        account_credentials = (
            config["STEAM"]["IRENESTEST"] if platform.system() == "Windows" else config["STEAM"]["IRENESBOT"]
        )
        username, password = account_credentials["USERNAME"], account_credentials["PASSWORD"]
        await super().login(username, password)

    @override
    async def close(self) -> None:
        await self.stratz.__aexit__()
        await self.steam_web_api.__aexit__()
        self.items.close()

    @override
    async def on_ready(self) -> None:
        log.info("Dota 2 Client: Ready - Successfully %s", self.user.name)
        await self.wait_until_gc_ready()
        log.info("Dota 2 Game Coordinator: Ready")
