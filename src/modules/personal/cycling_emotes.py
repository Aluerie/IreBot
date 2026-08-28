"""
_Insert Module Docstring Here._

License
-------
* This Source Code Form is subject to the terms of the [Mozilla Public License v2.0](<http://mozilla.org/MPL/2.0/>).
* Copyright (C) 2020-present [Aluerie](<https://github.com/Aluerie>).
"""

from __future__ import annotations

import contextlib
import logging
import re
from typing import TYPE_CHECKING, Annotated, Any, override

from twitchio.ext import commands

from core import IrePersonalComponent, ireloop
from utils import const, errors, guards, seven_tv

if TYPE_CHECKING:
    import twitchio

    from core import IreBot, IreContext


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def to_emote_id(user_input: str) -> str:
    """A function to convert a 7TV emote link to an emote_id.

    Does not do anything if the user input is already an emote_id.
    If no emote_id is provided then it errors out.
    """
    search = re.search(
        r"(?:https?:\/\/(?:www\.)?7tv\.app\/emotes\/)?(?P<emote_id>[0-7][0-9A-HJKMNP-TV-Z]{25})",
        user_input,
    )
    if search is None:
        msg = f"Bad emote id, make sure you made no mistakes {const.FFZ.peepoPolice}"
        raise errors.BadUserInputError(msg)
    return search["emote_id"]


class SevenTVEmoteConverter(commands.Converter[str]):
    @override
    async def convert(self, ctx: IreContext, user_input: str) -> str:
        """Convert `user_input` to 7TV emote_id."""
        # Step 1. Check if it's emote link / emote_id
        try:
            return to_emote_id(user_input)
        except errors.BadUserInputError:
            pass

        # Step 2. Try to find the said emote with 7TV Graph QL
        return await ctx.bot.stv.user_search_emote_name(broadcaster_id=ctx.broadcaster.id, emote_name=user_input)


