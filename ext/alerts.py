from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import LueComponent
from utils import const, formats

if TYPE_CHECKING:
    import twitchio

    from bot import LueBot

log = logging.getLogger(__name__)


class Alerts(LueComponent):
    """Twitch Chat Alerts.

    Mostly, EventSub events that are nice to have a notification in twitch chat for.
    """

    def __init__(self, bot: LueBot) -> None:
        super().__init__(bot)
        self.ban_list: set[str] = set()

    # SECTION 1.
    # Channel Points beta test event (because it's the easiest event to test out)

    @commands.Component.listener(name="custom_redemption_add")
    async def channel_points_redeem(self, event: twitchio.ChannelPointsRedemptionAdd) -> None:
        """Somebody redeemed a custom channel points reward."""
        # just testing
        print(f"{event.user.display_name} redeemed {event.reward.title} (id={event.reward.id}).")  # noqa: T201

        if event.user.id == const.UserID.Aluerie and event.reward.cost < 4:
            # < 4 is a weird way to exclude my "Text-To-Speech" redemption.
            # channel = self.get_channel(payload.broadcaster)
            await event.broadcaster.send_message(
                sender=self.bot.bot_id,
                message=f"Thanks, I think bot is working {const.FFZ.PepoG}",
            )

    # SECTION 2
    # Actual events

    @commands.Component.listener(name="follow")
    async def follows(self, follow: twitchio.ChannelFollow) -> None:
        """Somebody followed the channel."""
        random_phrase = random.choice(
            [
                "welcome in",
                "I appreciate it",
                "enjoy your stay",
                "nice to see you",
                "enjoy the show",
            ]
        )
        random_emote = random.choice(
            [
                const.STV.donkHappy,
                const.BTTV.PogU,
                const.STV.dankHey,
                const.STV.donkHey,
                const.BTTV.peepoHey,
                const.STV.Hey,
            ]
        )
        await follow.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=f"@{follow.user.display_name} just followed! Thanks, {random_phrase} {random_emote}",
        )

    @commands.Component.listener(name="raid")
    async def raids(self, raid: twitchio.ChannelRaid) -> None:
        """Somebody raided the channel."""

        streamer = await raid.to_broadcaster.user()
        raider_channel_info = await raid.from_broadcaster.fetch_channel_info()

        await streamer.send_shoutout(
            to_broadcaster=raid.from_broadcaster.id, moderator=const.UserID.Bot, token_for=const.UserID.Bot
        )
        await streamer.send_announcement(
            moderator=const.UserID.Bot,
            token_for=const.UserID.Bot,
            message=(
                f"@{raid.from_broadcaster.display_name} just raided us! "
                f'They were playing {raider_channel_info.game_name} with title "{raider_channel_info.title}". '
                f"chat be nice to raiders {const.STV.donkHappy} raiders, feel free to raid and run tho."
            ),
        )

    @commands.Component.listener(name="stream_offline")
    async def stream_end(self, offline: twitchio.StreamOffline) -> None:
        """Stream ended (went offline)."""
        await offline.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=f"Stream is now offline {const.BTTV.Offline}",
        )

    @commands.Component.listener(name="stream_online")
    async def stream_start(self, online: twitchio.StreamOnline) -> None:
        """Stream started (went live)."""
        channel_info = await online.broadcaster.fetch_channel_info()
        await online.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=(
                f"Stream just started {const.STV.FeelsBingMan} "
                f"Game: {channel_info.game_name} | Title: {channel_info.title}"
            ),
        )
        await online.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=(f"{online.broadcaster.mention} remember to pin some message, check if everything is working."),
        )

    @commands.Component.listener(name="ad_break")
    async def ad_break(self, ad_begin: twitchio.ChannelAdBreakBegin) -> None:
        """Ad break."""
        # word = "automatic" if payload.is_automatic else "manual"
        human_delta = formats.timedelta_to_words(seconds=ad_begin.duration, fmt=formats.TimeDeltaFormat.Short)
        await ad_begin.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=f"{human_delta} ad starting {const.STV.peepoAds}",
        )

        # this is pointless probably
        # await asyncio.sleep(payload.duration)
        # await channel.send("TAd break is over")

    @commands.Component.listener(name="ban")
    async def bans_timeouts(self, ban: twitchio.Ban) -> None:
        """Bans."""
        if ban.user.name:
            self.ban_list.add(ban.user.name.lower())

    # @commands.Component.listener(name="message")
    # async def first_message(self, message: twitchio.ChatMessage) -> None:
    #     """Greet first time chatters with FirstTimeChadder treatment.

    #     This functions filters out spam-bots that should be perma-banned right away by other features or other bots.
    #     """
    #     if not message.first or not message.content:
    #         return

    #     await asyncio.sleep(3.3)
    #     if message.author.name.lower() not in self.ban_list:
    #         content = (
    #             f"{const.STV.FirstTimeChadder} or {const.STV.FirstTimeDentge} "
    #             f"\N{WHITE QUESTION MARK ORNAMENT} {const.STV.DankThink}"
    #         )
    #         await message.channel.send(content)


async def setup(bot: LueBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(Alerts(bot))
