from __future__ import annotations

import abc
import datetime
import functools
import itertools
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict, override

from steam.ext.dota2 import GameMode, Hero, LobbyType, MatchOutcome
from twitchio.ext import commands

from bot import IreBot, IrePublicComponent, ireloop
from utils import errors, fuzzy
from utils.dota import constants as dota_constants, enums as dota_enums, utils as dota_utils

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from steam.ext.dota2 import User as Dota2SteamUser

    from bot import IreBot, IreContext

    class SteamAccountQueryRow(TypedDict):
        friend_id: int
        steam64_id: int

    class StreamersUserQueryRow(TypedDict):
        user_id: str
        display_name: str

    from utils.dota import SteamUserUpdate

    type ActiveMatch = PlayMatch | WatchMatch

    class ScoreQueryRow(TypedDict):
        friend_id: int
        start_time: datetime.datetime
        lobby_type: int
        game_mode: int
        outcome: int
        is_radiant: bool
        abandon: bool


__all__ = ("GameFlow",)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class RichPresence:
    """#TODO."""

    def __init__(self, raw: dict[str, str] | None) -> None:
        self.raw: dict[str, str] = raw or {}
        self.status = (
            dota_enums.Status.try_value(raw.get("status", "#MY_NO_STATUS")) if raw else dota_enums.Status.RichPresenceNone
        )

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} status={self.status.name}>"

    @override
    def __eq__(self, other: object) -> bool:
        # we need to exclude `param1` from comparison
        # because for Dota 2 Rich Presence it's usually a hero level
        # which is pointless for us to know
        # Hopefully this decision won't bite me.

        # https://stackoverflow.com/a/70145635/19217368
        ignore_keys: set[str] = {"param1"}
        return isinstance(other, RichPresence) and ignore_keys.issuperset(
            k for (k, _) in other.raw.items() ^ self.raw.items()
        )

    @override
    def __hash__(self) -> int:
        return hash(self.raw)


class Friend:
    def __init__(self, bot: IreBot, steam_user: Dota2SteamUser) -> None:
        self.bot: IreBot = bot
        self.steam_user: Dota2SteamUser = steam_user
        self.rich_presence: RichPresence = RichPresence(steam_user.rich_presence)
        self.active_match: PlayMatch | WatchMatch | None = None

    @override
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name="{self.steam_user.name}" id={self.steam_user.id}>'

    @property
    def is_playing_dota(self) -> bool:
        """#TODO."""
        return bool(app := self.steam_user.app) and app.id == 570


@dataclass
class Player:
    """#TODO.

    NO HERO DATA.
    """

    account_id: int
    player_slot: int
    lifetime_games: int
    medal: str

    @override
    def __repr__(self) -> str:
        return f"<Player id={self.account_id} slot={self.color}>"

    @classmethod
    async def create(cls, bot: IreBot, account_id: int, player_slot: int) -> Player:
        partial_user = bot.dota.create_partial_user(account_id)
        profile_card = await partial_user.dota2_profile_card()

        return Player(
            account_id=account_id,
            player_slot=player_slot,
            lifetime_games=profile_card.lifetime_games,
            medal=dota_utils.rank_medal_display_name(profile_card),
        )

    @property
    def stratz(self) -> str:
        return f"stratz.com/players/{self.account_id}"

    def profile(self) -> str:
        return f"{self.medal} \N{BULLET} {self.lifetime_games} total games \N{BULLET} {self.stratz}"

    @property
    def color(self) -> str:
        return dota_constants.PLAYER_COLORS[self.player_slot]


def format_match_response(func: Callable[..., Coroutine[Any, Any, str]]) -> Callable[..., Coroutine[Any, Any, str]]:
    @functools.wraps(func)
    async def wrapper(self: Match, *args: Any, **kwargs: Any) -> str:
        prefix = f"[{self.activity_tag}] " if self.activity_tag else ""
        response = await func(self, *args, **kwargs)
        return prefix + response

    return wrapper


