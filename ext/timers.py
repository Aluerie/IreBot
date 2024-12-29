from __future__ import annotations

import asyncio
import itertools
import random
from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import LueComponent, lueloop
from utils import const

if TYPE_CHECKING:
    import twitchio

    from bot import LueBot


class Timers(LueComponent):
    """Periodic messages/announcements in Aluerie's channel."""

    def __init__(self, bot: LueBot) -> None:
        super().__init__(bot)

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
            # "Discord discord.gg/K8FuDeP",
            # "if you have nothing to do Sadge you can try !randompasta. Maybe you'll like it Okayge",
        ]
        self.lines_count: int = 0

    @commands.Component.listener(name="aluerie_online")
    async def stream_online_start_the_task(self) -> None:
        """Start the timer task when stream goes online."""
        if not self.timer_task.is_running():
            self.timer_task.start()

    @commands.Component.listener(name="aluerie_offline")
    async def stream_offline_cancel_the_task(self) -> None:
        """Cancel the timer task when stream goes offline."""
        self.timer_task.cancel()

    @commands.Component.listener(name="message")
    async def count_messages(self, message: twitchio.ChatMessage) -> None:
        """Count messages between timers so the bot doesn't spam fill up an empty chat."""
        if message.chatter.name in const.Bots:
            # do not count messages from known bot accounts
            return

        self.lines_count += 1

    @lueloop(count=1)
    async def timer_task(self) -> None:
        """Task to send periodic messages into irene's channel on timer."""
        await asyncio.sleep(10 * 60)
        messages = self.messages.copy()
        random.shuffle(messages)

        # refresh lines count so it only counts messages from the current stream.
        self.lines_count = 0
        for text in itertools.cycle(messages):
            while self.lines_count < 99:
                await asyncio.sleep(100)

            self.lines_count = 0
            await self.deliver(text)
            minutes_to_sleep = 69 + random.randint(1, 21)
            await asyncio.sleep(minutes_to_sleep * 60)

    @timer_task.before_loop
    async def timer_task_before_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: LueBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(Timers(bot))