class CyclingEmotes(IrePersonalComponent):
    """Cycling Emotes."""

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.reward_ids_cache: set[str] = set()

    @override
    async def component_load(self) -> None:
        self.fill_known_rewards.start()
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.fill_known_rewards.cancel()
        await super().component_teardown()

    @ireloop(count=1)
    async def fill_known_rewards(self) -> None:
        """The task that fills a set of rewards ids for convenience to cut on a few database queries."""
        query = "SELECT reward_id FROM ttv_cycling_emote_rewards"
        self.reward_ids_cache = {r for (r,) in await self.bot.pool.fetch(query)}

    @guards.is_owner_channel()
    @commands.is_owner()
    @commands.command()
    async def create_7tv_cycling_emote_reward(self, ctx: IreContext) -> None:
        custom_reward = await ctx.broadcaster.create_custom_reward(
            title="Add a 7TV emote (10 slots, oldest cycles out)",
            cost=10,
            prompt=(
                "Give me a 7TV emote link or emote ID. "
                "If you want an alias name for the emote then provide it after a space. "
                'Example: "https://7tv.app/emotes/01FP8TR8G8000EJT2EVEY3JQTF smh"'
            ),
        )

        query = """
            INSERT INTO ttv_cycling_emote_rewards
            (streamer_id, reward_id, emote_limit)
            VALUES ($1, $2, $3)
        """
        await self.bot.pool.execute(query, ctx.broadcaster.id, custom_reward.id, 10)
        self.reward_ids_cache.add(custom_reward.id)
        await ctx.send(f"Created a cycling 7tv emote channel points reward {const.STV.DankApprove}")

    @commands.Component.listener(name="custom_redemption_add")
    async def channel_points_redeem(self, redemption: twitchio.ChannelPointsRedemptionAdd) -> None:
        """Somebody redeemed a custom channel points reward."""
        if redemption.reward.id not in self.reward_ids_cache:
            return

        log.debug(
            "🖍️ - User @%s (%s) requested cycling emote at broadcaster @%s (%s)",
            redemption.user.display_name,
            redemption.user.id,
            redemption.broadcaster.display_name,
            redemption.broadcaster.id,
        )

        # Step 1. Parse User Input
        split = redemption.user_input.split()

        if len(split) > 2:
            await redemption.refund(token_for=redemption.broadcaster.id)

            msg = 'Bad User Input, it\'s supposed to be an "*emote_link/id* *emote_alias* - no extra words"'
            raise errors.BadUserInputError(msg)

        try:
            emote_id = to_emote_id(split[0])
        except errors.BadUserInputError:
            await redemption.refund(token_for=redemption.broadcaster.id)
            raise

        emote_alias = ""
        with contextlib.suppress(IndexError):
            # If emote alias was given - assign it.
            emote_alias = split[1]

        log.debug("🖍️ - emote_id = %s emote_alias = %s", emote_id, emote_alias)

        # Step 2. Get Emote Set
        emote_set_id = await self.bot.stv.active_emote_set_by_broadcaster(broadcaster_id=redemption.broadcaster.id)
        log.debug("🖍️ - Operating on emote_set #%s", emote_set_id)

        # Step 3. Remove emote(-s) if above the limit
        query = """
            DELETE FROM ttv_cycling_emotes tce
            WHERE tce.emote_id IN (
                SELECT tce2.emote_id
                FROM ttv_cycling_emotes tce2
                WHERE tce2.streamer_id = $1
                    AND tce2.emote_set_id = $2
                ORDER BY tce2.added_at DESC
                OFFSET (
                    SELECT tcer.emote_limit - 1
                    FROM ttv_cycling_emote_rewards tcer
                    WHERE tcer.streamer_id = $1
                )
            )
            RETURNING tce.emote_id;
        """
        emote_ids_to_remove: list[str] = [
            r for (r,) in await self.bot.pool.fetch(query, redemption.broadcaster.id, emote_set_id)
        ]
        log.debug("🖍️ - Removing emotes #%s", emote_ids_to_remove)

        for emote_id_to_delete in emote_ids_to_remove:
            with contextlib.suppress(seven_tv.EmoteNotFoundInSetError):
                await self.bot.stv.emote_set_remove_emote(
                    emote_set_id=emote_set_id,
                    emote_id=emote_id_to_delete,
                )

            log.debug("🖍️ - Removed emote #%s", emote_id_to_delete)

        # Step 4. Add the requested emote
        await self.bot.stv.emote_set_add_emote(emote_set_id=emote_set_id, emote_id=emote_id, emote_alias=emote_alias)
        log.debug("🖍️ - Added emote #%s", emote_id)

        query = """
            INSERT INTO ttv_cycling_emotes
            (emote_id, streamer_id, emote_set_id, requested_by)
            VALUES ($1, $2, $3, $4)
        """
        await self.bot.pool.execute(query, emote_id, redemption.broadcaster.id, emote_set_id, redemption.user.id)

        content = f"Added {emote_id}"
        if emote_ids_to_remove:
            content += f"; Removed {', '.join(emote_ids_to_remove)}"
        content += f" {const.STV.DonkCrayon}"
        await redemption.respond(content)
        await redemption.fulfill(token_for=redemption.broadcaster.id)

    @guards.is_owner_channel()
    @commands.command()
    async def remove_emote_from_cycling(self, ctx: IreContext, emote_id: Annotated[str, SevenTVEmoteConverter]) -> None:
        """Remove an emote from the cycling list.

        Useful when a streamer wants an emote to stop from being cycled out."""
        query = """
            DELETE FROM ttv_cycling_emotes
            WHERE emote_id = $1 AND streamer_id = $2
        """
        await self.bot.pool.execute(query, emote_id, ctx.broadcaster.id)
        await ctx.send(f"The {emote_id} was removed from the cycling emote list {const.STV.DonkCrayon}")

    @commands.is_owner()
    @guards.is_owner_channel()
    @commands.command()
    async def dev_cycle_reset(self, ctx: IreContext) -> None:
        """Developer command for temporary reset / testing.

        This
        * sets @Irene's `emote_limit` to 2;
        * removes all current @Irene's cycling emotes;
        * removes color emotes (Blue, Teal, Yellow) from Irene's active emote set;
        """

        query = "UPDATE ttv_cycling_emote_rewards SET emote_limit = $1 WHERE streamer_id = $2;"
        await self.bot.pool.execute(query, 2, const.UserID.Irene)

        query = "DELETE FROM ttv_cycling_emotes tce WHERE tce.streamer_id = $1;"
        await self.bot.pool.execute(query, const.UserID.Irene)

        color_ball_ids = [
            "01J8FC6EN0000DNWJ3ST67HH38",  # Blue
            "01J8FCA6RR0004HJ8DYSFE2PF2",  # Teal
            "01J8FCAY6R0006NP3M7JY4GDAA",
            "01J8FCBGRG000A5QBDAQ50YRYC",
        ]
        for emote_id in color_ball_ids:
            try:
                await ctx.bot.stv.emote_set_remove_emote(emote_set_id="01FAQVCS500002EV4FV330P46A", emote_id=emote_id)
            except Exception as err:
                print(err)
        await ctx.send(f"Done {const.STV.DonkCrayon}")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(CyclingEmotes(bot))