class Match(abc.ABC):
    def __init__(
        self,
        bot: IreBot,
        tag: str = "",
    ) -> None:
        self.bot: IreBot = bot
        self.activity_tag: str = tag

        # match data
        self.match_id: int | None = None
        self.lobby_type: LobbyType | None = None
        self.game_mode: GameMode | None = None
        self.server_steam_id: int | None = None

        # players
        self.players: list[Player] = []
        self.heroes: list[Hero] = []

    @property
    def _is_players_data_ready(self) -> bool:
        return bool(self.game_mode) and len(self.players) == 10

    @property
    def _is_heroes_data_ready(self) -> bool:
        return bool(self.heroes) and all(bool(hero) for hero in self.heroes)

    @format_match_response
    async def game_medals(self) -> str:
        if not self.players:
            return "No players data yet."

        response_parts = [
            f"{hero if hero else player.color} {player.medal or '?'}"
            for player, hero in zip(self.players, self.heroes, strict=False)
        ]
        return " \N{BULLET} ".join(response_parts)  # [:5]) + " VS " + ", ".join(response_parts[5:])

    @format_match_response
    async def ranked(self) -> str:
        if not self.lobby_type or not self.game_mode:
            return "No lobby data yet."

        yes_no = "Yes" if self.lobby_type == LobbyType.Ranked else "No"
        return f"{yes_no}, it's {self.lobby_type.display_name} ({self.game_mode.display_name})"

    @format_match_response
    async def smurfs(self) -> str:
        if not self.players:
            return "No players data yet."

        response_parts = [
            f"{hero if hero else player.color} {player.lifetime_games}"
            for player, hero in zip(self.players, self.heroes, strict=False)
        ]
        return "Lifetime Games: " + " \N{BULLET} ".join(response_parts)

    def convert_argument_to_player_slot(self, argument: str) -> int:
        if argument.isdigit():
            # then the user typed only a number and our life is easy because it is a player slot
            player_slot = int(argument) - 1
            if not 0 <= player_slot <= 9:
                msg = "Sorry, player_slot can only be of 1-10 values."
                raise errors.PlaceholderRaiseError(msg)
            return player_slot

        # Unfortunate - we have to use the fuzzy search
        the_choice = (None, 0)

        # Step 1. let's look in more official identifiers such as colors or hero display names;
        for player_slot, hero in enumerate(self.heroes):
            identifiers = [dota_constants.PLAYER_COLORS[player_slot]]
            if hero:
                identifiers.extend([hero.name, hero.display_name])
            find = fuzzy.extract_one(argument, identifiers, score_cutoff=69)
            if find and find[1] > the_choice[1]:
                the_choice = (player_slot, find[1])

        # Step 2. let's see if hero aliases can beat official
        for player_slot, hero in enumerate(self.heroes):
            if hero:
                find = fuzzy.extract_one(argument, dota_constants.HERO_ALIASES[hero.id], score_cutoff=69)
                if find and find[1] > the_choice[1]:
                    the_choice = (player_slot, find[1])

        # Back to the dict
        player_slot = the_choice[0]
        if player_slot is None:
            msg = 'Sorry, didn\'t understand your query. Try something like !cmd "PA / 7 / Phantom Assassin / Blue".'
            raise errors.PlaceholderRaiseError(msg)
        return player_slot

    @format_match_response
    async def stats(self, argument: str) -> str:
        if not self.players:
            return "No player data yet."
        if self.server_steam_id is None:
            return "This match doesn't support real_time_stats"

        player_slot = self.convert_argument_to_player_slot(argument)

        try:
            match = await self.bot.dota.steam_web_api.get_real_time_stats(self.server_steam_id)
        except Exception as exc:
            log.exception("!items errored out at `get_real_time_stats` step", exc_info=exc)
            if self.lobby_type == LobbyType.NewPlayerMode:
                return "New Player Mode matches don't support `real_time_stats`."
            return "Failed to get `real_time_stats` for this match."

        team_ord = int(player_slot > 4)  # team_ord = 1 for Radiant, 2 for Dire
        team_slot = player_slot - 5 * team_ord  # 0 1 2 3 4 for Radiant, 5 6 7 8 9 for Dire

        for team in match["teams"]:
            if team["team_number"] == team_ord + 2:  # team_number = 2 for Radiant, 3 for Dire
                api_player = team["players"][team_slot]
                break
        else:
            msg = "Didn't find the player's team info Oups"
            raise errors.PlaceholderRaiseError(msg)

        prefix = f"[2m delay] {Hero.try_value(api_player['heroid'])} lvl {api_player['level']}"
        net_worth = f"NW: {api_player['net_worth']}"
        kda = f"{api_player['kill_count']}/{api_player['death_count']}/{api_player['assists_count']}"
        cs = f"CS: {api_player['lh_count']}"

        items = ", ".join([str(await self.bot.dota.items.by_id(item)) for item in api_player["items"] if item != -1])
        link = f"stratz.com/players/{api_player['accountid']}"

        response_parts = (prefix, net_worth, kda, cs, items, link)
        return " \N{BULLET} ".join(response_parts)

    @format_match_response
    async def match_id_command(self) -> str:
        return str(self.match_id)


