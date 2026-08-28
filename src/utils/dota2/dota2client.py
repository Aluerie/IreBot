from __future__ import annotations

import datetime
import logging
import re
from typing import TYPE_CHECKING, Any, NamedTuple, override

from steam import PersonaState
from steam.ext import dota2

from config import env
from core import ireloop
from utils import errors

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

    async def start_helpers(self) -> None:
        """Start helping services for steam."""
        if not self.started:
            self.refresh_database_dota_constants.start()
            self.started = True

    @override
    async def login(self, *args: Any, **kwargs: Any) -> None:
        await self.start_helpers()
        if self.bot.test_subset_mode:
            username, password = env.STEAM_IRENESTEST_USERNAME, env.STEAM_IRENESTEST_PASSWORD
        else:
            username, password = env.STEAM_IRENESBOT_USERNAME, env.STEAM_IRENESBOT_PASSWORD
        await super().login(username, password, *args, **kwargs)

    @override
    async def close(self) -> None:
        self.refresh_database_dota_constants.stop()

    @override
    async def on_ready(self) -> None:
        log.info("🍋 Dota 2 Client: Ready %s, now waiting till Game Coordinator is ready;", self.user.name)
        await self.wait_until_gc_ready()
        log.info("🍋 Dota 2 Game Coordinator: Ready")

    @override
    async def on_user_update(self, before: dota2.User, after: dota2.User) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Called when a steam user is updated, due to one or more of their attributes changing.

        The information from this event is redirected to `self.bot` events
        so we can process it in the bot components' listeners.
        """
        payload = SteamUserUpdate(before=before, after=after)
        self.bot.dispatch("steam_user_update", payload)

    # DATABASE DOTA CONSTANTS

    async def upsert_constants_items(self, to_insert: list[tuple[int, str]], service_name: str) -> None:
        """Upsert data into `dota_constants_items` table."""
        query = """
            INSERT INTO dota_constants_items
            (item_id, display_name)
            VALUES ($1, $2)
            ON CONFLICT (item_id)
                DO UPDATE SET display_name = $2;
        """
        await self.bot.pool.executemany(query, to_insert)
        log.debug("🍋 Database Dota Constants: Updated items with %s API", service_name)

    @ireloop(count=1)  # , time=datetime.time(hour=6, minute=44))
    async def refresh_database_dota_constants(self) -> None:
        """Daily Refresh Database's Dota Constants.

        Notes
        -----
        * IreBot currently only utilizes `dota_constants_items` table.
        * This task first tries to update stuff with Stratz API, if not successful then fallback to OpenDota.
        """
        log.debug("🍋 Database Dota Constants: Daily Refresh is starting")

        # Stratz
        try:
            items = await self.stratz.get_items()
        except errors.APIDataError as err:
            log.warning("🍋 Stratz API error: `get_items`", exc_info=err)
            # Then we should try with OpenDota
        else:
            await self.upsert_constants_items(
                # Sometimes Stratz return `None` for item display names.
                # Also they put '\x00' into their responses which is not supported by PostgresQL
                to_insert=[(item["id"], item["displayName"].replace('\x00','') or "") for item in items],
                service_name="Stratz",
            )
            return

        # Opendota
        try:
            items = await self.opendota.get_items()
        except errors.APIDataError as err:
            log.warning("🍋 Opendota API error: `get_items`", exc_info=err)
            # Then we are cooked ?
        else:
            await self.upsert_constants_items(
                # Some Opendota items are missing `dname` field.
                to_insert=[(item["id"], item.get("dname", "")) for _key, item in items.items()],
                service_name="Opendota",
            )
            return

        msg = "Something went wrong with `refresh_database_dota_constants`."
        raise errors.PlaceholderError(msg)
