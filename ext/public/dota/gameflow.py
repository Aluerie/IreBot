from __future__ import annotations

import asyncio
import datetime
import functools
import itertools
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, TypedDict, override

import steam
from steam.ext.dota2 import GameMode, Hero, LobbyType, MatchOutcome, MinimalMatch, User as Dota2User
from twitchio.ext import commands

from bot import IrePublicComponent, ireloop
from utils import errors, fmt, fuzzy
from utils.dota import constants as dota_constants, enums as dota_enums, utils as dota_utils

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from steam.ext.dota2 import MatchHistoryMatch, User as Dota2SteamUser

    from bot import IreBot, IreContext

    class SteamAccountQueryRow(TypedDict):
        friend_id: int
        steam64_id: int

    class StreamersUserQueryRow(TypedDict):
        user_id: str
        display_name: str

    from utils.dota import SteamUserUpdate

    type ActiveMatch = PlayMatch | WatchMatch | UnsupportedMatch

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
    """Class representing Steam Rich Presence.

    Normally Rich Presence is just a dictionary of data.
    This class adds some utility for GameFlow component to use.
    """

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
        # we need to exclude `param1` from comparison because for Dota 2 Rich Presence it's usually a hero level
        # which is pointless for the gameflow logic to know. Hopefully, this decision won't bite me in the future.

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
        self.active_match: PlayMatch | WatchMatch | UnsupportedMatch | None = None

    @override
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name="{self.steam_user.name}" id={self.steam_user.id}>'

    @property
    def is_playing_dota(self) -> bool:
        """Whether this friend is playing dota or not."""
        return bool(app := self.steam_user.app) and app.id == 570


@dataclass
class Player:
    """#TODO.

    Notes
    -----
    * Compared to my all previous implementations of this - the current iteration for Player class **_DOES NOT_**
        have any data about selected hero or any logic to assign a hero to the player.
        I found it's better to keep `.players` and `.heroes` data bound to `Match` classes.
        The order is carefully taken care of anyway.
    """

    friend_id: int
    player_slot: int
    lifetime_games: int
    medal: str

    @override
    def __repr__(self) -> str:
        return f"<Player id={self.friend_id} slot={self.color}>"

    @classmethod
    async def create(cls, bot: IreBot, account_id: int, player_slot: int) -> Player:
        partial_user = bot.dota.create_partial_user(account_id)
        profile_card = await partial_user.dota2_profile_card()

        return Player(
            friend_id=account_id,
            player_slot=player_slot,
            lifetime_games=profile_card.lifetime_games,
            medal=dota_utils.rank_medal_display_name(profile_card),
        )

    @property
    def stratz(self) -> str:
        return f"stratz.com/players/{self.friend_id}"

    def profile(self) -> str:
        return f"{self.medal} \N{BULLET} {self.lifetime_games} total games \N{BULLET} {self.stratz}"

    @property
    def color(self) -> str:
        return dota_constants.PLAYER_COLORS[self.player_slot]


def format_match_response(func: Callable[..., Coroutine[Any, Any, str]]) -> Callable[..., Coroutine[Any, Any, str]]:
    @functools.wraps(func)
    async def wrapper(self: Match, *args: Any, **kwargs: Any) -> str:
        if isinstance(self, UnsupportedMatch):
            return self.activity_tag

        prefix = f"[{self.activity_tag}] " if self.activity_tag else ""
        response = await func(self, *args, **kwargs)
        return prefix + response

    return wrapper


class Match:
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

        # ready events
        self.players_data_ready: asyncio.Event = asyncio.Event()
        self.heroes_data_ready: asyncio.Event = asyncio.Event()

    def _is_players_data_ready(self) -> bool:
        return bool(self.game_mode) and len(self.players) == 10

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
                find = fuzzy.extract_one(argument, dota_constants.HERO_ALIASES.get(hero.id, []), score_cutoff=69)
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
        """A response for chat command !stats."""
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
            msg = "Didn't find the player's team info"
            raise errors.PlaceholderRaiseError(msg)

        prefix = f"[2m delay] {api_player['name']} {Hero.try_value(api_player['heroid'])} lvl {api_player['level']}"
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

    @format_match_response
    async def notable_players(self) -> str:
        if not self.players:
            return "No player data yet."

        query = """
            SELECT friend_id, nickname
            FROM ttv_dota_notable_players
            WHERE friend_id = ANY($1);
        """
        rows = await self.bot.pool.fetch(query, [p.friend_id for p in self.players])
        if not rows:
            return "No notable players found"

        nickname_mapping = {row["friend_id"]: row["nickname"] for row in rows}

        response_parts = [
            f"{nick} as {hero if hero else player.color}"
            for player, hero in zip(self.players, self.heroes, strict=False)
            if (nick := nickname_mapping.get(player.friend_id))
        ]
        return " \N{BULLET} ".join(response_parts)