class PlayMatch(Match):
    def __init__(self, bot: IreBot, watchable_game_id: str) -> None:
        super().__init__(bot)
        self.watchable_game_id: str = watchable_game_id
        self.lobby_id: int = int(watchable_game_id)

        self.average_mmr: int | None = None

        self.update_data.start()

    @ireloop(seconds=10, count=30)
    async def update_data(self) -> None:
        log.debug('Updating %s data for watchable_game_id "%s"', self.__class__.__name__, self.watchable_game_id)
        match = next(iter(await self.bot.dota.live_matches(lobby_ids=[self.lobby_id])), None)
        if not match:
            msg = f'FindTopSourceTVGames didn\'t find watchable_game_id "{self.watchable_game_id}".'
            raise errors.PlaceholderRaiseError(msg)

        if not self._is_heroes_data_ready:
            # match data
            self.server_steam_id = match.server_steam_id
            self.match_id = match.id
            self.average_mmr = match.average_mmr
            self.lobby_type = match.lobby_type
            self.game_mode = match.game_mode

            # players
            self.players = [
                await Player.create(self.bot, gc_player.id, player_slot)
                for player_slot, gc_player in enumerate(match.players)
            ]

        if not self._is_heroes_data_ready:
            self.heroes = [gc_player.hero for gc_player in match.players]
        else:
            log.debug('%s data ready for watchable_game_id: "%s"', self.__class__.__name__, self.watchable_game_id)
            self.update_data.stop()

    @override
    async def game_medals(self) -> str:
        mmr_notice = f"[{self.average_mmr} avg] " if self.average_mmr else ""
        return mmr_notice + await super().game_medals()


class WatchMatch(Match):
    def __init__(self, bot: IreBot, watching_server: str) -> None:
        super().__init__(bot, tag="Spectating")
        self.watching_server: str = watching_server
        self.server_steam_id: int = dota_utils.convert_id3_to_id64(watching_server)

        self.update_data.start()

    @ireloop(seconds=10, count=30)
    async def update_data(self) -> None:
        log.debug('Updating %s data for watching_server "%s"', self.__class__.__name__, self.watching_server)
        match = await self.bot.dota.steam_web_api.get_real_time_stats(self.server_steam_id)
        api_players = list(itertools.chain(match["teams"][0]["players"], match["teams"][1]["players"]))

        if not self._is_heroes_data_ready:
            # match data
            self.match_id = int(match["match"]["match_id"])
            self.lobby_type = LobbyType.try_value(match["match"]["lobby_type"])
            self.game_mode = GameMode.try_value(match["match"]["game_mode"])

            # players
            self.players = [
                await Player.create(self.bot, api_player["accountid"], player_slot)
                for player_slot, api_player in enumerate(api_players)
            ]

        if not self._is_heroes_data_ready:
            self.heroes = [Hero.try_value(api_player["heroid"]) for api_player in api_players]
        else:
            log.debug('Match data ready for watching_server: "%s"', self.watching_server)
            self.update_data.stop()


