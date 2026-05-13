from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple, override

from steam import PersonaState
from steam.ext import dota2

from config import env

from .api_clients import OpenDotaClient, SteamWebAPIClient, StratzClient
from .storage import Items

if TYPE_CHECKING:
    from core import IreBot

log = logging.getLogger(__name__)

__all__ = ("Dota2Client", "SteamUserUpdate")


class SteamUserUpdate(NamedTuple):
    """Payload for my custom `steam_user_update` event to mirror `Dota2Client.on_user_update`."""

    before: dota2.User
    after: dota2.User


class Dota2Client(dota2.Client):
    """Subclass for SteamIO's Client.

    Used to communicate with Dota 2 Game Coordinator in order to track information about my profile real-time.
    """

    def __init__(self, twitch_bot: IreBot) -> None:
        persona_state = PersonaState.Online  # if not twitch_bot.test else PersonaState.Invisible
        super().__init__(state=persona_state)
        self.bot: IreBot = twitch_bot
        self.started: bool = False

        self.opendota = OpenDotaClient(session=self.bot.session)
        self.stratz = StratzClient(bearer_token=env.STRATZ_BEARER, session=self.bot.session)
        self.web_api = SteamWebAPIClient(api_key=env.STEAM_API_KEY, session=self.bot.session)

        self.items = Items(twitch_bot)

    async def start_helpers(self) -> None:
        """Start helping services for steam."""
        if not self.started:
            self.items.start()

    @override
    async def login(self) -> None:
        await self.start_helpers()
        if self.bot.test_subset_mode:
            username, password = env.STEAM_IRENESTEST_USERNAME, env.STEAM_IRENESTEST_PASSWORD
        else:
            username, password = env.STEAM_IRENESBOT_USERNAME, env.STEAM_IRENESBOT_PASSWORD
        await super().login(username, password)

    @override
    async def close(self) -> None:
        self.items.close()

    @override
    async def on_ready(self) -> None:
        log.info("Dota 2 Client: Ready %s, now waiting till Game Coordinator is ready;", self.user.name)
        await self.wait_until_gc_ready()
        log.info("Dota 2 Game Coordinator: Ready")

    @override
    async def on_user_update(self, before: dota2.User, after: dota2.User) -> None:
        """Called when a steam user is updated, due to one or more of their attributes changing.

        The information from this event is redirected to `self.bot` events
        so we can process it in the bot components' listeners.
        """
        payload = SteamUserUpdate(before=before, after=after)
        self.bot.dispatch("steam_user_update", payload)
