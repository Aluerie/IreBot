from __future__ import annotations

import datetime
import logging
from time import perf_counter
from typing import TYPE_CHECKING, Any, TypedDict, override

from twitchio.ext import commands

from bot import IreComponent, ireloop
from config import config
from utils import const, errors, helpers

from .models import BLOCKED_RP_STATUSES, Streamer

if TYPE_CHECKING:
    from bot import IreBot, IreContext

    from .models import ActiveMatch, RPStatus

    class CheckTwitchRenamesQueryRow(TypedDict):
        twitch_id: str
        twitch_name: str


__all__ = ("GameFlow",)


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GameFlow(IreComponent):
    """Cog responsible for Dota 2 related commands and statistics tracker.

    This functionality is supposed to be an analogy to 9kmmrbot/dotabod features.
    """

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.streamer: Streamer = Streamer(self.bot, config["STEAM"]["IRENE_ID64"])
        self.debug_mode: bool = True

    async def debug_send(self, message: str) -> None:
        """Debug send.

        The message will be sent to Irene's chat only if debug mode is activated.
        """
        if self.debug_mode:
            await self.deliver(f"[debug] {message}")

    @override
    async def component_load(self) -> None:
        """Cog load."""
        self.clean_up_the_database.start()
        self.check_streamers_rich_presence.start()
        # self.check_last_games.start()
        self.check_twitch_accounts_renames.start()

    @override
    async def component_teardown(self) -> None:
        self.check_streamers_rich_presence.cancel()

    @ireloop(hours=48)
    async def clean_up_the_database(self) -> None:
        log.debug("Task: cleaning database from too old matches.")
        query = """
            DELETE FROM ttv_dota_matches
            WHERE match_id IN (
                SELECT match_id
                FROM ttv_dota_matches
                WHERE start_time < $1
                ORDER BY start_time DESC
                OFFSET 1
            )
        """
        now = datetime.datetime.now(datetime.UTC)
        cutoff_dt = now - datetime.timedelta(hours=48)
        await self.bot.pool.execute(query, cutoff_dt)

        if self.clean_up_the_database.current_loop == 0:
            await self.streamer.fix_match_history()

    @ireloop(seconds=20)
    async def check_streamers_rich_presence(self) -> None:
        await self.streamer.update()

    @commands.Component.listener("event_rich_presence_changed")
    async def rich_presence_changed(self, status: RPStatus) -> None:
        """Debug alert for when the Irene's Rich Presence change is detected."""
        if status.name == f"{status.__class__.__name__}UnknownValue":
            if any(rp in status.value for rp in BLOCKED_RP_STATUSES):
                # skip blocked RP statuses, such as Crownfall or Deadlock
                return

            await self.debug_send(f'RP Change: Unknown "{status.value}"')
        else:
            await self.debug_send(f"RP Change: {status}")

    @commands.Component.listener("event_reset_streamer")
    async def reset_streamer(self, event_msg: str) -> None:
        """Debug alert for when the streamer state is reset."""
        await self.debug_send(f"Reset: {event_msg}")

    @commands.Component.listener("event_match_data_ready")
    async def announce_data_ready(self) -> None:
        """Debug alert for when the basic match data for a freshly queued game is ready."""
        await self.debug_send(f"Players+Match Data Ready! (1/2) {const.STV.wickedchad}")

    @commands.Component.listener("event_match_hero_ready")
    async def announce_hero_ready(self) -> None:
        """Debug alert for when hero match data for a freshly queued game is ready."""
        await self.debug_send(f"Hero Info Ready! (2/2) {const.STV.wickedchad}")

    # @commands.Component.listener("event_check_last_games")
    # async def start_checking_match_outcome(self, match_id: int, hero: Hero) -> None:
    #     await self.debug_send("Game ended. Checking data for it!")

    #     self.streamer.promised_match_ids[match_id] = hero

    #     if not self.check_last_games.is_running():
    #         self.check_last_games.start()

    # @irenes_loop(seconds=30)
    # async def check_last_games(self) -> None:
    #     await self.streamer.update_last_game()

    #     if not self.streamer.promised_match_ids:
    #         self.check_last_games.stop()

    # ACTIVE MATCH COMMANDS

    async def get_active_match(self, *, is_hero: bool) -> ActiveMatch:
        """Get Irene's current active match."""
        start = perf_counter()

        match = self.streamer.active_match
        if match is None:
            await self.streamer.update()
        else:
            if not match.is_data_ready:
                await match.update_data()
            if is_hero and not match.is_hero_ready:
                await match.update_heroes()

        if match:
            return match
        if self.streamer.unsupported_error:
            msg = self.streamer.unsupported_error
        else:
            msg = f"No Game Found. Irene's Status: {self.streamer.rp_status.display_name}"

        perf_time = perf_counter() - start
        msg = f"[{perf_time:.3f}s] {msg}"
        raise errors.GameNotFoundError(msg)

    def fmt_response(self, response: str, perf: helpers.measure_time, *, is_watch: bool) -> str:
        """Apply some formatting tags before sending the message."""
        debug_prefix = f"[{perf.end:.3f}s] " if self.debug_mode else ""
        tag = "[Watching] " if is_watch else ""
        return debug_prefix + tag + response

    @commands.command(aliases=["gm"])
    async def game_medals(self, ctx: IreContext) -> None:
        """Fetch each player rank medals in the current game."""
        async with helpers.measure_time() as perf:
            active_match = await self.get_active_match(is_hero=False)
            response = active_match.game_medals()
        await ctx.send(self.fmt_response(response, perf, is_watch=active_match.is_watch))

    @commands.command()
    async def ranked(self, ctx: IreContext) -> None:
        """Show whether the current game is ranked or not."""
        async with helpers.measure_time() as perf:
            active_match = await self.get_active_match(is_hero=False)
            response = active_match.ranked()
        await ctx.send(self.fmt_response(response, perf, is_watch=active_match.is_watch))

    @commands.command()
    async def smurfs(self, ctx: IreContext) -> None:
        """Show amount of total games each player has on their accounts.

        Not really a "smurf detector", but it's quite good initial metric.
        """
        async with helpers.measure_time() as perf:
            active_match = await self.get_active_match(is_hero=False)
            response = active_match.smurfs()
        await ctx.send(self.fmt_response(response, perf, is_watch=active_match.is_watch))

    @commands.command(aliases=["items", "item", "player"])
    async def profile(self, ctx: IreContext, *, argument: str) -> None:
        """Fetch items and some profile data about a certain player in the game.

        `argument` can be a hero name, hero alias, player slot or colour.
        """
        async with helpers.measure_time() as perf:
            active_match = await self.get_active_match(is_hero=False)
            response = await active_match.profile(argument)
        await ctx.send(self.fmt_response(response, perf, is_watch=active_match.is_watch))

    @profile.error
    async def profile_error(self, payload: commands.CommandErrorPayload) -> None:
        """Error for !profile argument."""
        if isinstance(payload.exception, commands.MissingRequiredArgument):
            await payload.context.send(
                "You need to provide a hero name (i.e. VengefulSpirit , PA, Mireska, etc) or "
                "player slot (i.e. 9, DarkGreen )",
            )
        else:
            raise payload.exception

    @commands.command(aliases=["matchid"])
    async def match_id(self, ctx: IreContext) -> None:
        """Show match ID for the current match."""
        async with helpers.measure_time() as perf:
            active_match = await self.get_active_match(is_hero=False)
            response = f"{active_match.match_id}"
        await ctx.send(self.fmt_response(response, perf, is_watch=active_match.is_watch))

    # LAST GAME

    @commands.command(aliases=["lg", "lm"])
    async def last_game(self, ctx: IreContext) -> None:
        """Show some data about streamer's previous game."""
        async with helpers.measure_time() as perf:
            last_game = self.streamer.last_game
            response = last_game.last_game_command_response if last_game else "No Data Yet."
        await ctx.send(self.fmt_response(response, perf, is_watch=False))

    # STREAMER INFO COMMANDS

    @commands.command(aliases=["wl", "winloss"])
    async def score(self, ctx: IreContext) -> None:
        """Show streamer's Win - Loss score ratio for today's gaming session.

        This by design should include offline games as well.
        Gaming sessions are considered separated if they are for at least 6 hours apart.
        """
        # await self.prepare()  # do we need it here ?
        async with helpers.measure_time() as perf:
            response = await self.streamer.wl_command_response()
        await ctx.send(self.fmt_response(response, perf, is_watch=False))

    @commands.command()
    async def mmr(self, ctx: IreContext) -> None:
        """Show streamer's MMR."""
        async with helpers.measure_time() as perf:
            response = await self.streamer.mmr_command_response()
        await ctx.send(self.fmt_response(response, perf, is_watch=False))

    @commands.is_moderator()
    @commands.command(name="setmmr")
    async def set_mmr(self, ctx: IreContext, mmr: int) -> None:
        """Set streamer's MMR."""
        async with helpers.measure_time() as perf:
            query = "UPDATE ttv_dota_streamers SET mmr = $1 WHERE account_id = $2"
            await self.bot.pool.execute(query, mmr, self.streamer.account_id)
            response = f"Set mmr to {mmr}"
        await ctx.send(self.fmt_response(response, perf, is_watch=False))

    @ireloop(time=datetime.time(hour=6, minute=34, second=10))
    async def check_twitch_accounts_renames(self) -> None:
        """Checks if people in FPC database renamed themselves on twitch.tv.

        I think we're using twitch ids everywhere so this timer is more for convenience matter
        when I'm browsing the database, but still.
        """
        if datetime.datetime.now(datetime.UTC).day != 31:
            return

        query = "SELECT twitch_id, twitch_name FROM ttv_dota_streamers"
        rows: list[CheckTwitchRenamesQueryRow] = await self.bot.pool.fetch(query)

        user_rows = {row["twitch_id"]: row["twitch_name"] for row in rows}
        # TODO: I think it bricks if user_ids is more than 100 ?
        users = await self.bot.fetch_users(ids=list(user_rows.keys()))

        for user in users:
            if user.display_name.lower() != user_rows[user.id]:
                query = "UPDATE ttv_dota_streamers SET twitch_name = $1 WHERE twitch_id = $2"
                await self.bot.pool.execute(query, user.display_name, user.id)

    # NOT ACTIVE
    @ireloop(hours=3)
    async def double_check_task(self) -> None:
        """A backup task to double check if we haven't missed any games.

        Useful to keep W-L as precise as possible.
        """
        account_id = self.streamer.account_id

        partial_user = self.bot.dota.instantiate_partial_user(account_id)
        match_history = await partial_user.match_history()

        history_match_ids = {match.id: match for match in match_history}
        query = """
            SELECT match_id
            FROM ttv_dota_matches
            WHERE account_id = $1 AND match_id != ANY($2)
            ORDER BY match_id DESC
            LIMIT 30
        """  # limit 30 but match history returns 20 by default
        database_match_ids: list[int] = [
            r for (r,) in await self.bot.pool.fetch(query, account_id, history_match_ids.keys())
        ]

        to_add_match_ids = set(history_match_ids.keys())
        to_add_match_ids.difference_update(set(database_match_ids))

        for match_id in to_add_match_ids:
            history_match = history_match_ids[match_id]
            await self.streamer.add_completed_match_to_database(history_match)

    @double_check_task.before_loop
    @clean_up_the_database.before_loop
    @check_streamers_rich_presence.before_loop
    async def before_check_streamers_rich_presence(self) -> None:
        """Wait for the IreBot, Dota Client and Game Coordinator ready-s."""
        await self.bot.wait_until_ready()
        await self.bot.dota.wait_until_ready()
        await self.bot.dota.wait_until_gc_ready()
