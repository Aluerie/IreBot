from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING, Any, override

from twitchio.ext import commands

from bot import IreComponent, ireloop
from utils import const, fmt

if TYPE_CHECKING:
    import twitchio

    from bot import IreBot

log = logging.getLogger(__name__)


class Alerts(IreComponent):
    """Twitch Chat Alerts.

    Mostly, EventSub events that are nice to have a notification in twitch chat for.
    """

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.ban_list: set[str] = set()
        self.known_chatters: list[str] = []

    @override
    async def component_load(self) -> None:
        self.fill_known_chatters.start()
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.fill_known_chatters.cancel()
        await super().component_teardown()

    # SECTION 1.
    # Channel Points beta test event (because it's the easiest event to test out)

    @commands.Component.listener(name="custom_redemption_add")
    async def channel_points_redeem(self, payload: twitchio.ChannelPointsRedemptionAdd) -> None:
        """Somebody redeemed a custom channel points reward."""
        # just testing
        print(f"{payload.user.display_name} redeemed {payload.reward.title} (id={payload.reward.id}).")  # noqa: T201

        if payload.user.id == const.UserID.Irene and payload.reward.cost < 4:
            # < 4 is a weird way to exclude my "Text-To-Speech" redemption.
            await payload.respond(f"Thanks, I think bot is working {const.FFZ.PepoG}")

    # SECTION 2
    # Actual events

    @commands.Component.listener(name="follow")
    async def follows(self, payload: twitchio.ChannelFollow) -> None:
        """Somebody followed the channel."""
        random_phrase = random.choice(
            [
                "welcome in",
                "I appreciate it",
                "enjoy your stay",
                "nice to see you",
                "enjoy the show",
            ],
        )
        random_emote = random.choice(
            [
                const.STV.donkHappy,
                const.BTTV.PogU,
                const.STV.dankHey,
                const.STV.donkHey,
                const.BTTV.peepoHey,
                const.STV.Hey,
            ],
        )
        await payload.respond(f"@{payload.user.display_name} just followed! Thanks, {random_phrase} {random_emote}")

    @commands.Component.listener(name="raid")
    async def raids(self, payload: twitchio.ChannelRaid) -> None:
        """Somebody raided the channel."""
        streamer = await payload.to_broadcaster.user()
        raider_channel_info = await payload.from_broadcaster.fetch_channel_info()

        await streamer.send_shoutout(to_broadcaster=payload.from_broadcaster.id, moderator=const.UserID.Bot)
        await streamer.send_announcement(
            moderator=const.UserID.Bot,
            message=(
                f"@{payload.from_broadcaster.display_name} just raided us! "
                f'They were playing {raider_channel_info.game_name} with title "{raider_channel_info.title}". '
                f"chat be nice to raiders {const.STV.donkHappy} raiders, feel free to raid and run tho."
            ),
        )

    @commands.Component.listener(name="stream_online")
    async def stream_start(self, payload: twitchio.StreamOnline) -> None:
        """Stream started (went live)."""
        channel_info = await payload.broadcaster.fetch_channel_info()
        # notification
        await payload.respond(
            f"Stream just started {const.STV.FeelsBingMan} Game: {channel_info.game_name} | Title: {channel_info.title}"
        )
        # reminder for the streamer
        await payload.respond(
            f"{payload.broadcaster.mention} a few reminders {const.STV.ALERT} "
            f"pin some info {const.STV.ALERT} "
            f"start recording {const.STV.ALERT} "
            f"Turn music on {const.STV.ALERT}"
        )
        await asyncio.sleep(10 * 60)  # 10 minutes
        # extra reminder for the streamer
        await payload.respond(
            f"Irene {const.STV.ALERT} "
            f"last reminder {const.STV.ALERT} "
            f"start recording please {const.STV.ALERT} "
            f'chat spam " {const.STV.ALERT} "'
        )

        # TODO: Maybe rework this into timers-like we have in the Discord bot;
        # YouTube only allows 12 hours of vods so let's warn ourselves just in case.
        youtube_vod_limit = 11 * 3600 + 40 * 60  # 11 hours 40 minutes + 10 minute of `asyncio.sleep` above
        await asyncio.sleep(youtube_vod_limit)
        if self.bot.irene.online:
            await payload.respond(
                f"Irene {const.STV.ALERT} "
                f"you've been streaming for almost 12h {const.STV.ALERT} "
                f"remember youtube vod time limit {const.STV.ALERT} "
                f"{const.STV.OVERWORKING} wrap it up {const.STV.ALERT} "
            )

    @commands.Component.listener(name="stream_offline")
    async def stream_end(self, payload: twitchio.StreamOffline) -> None:
        """Stream ended (went offline)."""
        await payload.respond(f"Stream is now offline {const.BTTV.Offline}")

    @commands.Component.listener(name="ad_break")
    async def ad_break(self, payload: twitchio.ChannelAdBreakBegin) -> None:
        """Ad break."""
        word = "automatic" if payload.automatic else "manual"
        human_delta = fmt.timedelta_to_words(seconds=payload.duration, fmt=fmt.TimeDeltaFormat.Short)
        await payload.respond(f"{human_delta} {word} ad starting {const.STV.peepoAds}")

        # this is pointless probably
        # await asyncio.sleep(payload.duration)
        # await channel.send("Ad break is over")

    @commands.Component.listener(name="ban")
    async def bans_timeouts(self, payload: twitchio.Ban) -> None:
        """Bans."""
        self.ban_list.add(payload.user.id)

    @ireloop(count=1)
    async def fill_known_chatters(self) -> None:
        """The task that ensures the reward "First" under a specific id exists.

        Just a fool proof measure in case I randomly snap and delete it.
        """
        query = "SELECT user_id FROM ttv_chatters"
        self.known_chatters: list[str] = [r for (r,) in await self.bot.pool.fetch(query)]

    @commands.Component.listener(name="message")
    async def first_message(self, payload: twitchio.ChatMessage) -> None:
        """Greet first time chatters with FirstTimeChadder treatment.

        This functions filters out spam-bots that should be perma-banned right away by other features or other bots.
        """
        # todo: change this when twitch adds it to event sub
        if not payload.text:
            return

        if payload.chatter.id in self.known_chatters:
            # if in database: a known chatter
            return

        await asyncio.sleep(4.0)  # wait for auto-mod / WizeBot to ban super-sus users - 4 sec is probably enough.
        if payload.chatter.id in self.ban_list:
            await payload.respond(const.STV.LastTimeChatter)
            return

        query = "INSERT INTO ttv_chatters (user_id, name_lower) VALUES ($1, $2)"
        await self.bot.pool.execute(query, payload.chatter.id, payload.chatter.name)
        self.known_chatters.append(payload.chatter.id)

        await payload.respond(
            f"{const.STV.FirstTimeChadder} or {const.STV.FirstTimeDentge} "
            f"\N{WHITE QUESTION MARK ORNAMENT} {const.STV.DankThink}"
        )

    @commands.Component.listener(name="subscription")
    async def subscription(self, payload: twitchio.ChannelSubscribe) -> None:
        """Subscriptions."""
        await payload.respond(f"{payload.user.mention} just subscribed {const.STV.Donki} thanks")

    @commands.Component.listener(name="subscription_message")
    async def subscription_message(self, payload: twitchio.ChannelSubscriptionMessage) -> None:
        """Subscriptions."""
        await payload.respond(
            f"{payload.user.mention} just subscribed for {fmt.ordinal(payload.months)} months "
            f"{const.STV.Donki} thanks a lot"
        )


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Alerts(bot))