class GameFlow(IrePublicComponent):
    """#TODO."""

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)
        self.friends: dict[int, Friend] = {}

        self.play_matches_index: dict[str, PlayMatch] = {}
        self.watch_matches_index: dict[str, WatchMatch] = {}

    @override
    async def component_load(self) -> None:
        # Wait for all ready, commenting the following lines may lead to a disaster.
        # await self.bot.wait_until_ready()
        # await self.bot.dota.wait_until_ready()
        # await self.bot.dota.wait_until_gc_ready()

        # Start the component tasks/listeners
        self.starting_fill_friends.start()
        self.bot.add_listener(self.steam_user_update, event="event_steam_user_update")

        await self.bot.wait_for("self_friends_ready")
        self.fill_completed_matches_from_gc_match_history.start()

    @override
    async def component_teardown(self) -> None:
        self.starting_fill_friends.cancel()

    @ireloop(count=1)
    async def starting_fill_friends(self) -> None:
        """#TODO."""
        log.debug("Indexing bot's friend list.")
        for friend in await self.bot.dota.user.friends():
            self.friends[friend.id] = Friend(self.bot, friend._user)  # pyright: ignore[reportArgumentType] #TODO: ???
        log.debug('Friends index ready. Dispatching "self_friends_ready".')
        self.bot.dispatch("self_friends_ready")

    @commands.Component.listener("self_friends_ready")
    async def starting_rich_presence_check(self) -> None:
        """#TODO."""
        log.debug("Searching for any Dota 2 players in bot's friend list.")
        for friend in self.friends.values():
            await self.analyze_rich_presence(friend)

    async def analyze_rich_presence(self, friend: Friend) -> None:
        """#TODO."""
        rp = friend.rich_presence

        match rp.status:
            case dota_enums.Status.Idle | dota_enums.Status.MainMenu | dota_enums.Status.Finding:
                # Friend is in a Main Menu
                friend.active_match = None

            case dota_enums.Status.HeroSelection | dota_enums.Status.Strategy | dota_enums.Status.Playing:
                # Friend is in a match as a player
                watchable_game_id = rp.raw.get("WatchableGameID")

                if watchable_game_id is None:
                    # something is off
                    msg = "#todo"
                    raise errors.PlaceholderRaiseError(msg)

                if watchable_game_id not in self.play_matches_index:
                    self.play_matches_index[watchable_game_id] = PlayMatch(self.bot, watchable_game_id)
                friend.active_match = self.play_matches_index[watchable_game_id]

            case dota_enums.Status.Spectating:
                # Friend is spectating a match

                watching_server = rp.raw.get("watching_server")
                if watching_server is None:
                    msg = f"RP is Playing but {watching_server=}"
                    raise errors.PlaceholderRaiseError(msg)

                if watching_server not in self.watch_matches_index:
                    self.watch_matches_index[watching_server] = WatchMatch(self.bot, watching_server)
                friend.active_match = self.watch_matches_index[watching_server]
            case _:
                log.warning(
                    "Uncategorized Rich Presence Status \n \N{WARNING SIGN} %s %s %s\nrich_presence.raw=%s",
                    repr(friend),
                    rp.status,
                    rp.status.value,
                    rp.raw,
                )

    # @commands.Component.listener("steam_user_update")
    async def steam_user_update(self, update: SteamUserUpdate) -> None:
        """#TODO."""
        rp_before = RichPresence(update.before.rich_presence)
        rp_after = RichPresence(update.after.rich_presence)

        if rp_before == rp_after:
            return

        friend = self.friends.setdefault(update.after.id, Friend(self.bot, update.after))
        friend.rich_presence = rp_after
        log.debug("Recognized rich presence update for %s: %s", repr(friend), repr(friend.rich_presence))
        await self.analyze_rich_presence(friend)

    async def find_friend_account(self, broadcaster_id: str) -> Friend:
        """#TODO."""
        query = """
            SELECT twitch_id, friend_id
            FROM ttv_dota_accounts
            WHERE twitch_id = $1;
        """
        rows = await self.bot.pool.fetch(query, broadcaster_id)

        for row in rows:
            friend = self.friends.get(row["friend_id"])
            if friend and friend.is_playing_dota:
                return friend

        msg = "I'm sorry, it seems the streamer isn't playing Dota 2 at the moment."
        raise errors.PlaceholderRaiseError(msg)

    #################################
    # ACTIVE MATCH RELATED COMMANDS #
    #################################

    async def find_active_match(self, broadcaster_id: str) -> ActiveMatch:
        """#TODO."""
        friend = await self.find_friend_account(broadcaster_id)

        active_match = friend.active_match
        if not active_match:
            msg = f"No Active Game Found. Streamer's status: {friend.rich_presence.status}"
            raise errors.GameNotFoundError(msg)

        return active_match

    @commands.command(aliases=["gm"])
    async def game_medals(self, ctx: IreContext) -> None:
        """Fetch each player rank medals in the current game."""
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.game_medals()
        await ctx.send(response)

    @commands.command()
    async def ranked(self, ctx: IreContext) -> None:
        """Show whether the current game is ranked or not."""
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.ranked()
        await ctx.send(response)

    @commands.command()
    async def smurfs(self, ctx: IreContext) -> None:
        """Show amount of total games each player has on their accounts.

        Not really a "smurf detector", but it's quite good initial metric.
        """
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.smurfs()
        await ctx.send(response)

    @commands.command(aliases=["items", "item", "player"])
    async def stats(self, ctx: IreContext, *, argument: str) -> None:
        """Fetch items and some profile data about a certain player in the game.

        `argument` can be a hero name, hero alias, player slot or colour.
        """
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.stats()
        await ctx.send(response)

    @stats.error
    async def profile_error(self, payload: commands.CommandErrorPayload) -> None:
        """Error for !stats argument."""
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
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.match_id_command()
        await ctx.send(response)

    #################################
    #      COMPLEMENTED MATCHES     #
    #################################

    @ireloop(hours=3)
    async def fill_completed_matches_from_gc_match_history(self) -> None:
        """A backup task to double check if we haven't missed any games.

        Useful to keep W-L as precise as possible.
        """
        for friend in self.friends.values():
            match_history = await friend.steam_user.match_history()

            for match in match_history:
                # match history entities do not give proper outcome (Radiant/Dire)
                minimal = await self.bot.dota.create_partial_match(match.id).minimal()

                query = """
                    INSERT INTO ttv_dota_completed_matches
                    (match_id, start_time, lobby_type, game_mode, outcome)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (match_id) DO NOTHING;
                """
                await self.bot.pool.execute(
                    query,
                    match.id,
                    match.start_time,
                    match.lobby_type,
                    match.game_mode,
                    minimal.outcome,
                )

                player_slot = next((slot for slot, player in enumerate(minimal.players) if player.hero == match.hero), None)
                if player_slot is None:
                    msg = "#TODO"
                    raise errors.PlaceholderRaiseError(msg)
                is_radiant = player_slot < 5

                query = """
                    INSERT INTO ttv_dota_completed_match_players
                    (friend_id, match_id, hero_id, is_radiant, abandon)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (friend_id, match_id) DO
                        UPDATE SET abandon = $5;
                """
                await self.bot.pool.execute(
                    query,
                    friend.steam_user.id,
                    match.id,
                    match.hero.id,
                    is_radiant,
                    match.abandon,
                )

    #################################
    #    FRIEND RELATED COMMANDS    #
    #################################

    async def score_response_helper(self, broadcaster_id: str, stream_started_at: datetime.datetime | None = None) -> str:
        """#TODO."""
        clause = "AND m.start_time < $2" if stream_started_at else ""
        query = f"""
            SELECT d.friend_id, m.start_time, m.lobby_type, m.game_mode, m.outcome, p.is_radiant, p.abandon
            FROM ttv_dota_completed_matches m
            JOIN ttv_dota_completed_match_players p ON m.match_id = p.match_id
            JOIN ttv_dota_accounts d ON d.friend_id = p.friend_id
            WHERE d.twitch_id = $1 {clause}
            ORDER BY m.start_time DESC;
        """
        if stream_started_at:
            rows: list[ScoreQueryRow] = await self.bot.pool.fetch(query, broadcaster_id, stream_started_at)
        else:
            rows: list[ScoreQueryRow] = await self.bot.pool.fetch(query, broadcaster_id)

        # Example: {my_friend_id: {ScoreCategory.Ranked: [0, 4], ScoreCategory.Unranked: [0, 0]}}
        # So !wl should return Ranked 0 W - 4 L.
        # Notice the order!
        index: dict[int, dict[dota_enums.ScoreCategory, list[int]]] = {}

        cutoff_dt = datetime.datetime.now(datetime.UTC)
        for row in rows:
            # Let's assume gaming sessions to be separated by 6 hours from each other;
            if row["start_time"] < cutoff_dt - datetime.timedelta(hours=6):
                break
            cutoff_dt = row["start_time"]

            score_category = dota_enums.ScoreCategory.create(row["lobby_type"], row["game_mode"])
            if row["outcome"] in (MatchOutcome.RadiantVictory, MatchOutcome.DireVictory):
                # Normal Win Loss scenario
                win = (
                    row["outcome"] == MatchOutcome.RadiantVictory
                    if row["is_radiant"]
                    else row["outcome"] == MatchOutcome.DireVictory
                )
                index.setdefault(row["friend_id"], {}).setdefault(score_category, [0, 0])[int(win)] += 1

        response_parts = {
            friend_id: " \N{BULLET} ".join(
                f"{category.name} {results[1]} W - {results[0]} L" for category, results in scores.items()
            )
            for friend_id, scores in index.items()
        }
        if len(index) == 0:
            return "0 W - 0 L"
        if len(index) == 1:
            return next(iter(response_parts.values()))
        return " | ".join(
            # Let's make extra query to know name accounts
            f"{u.name if (u := self.bot.dota.get_user(friend_id)) else friend_id}: {part}"
            for friend_id, part in response_parts.items()
        )

    @commands.group(aliases=["wl", "winloss"], invoke_fallback=True)
    async def score(self, ctx: IreContext) -> None:
        """Show streamer's Win - Loss score ratio for today's gaming session.

        This by design should include offline games as well.
        Gaming sessions are considered separated if they are for at least 6 hours apart.
        """
        streamer = self.bot.streamers[ctx.broadcaster.id]
        if not streamer.online:
            response = 'Streamer is offline. To get their offline score use "!wl offline".'
        else:
            response = await self.score_response_helper(ctx.broadcaster.id, streamer.started_dt)
        await ctx.send(content=response)

    @score.command()
    async def offline(self, ctx: IreContext) -> None:
        """#TODO."""
        response = await self.score_response_helper(ctx.broadcaster.id)
        await ctx.send(content=response)


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(GameFlow(bot))
