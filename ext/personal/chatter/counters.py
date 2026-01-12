from __future__ import annotations

import asyncio
import datetime
import random
import re
from typing import TYPE_CHECKING, Any, TypedDict, override

from discord import Embed
from twitchio.ext import commands

from bot import IrePersonalComponent, ireloop
from utils import const, fmt

if TYPE_CHECKING:
    import twitchio

    from bot import IreBot, IreContext

    class FirstRedeemsRow(TypedDict):
        """`first_redeems` Table Columns."""

        user_name: str
        first_times: int


FIRST_ID: str = "902e931b-3d09-4a2e-9996-1d1ad599761d"


class Counters(IrePersonalComponent):
    """Track some silly number counters of how many times this or that happened."""

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.last_erm_notification: datetime.datetime = datetime.datetime.now(datetime.UTC)

    @override
    async def component_load(self) -> None:
        self.check_first_reward.start()
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.check_first_reward.cancel()
        await super().component_teardown()

    @commands.is_owner()
    @commands.group()
    async def counter(self, ctx: IreContext) -> None:
        """Group command for !counter commands."""
        # TODO: I guess, we need to implement "send_help"
        await ctx.send("Use this command together with subcommands delete/create/change")

    @counter.command()
    async def create(self, ctx: IreContext, name: str) -> None:
        """Create a counter."""
        query = """
            INSERT INTO ttv_counters
            (name, value)
            VALUES ($1, $2)
            ON CONFLICT (name)
                DO NOTHING
            RETURNING value;
        """
        value: int | None = await self.bot.pool.fetchval(query, name, 0)
        if value is None:
            await ctx.send(f"Such counter already exists! {const.STV.POLICE}")
        else:
            await ctx.send(f"Created a counter `{name}` (current value = {value}) {const.STV.science}")

    # TODO: counter set (change)/increment (add) / remove commands ; maybe do it smarter like !deaths and it understands

    # ERM COUNTERS

    @commands.Component.listener(name="message")
    async def erm_counter(self, message: twitchio.ChatMessage) -> None:
        """Erm Counter."""
        if not self.is_owner(message.broadcaster.id):
            return
        if message.chatter.name in const.Bots or not message.text:
            return
        if not re.search(r"\bErm\b", message.text):
            return

        query = """--sql
            UPDATE ttv_counters
            SET value = value + 1
            where name = $1
            RETURNING value;
        """
        value: int = await self.bot.pool.fetchval(query, "erm")

        # milestone
        if value % 1000 == 0:
            await message.respond(f"{const.STV.wow} we reached a milestone of {value} {const.STV.Erm} in chat")
            return

        # random notification/reminder
        now = datetime.datetime.now(datetime.UTC)
        if random.randint(0, 150) < 2 and (now - self.last_erm_notification).seconds > 180:
            await asyncio.sleep(3)
            query = "SELECT value FROM ttv_counters WHERE name = $1"
            value: int = await self.bot.pool.fetchval(query, "erm")
            await message.respond(f"{value} {const.STV.Erm} in chat.")
            return

    @commands.command(aliases=["erm"])
    async def erms(self, ctx: IreContext) -> None:
        """Get an erm_counter value."""
        query = "SELECT value FROM ttv_counters WHERE name = $1"
        value: int = await self.bot.pool.fetchval(query, "erm")
        await ctx.send(f"{value} {const.STV.Erm} in chat.")

    # FIRST COUNTER

    @commands.Component.listener(name="custom_redemption_add")
    async def first_counter(self, redemption: twitchio.ChannelPointsRedemptionAdd) -> None:
        """Count all redeems for the reward 'First'."""
        if not self.is_owner(redemption.broadcaster.id):
            return

        if redemption.reward.id != FIRST_ID:
            return

        query = """--sql
            INSERT INTO ttv_first_redeems (user_id, user_name)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO
                UPDATE SET first_times = ttv_first_redeems.first_times + 1, user_name = $2
            RETURNING first_times;
        """
        count: int = await self.bot.pool.fetchval(query, redemption.user.id, str(redemption.user.name))

        if count == 1:
            msg = f'@{redemption.user.display_name}, gratz on your very first "First!" {const.STV.gg}'
        else:
            msg = f"@{redemption.user.display_name}, Gratz! you've been first {count} times {const.STV.gg} {const.Global.EZ}"

        await redemption.respond(msg)

        reward = await redemption.reward.fetch_reward()
        await reward.update(title=f"@{redemption.user.display_name} was 1st today !")

    @commands.Component.listener(name="stream_offline")
    async def reset_first_redeem_title(self, offline: twitchio.StreamOffline) -> None:
        """Reset the title of the "First!" redeem back to its original state.

        Currently, it should be changed when somebody redeems to "@user was first!
        """
        if not self.is_owner(offline.broadcaster.id):
            return

        first_reward = next(reward for reward in await offline.broadcaster.fetch_custom_rewards() if reward.id == FIRST_ID)
        await first_reward.update(title="First !")

    @commands.command(aliases=["first"])
    async def firsts(self, ctx: IreContext) -> None:
        """Get top10 first redeemers."""
        query = """--sql
            SELECT user_name, first_times
            FROM ttv_first_redeems
            ORDER BY first_times DESC
            LIMIT 3;
        """
        rows: list[FirstRedeemsRow] = await self.bot.pool.fetch(query)
        content = f'Top3 "First!" redeemers {const.BTTV.DankG} '

        rank_medals = [
            "\N{FIRST PLACE MEDAL}",
            "\N{SECOND PLACE MEDAL}",
            "\N{THIRD PLACE MEDAL}",
        ]  # + const.DIGITS[4:10]
        content += " ".join(
            [f"{rank_medals[i]} {row['user_name']}: {fmt.plural(row['first_times']):time};" for i, row in enumerate(rows)],
        )
        await ctx.send(content)

    @commands.command()
    async def test_digits(self, ctx: IreContext) -> None:
        """Test digit emotes in twitch chat.

        At the point of writing this function - the number emotes like :one: were not working
        in twitch chat powered with FFZ/7TV addons.
        So use it to check if it's fixed. if yes - then we can rewrite some functions to use these emotes.
        """
        content = " ".join(const.DIGITS)
        await ctx.send(content)

    @ireloop(time=[datetime.time(hour=3, minute=59)])
    async def check_first_reward(self) -> None:
        """The task that ensures the reward "First" under a specific id exists.

        Just a fool proof measure in case I randomly snap and delete it.
        """
        if datetime.datetime.now(datetime.UTC).day != 14:
            # simple way to make a task run once/month
            return

        custom_rewards = await self.bot.create_partialuser(const.UserID.Irene).fetch_custom_rewards()
        for reward in custom_rewards:
            if reward.id == FIRST_ID:
                # we good
                if reward.title != "First !":
                    # wrong title somehow
                    await reward.update()
                break
        else:
            # we bad
            content = self.bot.error_ping
            embed = Embed(
                description='Looks like you deleted "First!" channel points reward from the channel.',
                colour=0x345245,
            ).set_footer(text="WTF, bring it back!")
            await self.bot.error_webhook.send(content=content, embed=embed)


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Counters(bot))