class PlayMatch(Match):
    def __init__(self, bot: IreBot, watchable_game_id: str) -> None:
        super().__init__(bot)
        self.watchable_game_id: str = watchable_game_id
        self.lobby_id: int = int(watchable_game_id)

        self.average_mmr: int | None = None

        self.update_data.start()

    @ireloop(seconds=10.1, count=30)
    async def update_data(self) -> None:
        log.debug('Updating %s data for watchable_game_id "%s"', self.__class__.__name__, self.watchable_game_id)
        match = next(iter(await self.bot.dota.live_matches(lobby_ids=[self.lobby_id])), None)
        if not match:
            msg = f'FindTopSourceTVGames didn\'t find watchable_game_id "{self.watchable_game_id}".'
            raise errors.PlaceholderRaiseError(msg)

        if not self.players_data_ready.is_set():
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
            if self._is_players_data_ready():
                self.players_data_ready.set()
                log.debug('%s players data ready for: "%s"', self.__class__.__name__, self.watchable_game_id)

        if not self.heroes_data_ready.is_set():
            self.heroes = [gc_player.hero for gc_player in match.players]
            if self._is_heroes_data_ready():
                self.heroes_data_ready.set()
                log.debug('%s heroes data ready for: "%s"', self.__class__.__name__, self.watchable_game_id)

        if self.players_data_ready.is_set() and self.heroes_data_ready.is_set():
            self.update_data.stop()

    @override
    async def game_medals(self) -> str:
        mmr_notice = f"[{self.average_mmr} avg] " if self.average_mmr else ""
        return mmr_notice + await super().game_medals()

    async def played_with(self, friend_id: int, last_game: MinimalMatch) -> str:
        if not self.players:
            return "No player data yet."

        last_game_hero_player_index: dict[int, Hero] = {p.id: p.hero for p in last_game.players}
        last_game_hero_player_index.pop(friend_id, None)  # remove the streamer themselves

        response_parts = [
            f"{hero if hero else player.color} as {last_game_played_as}"
            for player, hero in zip(self.players, self.heroes, strict=False)
            if (last_game_played_as := last_game_hero_player_index.get(player.friend_id))
        ]
        if response_parts:
            return " \N{BULLET} ".join(response_parts)
        return "No players from the last game present in the match"


class WatchMatch(Match):
    def __init__(self, bot: IreBot, watching_server: str) -> None:
        super().__init__(bot, tag="Spectating")
        self.watching_server: str = watching_server
        self.server_steam_id: int = dota_utils.convert_id3_to_id64(watching_server)

        self.update_data.start()

    @ireloop(seconds=10.1, count=30)
    async def update_data(self) -> None:
        log.debug('Updating %s data for watching_server "%s"', self.__class__.__name__, self.watching_server)
        match = await self.bot.dota.steam_web_api.get_real_time_stats(self.server_steam_id)
        api_players = list(itertools.chain(match["teams"][0]["players"], match["teams"][1]["players"]))

        if not self.players_data_ready.is_set():
            # match data
            self.match_id = int(match["match"]["match_id"])
            self.lobby_type = LobbyType.try_value(match["match"]["lobby_type"])
            self.game_mode = GameMode.try_value(match["match"]["game_mode"])

            # players
            self.players = [
                await Player.create(self.bot, api_player["accountid"], player_slot)
                for player_slot, api_player in enumerate(api_players)
            ]
            if self._is_players_data_ready():
                self.players_data_ready.set()
                log.debug('%s players data ready for: "%s"', self.__class__.__name__, self.watching_server)

        if not self.heroes_data_ready.is_set():
            self.heroes = [Hero.try_value(api_player["heroid"]) for api_player in api_players]
            if self._is_heroes_data_ready():
                self.heroes_data_ready.set()
                log.debug('%s heroes data ready for: "%s"', self.__class__.__name__, self.watching_server)

        if self.players_data_ready.is_set() and self.heroes_data_ready.is_set():
            self.update_data.stop()


