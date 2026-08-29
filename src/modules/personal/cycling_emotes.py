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
from utils.seven_tv import EmoteNotFoundInSetError

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
        return await ctx.bot.stv.user_search_emote(broadcaster_id=ctx.broadcaster.id, emote_name=user_input)


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

        async def refund_and_respond(content: str) -> None:
            """Refund the redemption and response.

            Just a little lazy shortcut."""
            await redemption.refund(token_for=redemption.broadcaster.id)
            await redemption.respond(content=content)

        if len(split) > 2:
            await refund_and_respond(
                f"Bad Input, it's supposed to be an \"*emote_link/id* *emote_alias* - no extra words {const.FFZ.peepoPolice}"
            )
            return

        try:
            emote_id = to_emote_id(split[0])
        except errors.BadUserInputError:
            await refund_and_respond(f"Bad input, I couldn't find emote_link/emote_id in that {const.FFZ.peepoPolice}")
            return

        try:
            # If emote alias was given - assign it.
            emote_alias: str = split[1]
        except IndexError:
            # unfortunately, due to Seven TV weird implementation of Emote Set update call
            # we won't actually get the name from it, so we need to fetch it beforehand.
            emote_alias = await self.bot.stv.emote_get_name(emote_id)

        log.debug("🖍️ - emote_id = %s emote_alias = %s", emote_id, emote_alias)

        # Step 2. Get Emote Set
        emote_set_id = await self.bot.stv.user_get_active_emote(broadcaster_id=redemption.broadcaster.id)
        log.debug("🖍️ - Operating on emote_set #%s", emote_set_id)

        # Step 3. Remove emote(-s) if above the limit
        query = """
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
        """
        emote_ids_to_remove: list[str] = [
            r for (r,) in await self.bot.pool.fetch(query, redemption.broadcaster.id, emote_set_id)
        ]
        log.debug("🖍️ - Removing emotes #%s", emote_ids_to_remove)

        def get_seven_tv_link(emote_id: str) -> str:
            return f"7tv.app/emotes/{emote_id}"

        for emote_id_to_remove in emote_ids_to_remove:
            try:
                emote_name_to_remove: str = await self.bot.stv.emote_emote_set_alias(
                    emote_set_id=emote_set_id,
                    emote_id=emote_id_to_remove,
                )
                await self.bot.stv.emote_set_remove_emote(
                    emote_set_id=emote_set_id,
                    emote_id=emote_id_to_remove,
                )
            except seven_tv.EmoteNotFoundInSetError:
                pass
            else:
                await redemption.respond(f"Removed {emote_name_to_remove} ({get_seven_tv_link(emote_id_to_remove)})")
            log.debug("🖍️ - Removed emote #%s", emote_id_to_remove)
        if emote_ids_to_remove:
            query = """
                DELETE FROM ttv_cycling_emotes
                WHERE streamer_id = $1 AND emote_id = ANY($2);
            """
            await self.bot.pool.execute(query, redemption.broadcaster.id, emote_ids_to_remove)

        # Step 4. Add the requested emote
        try:
            await self.bot.stv.emote_set_add_emote(
                emote_set_id=emote_set_id,
                emote_id=emote_id,
                emote_alias=emote_alias,
            )
        except seven_tv.ConflictingEmoteNameError:
            await refund_and_respond(
                "This emote has a conflicting name, consider using an alias for it "
                f"(or maybe this emote was already added as non-cycling emote?) {const.FFZ.peepoPolice}"
            )
            return

        log.debug("🖍️ - Added emote #%s", emote_id)

        query = """
            INSERT INTO ttv_cycling_emotes
            (emote_id, streamer_id, emote_set_id, requested_by)
            VALUES ($1, $2, $3, $4)
        """
        await self.bot.pool.execute(query, emote_id, redemption.broadcaster.id, emote_set_id, redemption.user.id)

        await redemption.respond(f"Added '{emote_alias}' ({get_seven_tv_link(emote_id)}) {const.STV.DonkCrayon}")
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
            # cSpell: disable
            "01J8FC6EN0000DNWJ3ST67HH38",  # Blue
            "01J8FCA6RR0004HJ8DYSFE2PF2",  # Teal
            "01J8FCAY6R0006NP3M7JY4GDAA",  # Purple
            "01J8FCBGRG000A5QBDAQ50YRYC",  # Yellow
            "01J8FCC2B00005G1FWF2H9XPCE",  # Orange
            "01J8FCG750000D15QN0BDGKN3A",  # Pink
            "01J8FCGXKR000E0691W9XKC6X0",  # Olive
            "01J8FCHF68000E0691W9XKC6X5",  # LightBlue
            "01J8FCHZSG000C93G7AYMMNCBC",  # DarkGreen
            "01J8FCK00R0006NP3M7JY4GDB0",  # Brown
            # cSpell: enable
        ]
        for emote_id in color_ball_ids:
            with contextlib.suppress(EmoteNotFoundInSetError):
                await ctx.bot.stv.emote_set_remove_emote(
                    emote_set_id=const.STV_IRENE_DEFAULT_EMOTE_SET_ID,
                    emote_id=emote_id,
                )
        await ctx.send(f"Done {const.STV.DonkCrayon}")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(CyclingEmotes(bot))
