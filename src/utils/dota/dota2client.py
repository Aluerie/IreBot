from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple, override

from steam import PersonaState
from steam.ext.dota2 import Client

from config import config

from .opendota import OpenDotaClient
from .storage import Items
from .stratz import StratzClient
from .web_api import WebAPIClient

if TYPE_CHECKING:
    from steam.ext.dota2 import User

    from core import IreBot

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
        persona_state = PersonaState.Online  # if not twitch_bot.test else PersonaState.Invisible
        super().__init__(state=persona_state)
        self.bot: IreBot = twitch_bot
        self.started: bool = False

        self.opendota = OpenDotaClient(session=self.bot.session)
        self.stratz = StratzClient(bearer_token=config["TOKENS"]["STRATZ_BEARER"], session=self.bot.session)
        self.web_api = WebAPIClient(api_key=config["TOKENS"]["STEAM"], session=self.bot.session)

        self.items = Items(twitch_bot)

    async def start_helpers(self) -> None:
        """Start helping services for steam."""
        if not self.started:
            self.items.start()

    @override
    async def login(self) -> None:
        await self.start_helpers()
        account_credentials = config["STEAM"]["IRENESTEST"] if self.bot.test else config["STEAM"]["IRENESBOT"]
        username, password = account_credentials["USERNAME"], account_credentials["PASSWORD"]
        await super().login(username, password)

    @override
    async def close(self) -> None:
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
        so we can process it in the bot components' listeners.
        """
        payload = SteamUserUpdate(before=before, after=after)
        self.bot.dispatch("steam_user_update", payload)