class UnsupportedMatch(Match):
    def __init__(self, bot: IreBot, tag: str = "") -> None:
        super().__init__(bot, tag)


class UserNotFound(commands.BadArgument):
    """For when a matching user cannot be found."""

    def __init__(self, argument: str) -> None:
        self.argument = argument
        super().__init__(f"User {argument!r} not found.", value=argument)


class SteamUserConverter(commands.Converter[Dota2User]):
    """Simple Steam User converter."""

    @override
    async def convert(self, ctx: IreContext, argument: str) -> Dota2User:
        try:
            return await ctx.bot.dota.fetch_user(steam.utils.parse_id64(argument))
        except steam.InvalidID:
            id64 = await steam.utils.id64_from_url(argument)
            if id64 is None:
                raise UserNotFound(argument) from None
            return await ctx.bot.dota.fetch_user(id64)
        except TimeoutError:
            raise UserNotFound(argument) from None


class GameFlow(IrePublicComponent):
    """#TODO."""

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)
        self.friends: dict[int, Friend] = {}

        self.pending_matches: dict[int, set[int]] = {}
        self.play_matches_index: dict[str, PlayMatch] = {}
        self.watch_matches_index: dict[str, WatchMatch] = {}

    @override
    async def component_load(self) -> None:
        self.starting_fill_friends.start()
        self.add_steam_user_update_listener.start()
        self.fill_completed_matches_from_gc_match_history.start()
        self.remove_way_too_old_matches.start()

    @override
    async def component_teardown(self) -> None:
        self.starting_fill_friends.cancel()
        self.add_steam_user_update_listener.cancel()
        self.fill_completed_matches_from_gc_match_history.cancel()
        self.remove_way_too_old_matches.cancel()

    #################################
    #           EVENTS              #
    #################################

    @ireloop(count=1)
    async def starting_fill_friends(self) -> None:
        """#TODO."""
        log.debug("Indexing bot's friend list.")
        for friend in await self.bot.dota.user.friends():
            self.friends[friend.id] = Friend(self.bot, friend._user)  # pyright: ignore[reportArgumentType] #TODO: ???

        for friend in self.friends.values():
            await self.analyze_rich_presence(friend)

        log.debug('Friends index ready. Setting "_friends_index_ready".')
        self.bot._friends_index_ready.set()

    async def analyze_rich_presence(self, friend: Friend) -> None:
        """#TODO."""
        rp = friend.rich_presence

        if friend.is_playing_dota:
            # Update `last_seen` in the database;
            query = """
                UPDATE ttv_dota_accounts
                SET last_seen = $1
                WHERE friend_id = $2
            """
            await self.bot.pool.execute(query, datetime.datetime.now(datetime.UTC), friend.steam_user.id)

        match rp.status:
            case dota_enums.Status.Idle | dota_enums.Status.MainMenu | dota_enums.Status.Finding:
                # Friend is in a Main Menu
                self.add_active_match_to_pending(friend)
                friend.active_match = None

            case dota_enums.Status.HeroSelection | dota_enums.Status.Strategy | dota_enums.Status.Playing:
                # Friend is in a match as a player
                watchable_game_id = rp.raw.get("WatchableGameID")

                if watchable_game_id is None:
                    # something is off
                    lobby_param0 = rp.raw.get("param0")

                    if lobby_param0 == dota_enums.LobbyParam0.DemoMode:
                        friend.active_match = UnsupportedMatch(self.bot, tag="Demo mode is not supported")
                        return
                    if lobby_param0 == dota_enums.LobbyParam0.BotMatch:
                        friend.active_match = UnsupportedMatch(self.bot, tag="Private Lobbies are not supported")
                        return
                    msg = "#todo"
                    raise errors.PlaceholderRaiseError(msg)
                if watchable_game_id == "0":
                    # something is off again
                    party_state = rp.raw.get("party")
                    if party_state and "party_state: UI" in party_state:
                        # hacky but this is what happens when we quit the match into main menu sometimes
                        # let's pass to get a confirmation from other statuses (maybe wrong)
                        pass
                    else:
                        msg = f'RP is "Playing" but {watchable_game_id=} and {party_state=}'
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
                    "Uncategorized Rich Presence Status \nfriend=%s rich_presence=%s status=%s\nrich_presence.raw=%s",
                    repr(friend),
                    rp.status,
                    rp.status.value,
                    rp.raw,
                )
                # Let's assume that other statuses = not Dota
                self.add_active_match_to_pending(friend)
                friend.active_match = None

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

    def add_active_match_to_pending(self, friend: Friend) -> None:
        """#TODO."""
        if (match := friend.active_match) and isinstance(match, PlayMatch) and match.match_id:
            self.pending_matches.setdefault(friend.steam_user.id, set()).add(match.match_id)

        if self.pending_matches and not self.process_pending_matches.is_running():
            self.process_pending_matches.start()

    #################################
    # ACTIVE MATCH RELATED COMMANDS #
    #################################

    async def find_friend_account(self, broadcaster_id: str, *, is_green_online_required: bool = True) -> Friend:
        """Find broadcaster's friend account.

        Note that we only return their last-seen account.
        We assume the last-seen account is the one they want to use commands against.
        """
        query = """
            SELECT twitch_id, friend_id
            FROM ttv_dota_accounts
            WHERE twitch_id = $1
            ORDER BY last_seen DESC
            LIMIT 1;
        """
        row = await self.bot.pool.fetchrow(query, broadcaster_id)
        friend = self.friends.get(row["friend_id"])

        if friend:
            if is_green_online_required and not friend.is_playing_dota:
                msg = "Inactive command \N{BULLET} it requires streamer to be green-online \N{LARGE GREEN CIRCLE} in Dota 2"
                raise errors.PlaceholderRaiseError(msg)
            return friend

        if self.bot._friends_index_ready.is_set():
            msg = "Bot's Dota 2 functionality is not fully loaded in. Please, wait a bit."
            raise errors.PlaceholderRaiseError(msg)

        msg = "Couldn't find streamer's steam account in my friends uuh"
        raise errors.PlaceholderRaiseError(msg)

    async def find_active_match(self, broadcaster_id: str) -> ActiveMatch:
        """Find broadcaster's active match."""
        friend = await self.find_friend_account(broadcaster_id)

        active_match = friend.active_match
        if not active_match:
            msg = f"No Active Game Found \N{BULLET} Streamer's status: {friend.rich_presence.status}"
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

    @commands.command(aliases=["lifetime"])
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
        response = await active_match.stats(argument)
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

    @commands.command(name="notable", aliases=["np"])
    async def notable_players(self, ctx: IreContext) -> None:
        """List notable players for the current match."""
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.notable_players()
        await ctx.send(response)

    #################################
    #           LAST GAME           #
    #################################

    async def get_last_game(self, broadcaster_id: str) -> tuple[int, int, MinimalMatch]:
        """A helper function to get broadcaster's last played game from the database.

        Returns
        -------
        tuple[int, int, MinimalMatch]
            This tuple consists of `friend_id`, `hero_id` and `last_game` of `MinimalMatch` type because
            both `friend_id` and `hero_id` are useful at identifying the correct player later on.
            If a player has their data private then MinimalMatch will have zero for that player slot `friend_id`
        """
        query = """
            SELECT p.match_id, p.friend_id, p.hero_id
            FROM ttv_dota_completed_matches m
            JOIN ttv_dota_completed_match_players p ON m.match_id = p.match_id
            JOIN ttv_dota_accounts a ON a.friend_id = p.friend_id
            WHERE a.twitch_id = $1
            ORDER BY m.start_time DESC
            LIMIT 1;
        """
        row = await self.bot.pool.fetchrow(query, broadcaster_id)
        if not row:
            msg = "No last game found: it seems streamer hasn't played Dota in a while"
            raise errors.PlaceholderRaiseError(msg)
        last_game = await self.bot.dota.create_partial_match(row["match_id"]).minimal()
        return row["friend_id"], row["hero_id"], last_game

    @commands.command(name="played", aliases=["last_game", "lg", "lm"])
    async def played_with(self, ctx: IreContext) -> None:
        """List recurring players from the last game present in the current match."""
        active_match = await self.find_active_match(ctx.broadcaster.id)

        if isinstance(active_match, PlayMatch):
            friend_id, _, last_game = await self.get_last_game(ctx.broadcaster.id)
            response = await active_match.played_with(friend_id, last_game)
        else:
            response = 'Only matches streamer is playing in support "!last_game" command usage'
        await ctx.send(response)

    @commands.command(aliases=["pm"])
    async def previous_match(self, ctx: IreContext) -> None:
        """Show summary stats for the previous match."""
        _, hero_id, match = await self.get_last_game(ctx.broadcaster.id)

        slot, player = next(iter((s, p) for s, p in enumerate(match.players) if p.hero.id == hero_id), (None, None))
        if not slot or not player:
            msg = "Somehow can't find streamer's account in their previous match uuh weird"
            raise errors.PlaceholderRaiseError(msg)

        is_radiant = slot < 5
        score_category = dota_enums.ScoreCategory.create(match.lobby_type, match.game_mode)
        if match.outcome >= MatchOutcome.NotScoredPoorNetworkConditions:
            outcome = "Not Scored"
        elif match.outcome == MatchOutcome.RadiantVictory:
            outcome = "Win" if is_radiant else "Loss"
        elif match.outcome == MatchOutcome.DireVictory:
            outcome = "Loss" if is_radiant else "Win"
        else:
            outcome = "Unknown outcome"
        delta = datetime.datetime.now(datetime.UTC) - (match.start_time + match.duration)

        response = (
            f"Last Game - {score_category.name}: {outcome} as {player.hero} {player.kills}/{player.deaths}/{player.assists} "
            f"\N{BULLET} ended {fmt.timedelta_to_words(delta, fmt=fmt.TimeDeltaFormat.Letter)} ago "
            f"\N{BULLET} stratz.com/matches/{match.id}"
        )
        await ctx.send(response)

    #################################
    #       COMPLETED MATCHES       #
    #################################

    async def add_completed_match_to_database(self, match: MatchHistoryMatch, friend_id: int) -> None:
        """#TODO."""
        if match.start_time < datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=48):
            # Match is way too old to care
            return

        # match history entities on their own do not give proper outcome (Radiant/Dire)
        minimal = await self.bot.dota.create_partial_match(match.id).minimal()

        query = """
            INSERT INTO ttv_dota_completed_matches
            (match_id, start_time, lobby_type, game_mode, outcome)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (match_id) DO NOTHING
            RETURNING match_id;
        """
        match_id: int | None = await self.bot.pool.fetchval(
            query,
            match.id,
            match.start_time,
            match.lobby_type,
            match.game_mode,
            minimal.outcome,
        )
        if match_id is not None:
            # if it's None - then it already was in the database
            # otherwise it's a new match and we can explore mmr_delta
            # MMR Tracking
            if match.lobby_type != LobbyType.Ranked:
                mmr_delta = 0
            elif match.abandon:
                mmr_delta = -25
            elif minimal.outcome >= MatchOutcome.NotScoredPoorNetworkConditions:
                mmr_delta = 0
            else:
                mmr_delta = 25 if match.win else -25

            if mmr_delta:
                query = """
                    UPDATE ttv_dota_accounts
                    SET estimated_mmr = estimated_mmr + $1
                    WHERE friend_id = $2;
                """
                await self.bot.pool.execute(query, mmr_delta, friend_id)

        player_slot = next((slot for slot, player in enumerate(minimal.players) if player.hero == match.hero), None)
        if player_slot is None:
            msg = "Somehow `player_slot` is None in match history match"
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
            friend_id,
            match.id,
            match.hero.id,
            is_radiant,
            match.abandon,
        )

    @ireloop(hours=3)
    async def fill_completed_matches_from_gc_match_history(self) -> None:
        """A backup task to double check if we haven't missed any games.

        Useful to keep W-L as precise as possible.
        """
        for friend in self.friends.values():
            for match in await friend.steam_user.match_history():
                await self.add_completed_match_to_database(match, friend.steam_user.id)

    @ireloop(hours=6)
    async def remove_way_too_old_matches(self) -> None:
        """Clean the database from way too old matches.

        Currently, 48 hours is considered as "too old".
        """
        # if self.remove_way_too_old_matches.current_loop == 0:
        #     # No need to bother on bot reloads.
        #     return

        log.debug("Removing way too old matches from the database.")
        query = """
            DELETE FROM ttv_dota_completed_matches
            WHERE start_time < $1;
        """
        await self.bot.pool.execute(query, datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=48))

    @ireloop(seconds=20)
    async def process_pending_matches(self) -> None:
        """Process pending matches."""
        log.debug("Processing pending matches.")
        for friend_id, pending_matches in self.pending_matches.items():
            friend = self.bot.dota.get_user(friend_id)
            if friend:
                match_history = await friend.match_history()
            else:
                match_history = await self.bot.dota.create_partial_user(friend_id).match_history()
            for match in match_history:
                if match.id in pending_matches:
                    await self.add_completed_match_to_database(match, friend_id)
                    pending_matches.remove(match.id)
            if pending_matches:
                log.debug("Still pending matches for @%s: %s", friend.name if friend else friend_id, pending_matches)
            else:
                self.pending_matches.pop(friend_id)

        if not self.pending_matches:
            self.process_pending_matches.stop()

    #################################
    #    FRIEND PROFILE COMMANDS    #
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

        # Example: {my_friend_id: {ScoreCategory.Ranked: [0, 4, 1], ScoreCategory.Unranked: [0, 0, 0]}}
        # So !wl should return Ranked 0 W - 4 L, 1 Abandon.
        # Notice the order!!
        index: dict[int, dict[dota_enums.ScoreCategory, list[int]]] = {}

        cutoff_dt = datetime.datetime.now(datetime.UTC)
        for row in rows:
            # Let's assume gaming sessions to be separated by 6 hours from each other;
            if row["start_time"] < cutoff_dt - datetime.timedelta(hours=6):
                break
            cutoff_dt = row["start_time"]

            score_category = dota_enums.ScoreCategory.create(row["lobby_type"], row["game_mode"])
            scores = index.setdefault(row["friend_id"], {}).setdefault(score_category, [0, 0, 0])

            if row["outcome"] in (MatchOutcome.RadiantVictory, MatchOutcome.DireVictory):
                # Normal Win Loss scenario
                win = (
                    row["outcome"] == MatchOutcome.RadiantVictory
                    if row["is_radiant"]
                    else row["outcome"] == MatchOutcome.DireVictory
                )
                scores[int(win)] += 1
            elif row["abandon"]:
                scores[2] += 1

        def format_results(results: list[int]) -> str:
            abandons = f", Abandons: {a}" if (a := results[2]) else ""
            return f"{results[1]} W - {results[0]} L" + abandons

        response_parts = {
            friend_id: " \N{BULLET} ".join(
                [f"{category.name} {format_results(results)}" for category, results in scores.items()]
                + ([f"Pending: {len(pm)} Match(-es)"] if (pm := self.pending_matches.get(friend_id)) else [])
            )
            for friend_id, scores in index.items()
        }
        if len(index) == 0:
            return "0 W - 0 L"
        return " | ".join(
            # Let's make extra query to know name accounts
            f"{u.name if (u := self.bot.dota.get_user(friend_id)) else friend_id}: {part}"
            for friend_id, part in response_parts.items()
        )

    @commands.group(aliases=["wl", "winloss"], invoke_fallback=True)
    async def score(self, ctx: IreContext) -> None:
        """Show streamer's Win - Loss score ratio during the stream."""
        streamer = self.bot.streamers[ctx.broadcaster.id]
        if not streamer.online:
            response = 'Streamer offline (to get their offline winloss use "!wl offline")'
        else:
            response = await self.score_response_helper(ctx.broadcaster.id, streamer.started_dt)
        await ctx.send(content=response)

    @score.command()
    async def offline(self, ctx: IreContext) -> None:
        """Show streamer's Win - Loss score ratio during their last gaming session.

        Unlike !wl without any argument - this command counts games that were played off stream.
        Note that for both commands a "gaming session" is considered to be broken if there was a 6 hours break between
        their Dota 2 matches.
        """
        response = await self.score_response_helper(ctx.broadcaster.id)
        await ctx.send(content=response)

    @commands.group(invoke_fallback=True)
    async def mmr(self, ctx: IreContext) -> None:
        """Show streamer's mmr on the current account."""
        friend = await self.find_friend_account(ctx.broadcaster.id, is_green_online_required=False)
        query = """
            SELECT estimated_mmr
            FROM ttv_dota_accounts
            WHERE friend_id = $1;
        """
        mmr: int = await self.bot.pool.fetchval(query, friend.steam_user.id)

        profile_card = await friend.steam_user.dota2_profile_card()
        response = f"Medal: {dota_utils.rank_medal_display_name(profile_card)} \N{BULLET} Database tracked MMR: {mmr}"
        await ctx.send(response)

    @commands.is_broadcaster()
    @mmr.command(name="set")
    async def mmr_set(self, ctx: IreContext, new_mmr: int) -> None:
        """#TODO."""
        friend = await self.find_friend_account(ctx.broadcaster.id, is_green_online_required=False)
        query = """
            UPDATE ttv_dota_accounts
            SET estimated_mmr = $1
            WHERE friend_id = $2;
        """
        await self.bot.pool.fetchval(query, new_mmr, friend.steam_user.id)
        response = f'Successfully set MMR to {new_mmr} for the account "{friend.steam_user.name}"'
        await ctx.send(response)

    @commands.command(aliases=["stratz", "opendota"])
    async def dotabuff(self, ctx: IreContext) -> None:
        """Show stats service profile link for the streamer, i.e. dotabuff / stratz / opendota."""
        friend = await self.find_friend_account(ctx.broadcaster.id, is_green_online_required=False)
        if not (invoked := ctx.invoked_with):
            invoked = "stratz"
        await ctx.send(content=f"{invoked}.com/players/{friend.steam_user.id}")

    @commands.command(name="lastseen")
    async def last_seen(self, ctx: IreContext) -> None:
        """Show the steam account the bot has seen you last online on.

        This account is considered to be queried against for the bot's commands.
        """
        friend = await self.find_friend_account(ctx.broadcaster.id, is_green_online_required=False)
        query = "SELECT last_seen FROM ttv_dota_accounts WHERE friend_id = $1"
        last_seen: datetime.datetime = await self.bot.pool.fetchval(query, friend.steam_user.id)
        delta = datetime.datetime.now(datetime.UTC) - last_seen
        response = (
            f"{friend.steam_user.name} id={friend.steam_user.id} status={friend.rich_presence.status} - "
            f"last seen green online in Dota 2 {fmt.timedelta_to_words(delta, fmt=fmt.TimeDeltaFormat.Letter)} ago"
        )
        await ctx.send(response)

    #################################
    #       DEV ONLY COMMANDS       #
    #################################

    @commands.is_owner()
    @commands.group(name="notable-dev", invoke_fallback=True)
    async def notable_dev(self, ctx: IreContext) -> None:
        """A group command for the bot developer to manage list of notable players in the database."""
        await ctx.send(
            '"!notable-dev" is a group command: use it together with its subcommands, i.e. "!notable_dev add 123 Arteezy"'
        )

    # Remember, group guards apply to children.
    @notable_dev.command(name="add", aliases=["edit"])
    async def notable_dev_add(
        self, ctx: IreContext, steam_user: Annotated[Dota2User, SteamUserConverter], *, name: str
    ) -> None:
        """Add a notable player to the database."""
        query = """
            INSERT INTO ttv_dota_notable_players
            (friend_id, nickname)
            VALUES ($1, $2)
            ON CONFLICT (friend_id) DO
                UPDATE SET nickname = $2;
        """
        await self.bot.pool.execute(query, steam_user.id, name)
        await ctx.send(f"Added a new notable player (friend_id={steam_user.id}, name={name})")

    #################################
    #         TASK CARE             #
    #################################

    @ireloop(count=1)
    async def add_steam_user_update_listener(self) -> None:
        """A crutch task to add `steam_user_update` listener after all the clients are ready."""
        self.bot.add_listener(self.steam_user_update, event="event_steam_user_update")

    @add_steam_user_update_listener.before_loop
    @starting_fill_friends.before_loop
    async def wait_for_clients(self) -> None:
        """Wait for all the needed clients to get ready.

        Otherwise, such things as Dota 2 Coordinator requests are going to error out.
        Unfortunately, specifically, Dota 2 Coordinator usually takes ~30 seconds to get ready.
        """
        await self.bot.wait_until_ready()
        await self.bot.dota.wait_until_ready()
        await self.bot.dota.wait_until_gc_ready()
        await self.bot._streamers_index_ready.wait()

    @fill_completed_matches_from_gc_match_history.before_loop
    @remove_way_too_old_matches.before_loop
    async def wait_for_friends_index_as_well(self) -> None:
        """Extra waiting for friends index to get filled with initial data.

        This calls `.wait_for_clients` which also waits for all the required clients to be ready.
        """
        await self.wait_for_clients()
        await self.bot._friends_index_ready.wait()


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(GameFlow(bot))
