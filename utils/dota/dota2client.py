from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple, override

from steam import PersonaState
from steam.ext.dota2 import Client

from config import config

from .pulsefire_clients import SteamWebAPIClient, StratzClient
from .storage import Items

if TYPE_CHECKING:
    from steam.ext.dota2 import PartialUser, User

    from bot import IreBot

log = logging.getLogger(__name__)

__all__ = (
    "Dota2Client",
    "SteamUserUpdate",
)


class SteamUserUpdate(NamedTuple):
    """Payload for my custom `steam_user_update` event to mirror `Dota2Client.on_user_update`."""

    before: User
    after: User


class Dota2Client(Client):
    """Subclass for SteamIO's Client.

    Used to communicate with Dota 2 Game Coordinator in order to track information about my profile real-time.
    """

    def __init__(self, twitch_bot: IreBot) -> None:
        persona_state = PersonaState.Invisible if twitch_bot.test else PersonaState.Online
        super().__init__(state=persona_state)
        self.bot: IreBot = twitch_bot
        self.started: bool = False

        self.steam_web_api = SteamWebAPIClient()
        self.stratz = StratzClient()
        self.items = Items(twitch_bot)

    def irene(self) -> PartialUser:
        """Irene's Dota/Steam Profile (partial user)."""
        return self.create_partial_user(config["STEAM"]["IRENE_ID64"])

    async def start_helpers(self) -> None:
        """Start helping services for steam."""
        if not self.started:
            await self.steam_web_api.__aenter__()
            await self.stratz.__aenter__()
            self.items.start()

    @override
    async def login(self) -> None:
        await self.start_helpers()
        account_credentials = config["STEAM"]["IRENESTEST"] if self.bot.test else config["STEAM"]["IRENESBOT"]
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

    @override
    async def on_user_update(self, before: User, after: User) -> None:
        """Called when a steam user is updated, due to one or more of their attributes changing.

        The information from this event is redirected to `self.bot` events
        so we can process it in the bot components.
        """
        payload = SteamUserUpdate(before=before, after=after)
        self.bot.dispatch("steam_user_update", payload)
