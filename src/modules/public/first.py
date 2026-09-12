"""
First feature.

Manages the channel point reward (usually called "First!") which only one chatter (the very first one) can redeem.

License
-------
* This Source Code Form is subject to the terms of the [Mozilla Public License v2.0](<http://mozilla.org/MPL/2.0/>).
* Copyright (C) 2020-present [@Aluerie](<https://github.com/Aluerie>).
"""

from __future__ import annotations

import contextlib
import datetime
from typing import TYPE_CHECKING, TypedDict, override

import twitchio
from discord import Embed
from twitchio.ext import commands

from core import IrePublicComponent, ireloop
from shared import common_const, errors, fmt
from utils import const, guards

if TYPE_CHECKING:
    from core import IreBot, IreContext

    class FirstRedeemsRow(TypedDict):
        user_id: str
        first_times: int

    class FirstChatterRewardsQuery(TypedDict):
        streamer_id: str
        reward_id: str
        original_title: str


__all__ = ("FirstChatterChannelRewardManagement",)

# FIRST_ID: str = "902e931b-3d09-4a2e-9996-1d1ad599761d"

DEFAULT_FIRST_REWARD_TITLE = "First!"


class FirstChatterChannelRewardManagement(IrePublicComponent):
    """Track some silly number counters of how many times this or that happened."""

    @override
    async def component_load(self) -> None:
        self.double_check_offline.start()
        self.check_first_reward.start()
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.double_check_offline.cancel()
        self.check_first_reward.cancel()
        await super().component_teardown()

    @guards.is_broadcaster_or_dev()
    @commands.command()
    async def setup_first_reward(self, ctx: IreContext) -> None:
        """Setup First Chatter Channel Reward in the broadcaster channel."""
        custom_reward = await ctx.broadcaster.create_custom_reward(
            title="First!",
            cost=1,
            max_per_stream=1,
            max_per_user=1,
            redemptions_skip_queue=True,
        )
        query = """
            INSERT INTO ttv_first_chatter_rewards
            (streamer_id, reward_id)
            VALUES ($1, $2)
        """
        await self.bot.pool.execute(query, ctx.broadcaster.id, custom_reward.id)
        await ctx.send(
            "Successfully created channel reward 'First'! If you want to edit it (e.g. text or color) - "
            "visit your creator dashboard "
            f"(dashboard.twitch.tv/u/{ctx.broadcaster.name}/viewer-rewards/channel-points/rewards)"
        )

    @commands.Component.listener(name="event_custom_reward_update")
    async def update_reward_title_in_database(self, reward_update: twitchio.ChannelPointsRewardUpdate) -> None:
        """Update reward title in the database."""
        query = """
            UPDATE ttv_first_chatter_rewards
            SET original_title = $1
            WHERE reward_id = $2
        """
        await self.bot.pool.execute(query, reward_update.title, reward_update.id)

    @commands.Component.listener(name="custom_redemption_add")
    async def first_counter(self, redemption: twitchio.ChannelPointsRedemptionAdd) -> None:
        """Process First Chatter Channel Point redeem.

        * Count all redeems for the reward 'First'.
        * Responds to the user.
        """
        query = """--sql
            SELECT COUNT(1)
            FROM ttv_first_chatter_rewards
            WHERE reward_id = $1
        """
        if await self.bot.pool.fetchval(query, redemption.reward.id) == 0:
            return

        query = """--sql
            INSERT INTO ttv_first_chatter_redeems
            (user_id, streamer_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, streamer_id) DO
                UPDATE SET first_times = ttv_first_chatter_redeems.first_times + 1
            RETURNING first_times;
        """
        count: int = await self.bot.pool.fetchval(query, redemption.user.id, redemption.broadcaster.id)
        msg = (
            f'@{redemption.user.display_name}, gratz on your very first "First!" {const.STV.gg}'
            if count == 1
            else f"@{redemption.user.display_name}, Gratz! you've been first {count} times {const.STV.gg} {const.Global.EZ}"
        )
        await redemption.respond(msg)
        with contextlib.suppress(twitchio.HTTPException):
            await redemption.fulfill(token_for=redemption.broadcaster.id)
        reward = await redemption.reward.fetch_reward()
        await reward.update(title=f"@{redemption.user.display_name} was 1st today !")

    async def helper_reset_redeem_title_to_original(
        self, broadcaster: twitchio.PartialUser, reward_id: str, original_title: str
    ) -> None:
        """Helper function to reset First Chatter Reward title's to normal.

        Title gets replaces by "@User was first today!" during the streams.
        This replaces it back to the original.
        """
        first_reward = next(iter(await broadcaster.fetch_custom_rewards(ids=[reward_id])))
        await first_reward.update(title=original_title or DEFAULT_FIRST_REWARD_TITLE)

    @commands.Component.listener(name="stream_offline")
    async def reset_first_redeem_title(self, offline: twitchio.StreamOffline) -> None:
        """Reset the title of the "First!" redeem back to its original state.

        Currently, it should be changed when somebody redeems to "@user was first!
        """
        query = """
            SELECT original_title, reward_id
            FROM ttv_first_chatter_rewards
            WHERE streamer_id = $1;
        """
        if row := await self.bot.pool.fetchrow(query, offline.broadcaster.id):
            await self.helper_reset_redeem_title_to_original(
                offline.broadcaster,
                row["reward_id"],
                row["original_title"],
            )

    @ireloop(hours=6)
    async def double_check_offline(self) -> None:
        """Double Check if the stream is online.

        Sometimes, the bot is offline during streamer stream ends so it doesn't catch the `stream_offline` event.
        """
        await self.bot.streamers_index_ready.wait()
        query = """
            SELECT streamer_id, reward_id, original_title
            FROM ttv_first_chatter_rewards;
        """
        rows: list[FirstChatterRewardsQuery] = await self.bot.pool.fetch(query)
        for row in rows:
            streamer = self.bot.streamers.get(row["streamer_id"])
            if streamer is None or not streamer.online:
                continue
            await self.helper_reset_redeem_title_to_original(
                self.bot.create_partialuser(row["streamer_id"]),
                row["reward_id"],
                row["original_title"],
            )

    @commands.command(aliases=["first"])
    async def firsts(self, ctx: IreContext) -> None:
        """Get top5 first redeemers."""
        query = """--sql
            SELECT user_id, first_times
            FROM ttv_first_chatter_redeems
            WHERE streamer_id = $1
            ORDER BY first_times DESC
            LIMIT 5;
        """
        rows: list[FirstRedeemsRow] = await self.bot.pool.fetch(query, ctx.broadcaster.id)
        if not rows:
            msg = "This channel doesn't have `First!` feature setup."
            raise errors.RespondWithError(msg)

        content = f'Top5 "First!" redeemers {const.BTTV.DankG} '
        rank_medals = [
            "\N{FIRST PLACE MEDAL}",
            "\N{SECOND PLACE MEDAL}",
            "\N{THIRD PLACE MEDAL}",
            common_const.DIGITS[4],
            common_const.DIGITS[5],
        ]
        content += " ".join(
            [
                f"{rank_medals[i]} {(await self.bot.create_partialuser(row['user_id']).user()).display_name}: "
                f"{fmt.plural(number=row['first_times']):time};"
                for i, row in enumerate(rows)
            ]
        )
        await ctx.send(content)

    @ireloop(time=[datetime.time(hour=3, minute=59)])
    async def check_first_reward(self) -> None:
        """The task that ensures the reward "First" under a specific id exists.

        Just a fool proof measure in case I randomly snap and delete it.
        """
        if datetime.datetime.now(datetime.UTC).day != 14:
            # simple way to make a task run once/month
            return

        query = """
            SELECT streamer_id, reward_id, original_title
            FROM ttv_first_chatter_rewards;
        """
        rows: list[FirstChatterRewardsQuery] = await self.bot.pool.fetch(query)

        for row in rows:
            partial_user = self.bot.create_partialuser(row["streamer_id"])
            first_reward = next(iter(await partial_user.fetch_custom_rewards(ids=[row["reward_id"]])))
            if not first_reward:
                content = self.bot.error_ping
                embed = Embed(
                    description=(
                        f"Looks like something wrong with streamer @{partial_user.name} ({row['streamer_id']}) "
                        'deleted "First!" channel points reward from the channel.'
                    ),
                    colour=0x345245,
                )
                await self.bot.error_webhook.send(content=content, embed=embed)


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(FirstChatterChannelRewardManagement(bot))
