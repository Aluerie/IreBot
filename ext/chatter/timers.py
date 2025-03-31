from __future__ import annotations

import asyncio
import datetime
import random
from typing import TYPE_CHECKING, Any

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    import twitchio

    from bot import IreBot


class Timers(IreComponent):
    """Periodic messages/announcements in Aluerie's channel."""

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

        self.lines_count: int = 0
        self.index: int = 0
        self.cooldown: datetime.timedelta = datetime.timedelta(hours=1)
        self._most_recent: datetime.datetime | None = None
        self._lock: asyncio.Lock = asyncio.Lock()

        self.messages: list[str] = [
            f"FIX YOUR POSTURE {const.BTTV.weirdChamp}",
            (
                f"{const.STV.heyinoticedyouhaveaprimegamingbadgenexttoyourname} Use your Twitch Prime to sub for "
                f"my channel {const.STV.DonkPrime} it's completely free {const.BTTV.PogU}"
            ),
            f"{const.STV.Adge} {const.STV.DankApprove}",
            f"Don't forget to stretch and scoot {const.STV.GroupScoots}",
            f"{const.STV.plink}",
            f"{const.STV.uuh}",
            f"chat don't forget to {const.STV.plink}",
            (
                "hi chat many features of this bot are WIP so, please, if you notice bugs or incorrect responses "
                f"- inform me {const.STV.DANKHACKERMANS}"
            ),
            (
                "hey chat I'm making a small web-page to describe the bot's features (WIP)."
                "You can see it here: (not implemented xdd)"  # TODO: add the web page
            ),
            # "Discord discord.gg/K8FuDeP",
            # "if you have nothing to do Sadge you can try !randompasta. Maybe you'll like it Okayge",
        ]

    @commands.Component.listener(name="irene_online")
    async def stream_online_start_the_task(self) -> None:
        """Start counting messages when stream goes online."""
        random.shuffle(self.messages)
        self.index = 0
        self.bot.add_listener(self.count_messages, event="event_message")

    @commands.Component.listener(name="irene_offline")
    async def stream_offline_cancel_the_task(self) -> None:
        """Cancel the counting messages listener when stream goes offline."""
        self.bot.remove_listener(self.count_messages)

    # @commands.Component.listener(name="message")
    async def count_messages(self, message: twitchio.ChatMessage) -> None:
        """The listener responsible for sending timer-messages.

        Timer messages are sent if the following conditions are met
        * there were X amount of messages in the chat between bot timer-messages
        * Y time passed between those.

        If these two are fulfilled then the bot sends a semi-periodic message in the chat.
        """
        if message.chatter.name in const.Bots:
            # do not count messages from known bot accounts
            return

        self.lines_count += 1
        async with self._lock:
            if self._most_recent and (datetime.datetime.now(datetime.UTC) - self._most_recent) < self.cooldown:
                # we already have a timer to send
                return

            if self.lines_count > 99:
                await asyncio.sleep(30 + random.randint(1, 5 * 60))
                await self.deliver(self.messages[self.index % len(self.messages)])

                # reset the index vars
                self.index += 1
                self.lines_count = 0
                self._most_recent = datetime.datetime.now(datetime.UTC)

    @commands.Component.listener(name="irene_online")
    async def periodic_announcements(self) -> None:
        """Send periodic announcements into irene's channel on timer."""
        # lazy implementation
        await asyncio.sleep(7200 + 60 * random.randint(0, 240))  # 2 hours + random(0, 4 hours)
        if not self.bot.irene_online:
            return

        await self.irene.send_announcement(
            moderator=const.UserID.Bot,
            message=(
                "hey chat soon I will need to grind an affiliate on @IrenesBot account. "
                f"{const.STV.please} Any follows and lurks for that account are appreciated. {const.STV.Erm} "
                f"Feel free to {const.STV.catFU} though."
            ),
        )


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Timers(bot))
