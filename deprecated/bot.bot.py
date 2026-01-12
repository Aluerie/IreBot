from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, override

from twitchio.ext import commands

from bot import ireloop

if TYPE_CHECKING:
    import twitchio


class Irene:
    """
    Class describing the streamer (Irene) utilizing IreBot.

    This class meant to provide some utilities and shortcuts to often used TwitchIO features.
    """

    def __init__(self, user_id: str | None, bot: IreBot) -> None:
        if not user_id:
            msg = "Provided `user_id` must be a string."
            raise TypeError(msg)

        self.id: str = user_id
        self.bot: IreBot = bot

        # a variable tracking Irene's online status; helps on saving some API calls.
        self.online: bool = False

    async def stream(self) -> twitchio.Stream | None:
        """Shortcut to get @Irene's stream."""
        return next(iter(await self.bot.fetch_streams(user_ids=[self.id])), None)

    def partial(self) -> twitchio.PartialUser:
        """Get Irene's channel from the cache."""
        return self.bot.create_partialuser(self.id)

    async def deliver(self, content: str) -> None:
        """A shortcut to send a message in Irene's twitch channel."""
        await self.partial().send_message(sender=self.bot.bot_id, message=content)


class IreBot(commands.AutoBot):
    """XD."""

    @override
    async def setup_hook(self) -> None:
        self.irene = Irene("69", self)
        self.check_if_online.start()

    # Irene's class related events
    @ireloop(count=1)
    async def check_if_online(self) -> None:
        """Check if Irene is online - used to make my own (proper) online event instead of twitchio's."""
        await asyncio.sleep(1.0)  # just in case;
        if await self.irene.stream():
            self.online = True
            self.dispatch("irene_online")

    async def event_stream_online(self, _: twitchio.StreamOnline) -> None:
        """Instead of the twitchio event - dispatch my own online event.

        The difference is that my event accounts for the state of my stream when the bot restarts.
        """
        self.irene.online = True
        self.dispatch("irene_online")

    async def event_stream_offline(self, _: twitchio.StreamOffline) -> None:
        """Instead of the twitchio event - dispatch my own offline event."""
        self.irene.online = False
        self.dispatch("irene_offline")

    # def show_oauth(self) -> None:
    #     oauth = twitchio.authentication.OAuth(
    #         client_id=config.TTV_DEV_CLIENT_ID,
    #         client_secret=config.TTV_DEV_CLIENT_SECRET,
    #         redirect_uri="http://localhost:4343/oauth/callback",
    #         scopes=twitchio.Scopes(
    #             [
    #                 "channel:bot",
    #                 "channel:read:ads",
    #                 "channel:moderate",
    #                 "moderator:read:followers",
    #                 "channel:read:redemptions",
    #             ]
    #         ),
    #     )
    #     #
    #     #  # Generate the authorization URL
    #     auth_url = oauth.get_authorization_url(force_verify=True)
    #     print(auth_url)  # noa: T201
