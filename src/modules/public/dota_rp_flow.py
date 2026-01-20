from __future__ import annotations

import asyncio
import datetime
import functools
import itertools
import logging
import pprint
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Annotated, Any, TypedDict, override
from urllib import parse as url_parse

import orjson
import steam
from steam.ext.dota2 import GameMode, Hero, LobbyType, MatchOutcome, MinimalMatch, User as Dota2User
from twitchio.ext import commands

from config import config
from core import IrePublicComponent, ireloop
from utils import const, errors, fmt, fuzzy, guards
from utils.dota import constants as dota_constants, enums as dota_enums, utils as dota_utils

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from steam.ext.dota2 import MatchHistoryMatch, User as Dota2SteamUser

    from core import IreBot, IreContext
    from utils.dota import SteamUserUpdate
    from utils.dota.schemas import opendota, steam_web_api

    type ActiveMatch = PlayMatch | WatchMatch | UnsupportedMatch

    class ScoreQueryRow(TypedDict):
        friend_id: int
        start_time: datetime.datetime
        lobby_type: int
        game_mode: int
        outcome: int | None
        player_slot: int
        abandon: bool

    class NotablePlayersQueryRow(TypedDict):
        friend_id: int
        nickname: str

    class PendingAbandonsQueryRow(TypedDict):
        friend_id: int
        match_id: int
        outcome: int
        lobby_type: int
        player_slot: int


__all__ = ("Dota2RichPresenceFlow",)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@dataclass
class Score:
    wins: int
    losses: int
    abandons: int
    pending: int


@dataclass(slots=True)
class Activity:
    """Activity.

    Dev Note
    --------
    * I'm not sure if I like this implementation.
        Maybe we need to combine Play Watch Match with this and combine all the classes?
    """


@dataclass(slots=True)
class SomethingIsOff(Activity): ...


@dataclass(slots=True)
class Dashboard(Activity): ...


@dataclass(slots=True)
class Playing(Activity):
    watchable_game_id: str


@dataclass(slots=True)
class Watching(Activity):
    watching_server: str


@dataclass(slots=True)
class DemoMode(Activity): ...


@dataclass(slots=True)
class BotMatch(Activity): ...


@dataclass(slots=True)
class Replay(Activity): ...


@dataclass(slots=True)
class PrivateLobby(Activity): ...


@dataclass(slots=True)
class CustomGames(Activity): ...


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
        self._bot: IreBot = bot
        self.steam_user: Dota2SteamUser = steam_user
        self.rich_presence: RichPresence = RichPresence(steam_user.rich_presence)
        self.active_match: PlayMatch | WatchMatch | UnsupportedMatch | None = None
        self.activity: Activity = SomethingIsOff()

    @override
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name="{self.steam_user.name}" id={self.steam_user.id}>'

    @property
    def is_playing_dota(self) -> bool:
        """Whether this friend is playing dota or not."""
        return bool(app := self.steam_user.app) and app.id == 570


@dataclass
class Player:
    """A class representing an active Dota 2 match player.

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
        """A condition to check whether match player data is filled properly."""
        return bool(self.game_mode) and len(self.players) == 10

    def _is_heroes_data_ready(self) -> bool:
        """A condition to check whether match hero data is filled properly."""
        return bool(self.heroes) and all(bool(hero) for hero in self.heroes)

    @format_match_response
    async def game_medals(self) -> str:
        """Response for !gm command."""
        if not self.players:
            return "No players data yet."

        response_parts = [
            f"{hero if hero else player.color} {player.medal or '?'}"
            for player, hero in zip(self.players, self.heroes, strict=True)
        ]
        return " \N{BULLET} ".join(response_parts)  # [:5]) + " VS " + ", ".join(response_parts[5:])

    @format_match_response
    async def ranked(self) -> str:
        """Response for !ranked command."""
        if not self.lobby_type or not self.game_mode:
            return "No lobby data yet."

        yes_no = "Yes" if self.lobby_type == LobbyType.Ranked else "No"
        return f"{yes_no}, it's {self.lobby_type.display_name} ({self.game_mode.display_name})"

    @format_match_response
    async def smurfs(self) -> str:
        """Response for !smurfs command."""
        if not self.players:
            return "No players data yet."

        response_parts = [
            f"{hero if hero else player.color} {player.lifetime_games}"
            for player, hero in sorted(
                zip(self.players, self.heroes, strict=True),
                key=lambda x: attrgetter("lifetime_games")(x[0]),
            )
        ]
        return "Lifetime Games: " + " \N{BULLET} ".join(response_parts)

    def convert_argument_to_player_slot(self, argument: str) -> int:
        """Convert command argument provided by user (twitch chatter) into a player_slot in the match.

        It supports
        * player slot as digits;
        * player colors;
        * hero aliases (which include hero localized names, abbreviations and some common nicknames);
        """
        if argument.isdigit():
            # then the user typed only a number and our life is easy because it is a player slot
            player_slot = int(argument) - 1
            if not 0 <= player_slot <= 9:
                msg = "Sorry, player_slot can only be of 1-10 values."
                raise errors.RespondWithError(msg)
            return player_slot

        # Otherwise - we have to use the fuzzy search

        # Step 1. Colors;
        player_slot_choice = (None, 0)
        for player_slot, color_aliases in dota_constants.COLOR_ALIASES.items():
            find = fuzzy.extract_one(argument, color_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
            if find and find[1] > player_slot_choice[1]:
                player_slot_choice = (player_slot, find[1])

        # Step 2. let's see if hero aliases can beat official
        hero_slot_choice = (None, 0)
        # Sort the hero list so heroes in the match come first (i.e. so "es" alias triggers on a hero in the match)
        for hero, hero_aliases in sorted(
            dota_constants.HERO_ALIASES.items(), key=lambda x: x[0] in self.heroes, reverse=True
        ):
            find = fuzzy.extract_one(argument, hero_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
            if find and find[1] > hero_slot_choice[1]:
                hero_slot_choice = (hero, find[1])

        error_message = 'Sorry, didn\'t understand your query. Try something like "PA / 7 / Phantom Assassin / Blue".'
        if player_slot_choice[1] > hero_slot_choice[1]:
            # then color matched better
            player_slot = player_slot_choice[0]
            if player_slot is None:
                raise errors.RespondWithError(error_message)
        else:
            # hero aliases matched better;
            hero = hero_slot_choice[0]
            if hero is None:
                raise errors.RespondWithError(error_message)

            try:
                player_slot = self.heroes.index(hero)
            except ValueError:
                msg = f"Hero {hero} is not present in the match."
                raise errors.RespondWithError(msg) from None
        return player_slot

    @format_match_response
    async def profile(self, argument: str) -> str:
        """Response for !profile command."""
        if not self.players:
            return "No player data yet."

        player_slot = self.convert_argument_to_player_slot(argument)
        return f"{self.heroes[player_slot]} stratz.com/players/{self.players[player_slot].friend_id}"

    async def get_real_time_stats(self) -> steam_web_api.RealTimeStatsResponse:
        """Get Real Time Stats from Steam Web API.

        Disclaimer
        ----------
        For some reason, `pulsefire` clients are erroring out for this.
        Maybe, worth investigating.
        """
        for _ in range(5):
            url = (
                "https://api.steampowered.com//IDOTA2MatchStats_570/GetRealtimeStats/v1/"
                f"?key={config['TOKENS']['STEAM']}"
                f"&server_steam_id={self.server_steam_id}"
            )
            async with self.bot.session.get(url=url) as resp:
                # encoding='utf-8' errored out one day
                match = await resp.json(loads=orjson.loads, encoding="ISO-8859-1")
            if match:
                break
            # Sometimes it returns an empty dict `{}` (especially on the very first request)
            await asyncio.sleep(0.69)
            continue
        else:
            msg = "get_real_time_stats got an empty dict 5 times in a row"
            raise errors.PlaceholderError(msg)

        return match

    @format_match_response
    async def stats(self, argument: str) -> str:
        """Response for !stats command."""
        if not self.players:
            return "No player data yet."
        if self.server_steam_id is None:
            return "This match doesn't support real time stats"
        if self.lobby_type == LobbyType.NewPlayerMode:
            return "New Player Mode matches do not support real time stats."

        player_slot = self.convert_argument_to_player_slot(argument)

        match = await self.get_real_time_stats()

        team_ord = int(player_slot > 4)  # team_ord = 0 for Radiant, 1 for Dire
        team_slot = player_slot - 5 * team_ord  # 0 1 2 3 4 for Radiant, 5 6 7 8 9 for Dire
        api_player = match["teams"][team_ord]["players"][team_slot]

        prefix = f"[2m delay] {api_player['name']} {Hero.try_value(api_player['heroid'])} lvl {api_player['level']}"
        net_worth = f"NW: {api_player['net_worth']}"
        kda = f"{api_player['kill_count']}/{api_player['death_count']}/{api_player['assists_count']}"
        cs = f"CS: {api_player['lh_count']}"

        items = ", ".join([str(await self.bot.dota.items.by_id(item)) for item in api_player["items"] if item != -1])
        response_parts = (prefix, net_worth, kda, cs, items)
        return " \N{BULLET} ".join(response_parts)

    @format_match_response
    async def lead(self) -> str:
        """Response for !lead command."""
        match = await self.get_real_time_stats()
        radiant = match["teams"][0]
        dire = match["teams"][1]

        lead = radiant["net_worth"] - dire["net_worth"]
        word = "Radiant" if lead > 0 else "Dire"

        return f"[2m delay] Radiant {radiant['score']} - Dire {dire['score']}: {word} is leading by {abs(lead) / 1000:.1f}k"

    @format_match_response
    async def match_id_command(self) -> str:
        """Response for !match_id command."""
        return str(self.match_id)

    @format_match_response
    async def notable_players(self) -> str:
        """Response for !notable command."""
        if not self.players:
            return "No player data yet."

        query = """
            SELECT friend_id, nickname
            FROM ttv_dota_notable_players
            WHERE friend_id = ANY($1);
        """
        rows: list[NotablePlayersQueryRow] = await self.bot.pool.fetch(query, [p.friend_id for p in self.players])
        if not rows:
            return "No notable players found"

        nickname_mapping = {row["friend_id"]: row["nickname"] for row in rows}

        response_parts = [
            f"{nick} as {hero if hero else player.color}"
            for player, hero in zip(self.players, self.heroes, strict=True)
            if (nick := nickname_mapping.get(player.friend_id))
        ]
        return " \N{BULLET} ".join(response_parts)

    @format_match_response
    async def server_steam_id_command_response(self) -> str:
        """Command response for !server_steam_id."""
        return str(self.server_steam_id)


class PlayMatch(Match):
    def __init__(self, bot: IreBot, watchable_game_id: str) -> None:
        super().__init__(bot)
        self.watchable_game_id: str = watchable_game_id
        self.lobby_id: int = int(watchable_game_id)

        self.average_mmr: int | None = None

        self.update_data.start()

    @override
    def __hash__(self) -> int:
        return self.match_id or super().__hash__()

    @ireloop(seconds=10.1, count=30)
    async def update_data(self) -> None:
        log.debug('Updating %s data for watchable_game_id "%s"', self.__class__.__name__, self.watchable_game_id)
        match = next(iter(await self.bot.dota.live_matches(lobby_ids=[self.lobby_id])), None)
        if not match:
            msg = f'FindTopSourceTVGames did not find watchable_game_id "{self.watchable_game_id}".'
            raise errors.PlaceholderError(msg)

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
            # add to the database
            query = """
                INSERT INTO ttv_dota_matches
                (match_id, start_time, lobby_type, game_mode)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (match_id) DO NOTHING;
            """
            await self.bot.pool.execute(query, self.match_id, match.start_time, self.lobby_type, self.game_mode)
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
            f"{hero if hero else player.color} played as {last_game_played_as}"
            for player, hero in zip(self.players, self.heroes, strict=True)
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
        match = await self.get_real_time_stats()
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
    """A class describing unsupported matches.

    All chat commands for objects of this type should return unsupported message response.
    For example, if streamer is playing Demo Mode, then the bot should only respond with "Demo Mode is not supported",
    because, well, there is no data in Demo Mode to insect.
    """

    def __init__(self, bot: IreBot, tag: str = "") -> None:
        super().__init__(bot, tag)


class SteamUserNotFound(commands.BadArgument):
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
                raise SteamUserNotFound(argument) from None
            return await ctx.bot.dota.fetch_user(id64)
        except TimeoutError:
            raise SteamUserNotFound(argument) from None


def is_allowed_to_add_notable() -> Any:
    """Allow !np add to only be invoked by certain people."""

    def predicate(ctx: IreContext) -> bool:
        # Maybe we will edit this to be some proper dynamic database thing;
        allowed_ids = (const.UserID.Irene, const.UserID.Aluerie, const.UserID.Xas)
        return ctx.chatter.id in allowed_ids

    return commands.guard(predicate)


class Dota2RichPresenceFlow(IrePublicComponent):
    """Component with all 9kmmrbot-like Dota 2 features.

    This component uses Dota 2 Rich Presence (RP), Dota 2 web API and Dota 2 Game Coordinator (GC) API calls
    to figure out current state of each friend in the bot's steam friend list.
    If they are currently playing - the bot activates special chat commands inspecting their live match.
    The bot also stores some match history information in the database for some features/commands to use.

    Notes
    -----
    * The restrictions of such approach are
            1. Streamers have to add the bot into their friend list;
            2. Streamers have to play Dota 2 while being green-online in steam;
        The other solution that would solve these problems would be using Dota 2 Game State Integration (GSI),
        which I'm going to implement one day.
    """

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)
        self.friends: dict[int, Friend] = {}

        self.play_matches_index: dict[str, PlayMatch] = {}
        self.watch_matches_index: dict[str, WatchMatch] = {}

        self.debug: bool = True

    @override
    async def component_load(self) -> None:
        self.starting_fill_friends.start()
        self.add_steam_user_update_listener.start()
        self.fill_completed_matches_from_gc_match_history.start()
        self.remove_way_too_old_matches.start()
        self.debug_announce_gc_ready.start()

    @override
    async def component_teardown(self) -> None:
        self.starting_fill_friends.cancel()
        self.add_steam_user_update_listener.cancel()
        self.fill_completed_matches_from_gc_match_history.cancel()
        self.remove_way_too_old_matches.cancel()
        self.debug_announce_gc_ready.cancel()

    #################################
    #           EVENTS              #
    #################################

    @ireloop(count=1)
    async def starting_fill_friends(self) -> None:
        """Index bot's friend list on bot's startup.

        Also makes initial analyse of their rich presences.
        """
        log.debug("Indexing bot's friend list.")
        for friend in await self.bot.dota.user.friends():
            self.friends[friend.id] = Friend(self.bot, friend._user)  # pyright: ignore[reportArgumentType]

        for friend in self.friends.values():
            await self.analyze_rich_presence(friend)

        log.debug('Friends index ready. Setting "_friends_index_ready".')
        self.bot._friends_index_ready.set()

    async def get_activity(self, friend: Friend) -> Activity:
        """Get Activity."""
        rp = friend.rich_presence

        # Dashboard
        if rp.status in {dota_enums.Status.Idle, dota_enums.Status.MainMenu, dota_enums.Status.Finding}:
            return Dashboard()

        # Playing somewhere
        if rp.status in {
            dota_enums.Status.WaitingToLoad,
            dota_enums.Status.HeroSelection,
            dota_enums.Status.Strategy,
            dota_enums.Status.Playing,
        }:
            if (watchable_game_id := rp.raw.get("WatchableGameID")) is None:
                # something is off
                lobby_param0 = rp.raw.get("param0") or "_missing"
                lobby_map: dict[str, Activity] = {
                    dota_enums.LobbyParam0.DemoMode: DemoMode(),
                    dota_enums.LobbyParam0.BotMatch: BotMatch(),
                }
                return lobby_map.get(lobby_param0, SomethingIsOff())

            if watchable_game_id == "0":
                # something is off again
                # usually this happens when a player has just quit the match into the main menu
                # the status flickers for a few seconds to be `watchable_game_id=0`
                return SomethingIsOff()
            return Playing(watchable_game_id)

        # Watching
        if rp.status in {dota_enums.Status.Spectating, dota_enums.Status.WatchingTournament}:
            watching_server = rp.raw.get("watching_server")
            if watching_server is None:
                return Replay()
            return Watching(watching_server)

        if rp.status == dota_enums.Status.BotPractice:
            return DemoMode()

        # Private Lobby
        if rp.status == dota_enums.Status.PrivateLobby:
            return PrivateLobby()

        # Custom games
        if rp.status == dota_enums.Status.CustomGame:
            return CustomGames()

        if rp.status == dota_enums.Status.NoStatus:
            # usually this happens in exact moment when the player closes Dota
            return SomethingIsOff()

        # Unrecognized
        text = (
            f"Uncategorized Rich Presence Status \n"
            f"friend=`{friend!r}`\n"
            f"status=`{rp.status.value}`\n"
            "rich_presence.raw="
            f"```json\n{pprint.pformat(rp.raw)}```"
        )
        log.warning(text)
        await self.bot.error_webhook.send(content=self.bot.error_ping + "\n" + text)

        return SomethingIsOff()

    async def analyze_rich_presence(self, friend: Friend) -> None:
        """Analyze Rich Presence.

        Central function for this component.
        The bot tries its best to track friend's gameflow via inspecting their rich presence.
        If the bot detects a new game being played or watched - it will do necessary actions to
        prepare those matches for further inspection.

        Warning
        -------
        The code in this function is also quite volatile. Valve are quite inconsistent in their Rich Presence data,
        so the logic might break any day.
        """
        if friend.is_playing_dota:
            # Update `last_seen` in the database;
            query = """
                UPDATE ttv_dota_accounts
                SET last_seen = $1
                WHERE friend_id = $2;
            """
            await self.bot.pool.execute(query, datetime.datetime.now(datetime.UTC), friend.steam_user.id)
        else:
            # not interested if not playing Dota 2
            await self.conclude_friend_match(friend)
            return

        new_activity = await self.get_activity(friend)
        if friend.activity != new_activity:
            friend.activity = new_activity
        else:
            # no activity changes = no need to do anything
            return

        match new_activity:
            case Dashboard():
                await self.conclude_friend_match(friend)
            case Playing():
                # Friend is in a match as a player
                if (w_id := new_activity.watchable_game_id) not in self.play_matches_index:
                    self.play_matches_index[w_id] = PlayMatch(self.bot, w_id)
                friend.active_match = self.play_matches_index[w_id]
            case Watching():
                if (w_s := new_activity.watching_server) not in self.watch_matches_index:
                    self.watch_matches_index[w_s] = WatchMatch(self.bot, w_s)
                friend.active_match = self.watch_matches_index[w_s]
            case DemoMode():
                friend.active_match = UnsupportedMatch(self.bot, tag="Demo mode is not supported")
            case BotMatch():
                friend.active_match = UnsupportedMatch(self.bot, tag="Bot matches are not supported")
            case Replay():
                friend.active_match = UnsupportedMatch(self.bot, tag="Data in watching replays is not supported")
            case PrivateLobby():
                friend.active_match = UnsupportedMatch(
                    self.bot, tag="Private lobbies (this includes draft in public lobbies) are not supported"
                )
            case CustomGames():
                friend.active_match = UnsupportedMatch(self.bot, tag="Custom Games are not supported")
            case SomethingIsOff():
                # Wait for confirmed statuses
                return
            case _:
                # Wait for confirmed statuses
                return

    # @commands.Component.listener("steam_user_update")
    async def steam_user_update(self, update: SteamUserUpdate) -> None:
        """Called when bot's steam friend profile is updated.

        For example, this component is interested in Rich Presence changes.

        Note
        ----
        This is not `@commands.Component.listener("steam_user_update")` because we have to manually
        `.add_listener` for this function after waiting for all the clients to start.
        """
        rp_before = RichPresence(update.before.rich_presence)
        rp_after = RichPresence(update.after.rich_presence)

        if rp_before == rp_after:
            return

        friend = self.friends.setdefault(update.after.id, Friend(self.bot, update.after))
        friend.rich_presence = rp_after
        log.debug("Recognized rich presence update for %s: %s", repr(friend), repr(friend.rich_presence))
        await self.analyze_rich_presence(friend)

    async def conclude_friend_match(self, friend: Friend) -> None:
        """Conclude match as finished for a friend.

        This nulls `Friend.active_match` attribute as well as adds the match into the database
        if it's a play match.
        """
        if (match := friend.active_match) and isinstance(match, PlayMatch) and match.match_id:
            player_slot = next(iter(s for (s, p) in enumerate(match.players) if p.friend_id == friend.steam_user.id), None)
            if player_slot is None:
                msg = "Somehow `player_slot` is `None` in `conclude_friend_match`"
                raise errors.PlaceholderError(msg)
            hero = match.heroes[player_slot]
            query = """
                INSERT INTO ttv_dota_match_players
                (friend_id, match_id, hero_id, player_slot)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (friend_id, match_id) DO NOTHING;
            """
            await self.bot.pool.execute(query, friend.steam_user.id, match.match_id, hero.id, player_slot)

            if not self.process_pending_matches.is_running():
                self.process_pending_matches.start()

        friend.active_match = None

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
                raise errors.RespondWithError(msg)
            return friend

        if not self.bot._friends_index_ready.is_set():
            msg = "Bot is restarting. Dota 2 features are not ready yet. Please, wait a bit."
            raise errors.RespondWithError(msg)

        msg = "Couldn't find streamer's steam account in my friends uuh"
        raise errors.RespondWithError(msg)

    async def find_active_match(self, broadcaster_id: str) -> ActiveMatch:
        """Find broadcaster's active match."""
        friend = await self.find_friend_account(broadcaster_id)

        active_match = friend.active_match
        if not active_match:
            msg = f"No Active Game Found \N{BULLET} Streamer's status: {friend.rich_presence.status}"
            raise errors.RespondWithError(msg)

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

    @commands.command(aliases=["items", "kda"])
    async def stats(self, ctx: IreContext, *, argument: str) -> None:
        """Fetch items and some profile data about a certain player in the game.

        `argument` can be a hero name, hero alias, player slot or colour.
        """
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.stats(argument)
        await ctx.send(response)

    @commands.command(aliases=["player"])
    async def profile(self, ctx: IreContext, *, argument: str) -> None:
        """Get a link to player stats profile.

        `argument` can be a hero name, hero alias, player slot or colour.
        """
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.profile(argument)
        await ctx.send(response)

    @stats.error
    async def stats_error(self, payload: commands.CommandErrorPayload) -> None:
        """Error for !stats argument."""
        if isinstance(payload.exception, commands.MissingRequiredArgument):
            await payload.context.send(
                "You need to provide a hero name (i.e. VengefulSpirit , PA, Mireska, etc) or "
                "player slot (i.e. 9, DarkGreen )",
            )
        else:
            raise payload.exception

    @commands.command()
    async def lead(self, ctx: IreContext) -> None:
        """Show which team has a gold lead and by how much."""
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.lead()
        await ctx.send(response)

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
            FROM ttv_dota_matches m
            JOIN ttv_dota_match_players p ON m.match_id = p.match_id
            JOIN ttv_dota_accounts a ON a.friend_id = p.friend_id
            WHERE a.twitch_id = $1
            ORDER BY m.start_time DESC
            LIMIT 1;
        """
        row = await self.bot.pool.fetchrow(query, broadcaster_id)
        if not row:
            msg = "No last game found: streamer hasn't played Dota 2 in the last 2 days"
            raise errors.RespondWithError(msg)
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
            raise errors.PlaceholderError(msg)

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

    async def update_mmr(self, *, friend_id: int, lobby_type: int, player_slot: int, outcome: int, is_abandon: bool) -> None:
        """Update MMR for friend under friend_id."""
        if lobby_type != LobbyType.Ranked:
            return
        if outcome >= MatchOutcome.NotScoredPoorNetworkConditions:
            return

        if is_abandon:
            mmr_delta = -25
        elif outcome == MatchOutcome.RadiantVictory:
            mmr_delta = 25 if player_slot < 5 else -25
        elif outcome == MatchOutcome.DireVictory:
            mmr_delta = 25 if player_slot > 4 else -25
        else:
            mmr_delta = 0

        if mmr_delta:
            query = """
                UPDATE ttv_dota_accounts
                SET estimated_mmr = estimated_mmr + $1
                WHERE friend_id = $2;
            """
            await self.bot.pool.execute(query, mmr_delta, friend_id)

    async def add_completed_match_to_database(self, match: MatchHistoryMatch, friend_id: int) -> None:
        """Add matches from match history check loop into the database.

        Development Notes
        -----------------
        * We use match history endpoint specifically
        """
        if match.start_time < datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=48):
            # Match is way too old to care
            return

        # match history entities on their own do not give proper outcome (Radiant/Dire)
        minimal = await self.bot.dota.create_partial_match(match.id).minimal()

        query = """
            INSERT INTO ttv_dota_matches
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
        player_slot = next((slot for slot, player in enumerate(minimal.players) if player.hero == match.hero), None)
        if player_slot is None:
            msg = "Somehow `player_slot` is `None` in match history match"
            raise errors.PlaceholderError(msg)

        if match_id is not None:
            # if it's None - then it already was in the database
            # otherwise it's a new match and we can explore mmr_delta
            # MMR Tracking
            await self.update_mmr(
                friend_id=friend_id,
                lobby_type=match.lobby_type,
                player_slot=player_slot,
                outcome=minimal.outcome,
                is_abandon=match.abandon,
            )

        query = """
            INSERT INTO ttv_dota_match_players
            (friend_id, match_id, hero_id, player_slot, abandon)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (friend_id, match_id) DO
                UPDATE SET abandon = $5;
        """
        await self.bot.pool.execute(
            query,
            friend_id,
            match.id,
            match.hero.id,
            player_slot,
            match.abandon,
        )

    @ireloop(hours=1)
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
            DELETE FROM ttv_dota_matches
            WHERE start_time < $1;
        """
        await self.bot.pool.execute(query, datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=48))

    @ireloop(seconds=20)
    async def process_pending_matches(self) -> None:
        """Process pending matches.

        Development Notes
        -----------------
        * We use match history endpoint specifically because it has `.abandon` attribute.
            So if we remove that quirk - we can probably be fine with just "minimal_match" data.
        * Another option is to use opendota api (stratz is too slow -
            they don't allow access to data until full parse is done)
        """
        log.debug("Processing pending matches.")

        query = """
            SELECT match_id
            FROM ttv_dota_matches
            WHERE outcome IS NULL;
        """
        rows = await self.bot.pool.fetch(query)
        if not rows:
            # I guess no pending matches left
            self.process_pending_matches.cancel()
            return

        for row in rows:
            minimal = await self.bot.dota.create_partial_match(row["match_id"]).minimal()
            query = """
                UPDATE ttv_dota_matches
                SET outcome = $1
                WHERE match_id = $2;
            """
            await self.bot.pool.execute(query, minimal.outcome, row["match_id"])

    async def get_match_from_opendota(self, match_id: int) -> opendota.Match:
        """Get match from opendota API via GET matches endpoint."""
        url = f"https://api.opendota.com/api/matches/{match_id}"
        async with self.bot.session.get(url=url) as resp:
            return await resp.json(loads=orjson.loads)

    @ireloop(seconds=20)
    async def process_pending_abandons(self) -> None:
        """Process pending abandons.

        This task is separate from pending matches due to fetching matches from opendota.
        """
        query = """
            SELECT p.match_id, p.friend_id, p.player_slot, m.outcome, m.lobby_type
            FROM ttv_dota_match_players p
            JOIN ttv_dota_matches m ON m.match_id = p.match_id
            WHERE abandon IS NULL;
        """
        rows: list[PendingAbandonsQueryRow] = await self.bot.pool.fetch(query)
        if not rows:
            # I guess no pending matches left
            self.process_pending_abandons.cancel()
            return

        players_cache: dict[int, list[opendota.Player]] = {}

        for row in rows:
            players = players_cache.get(row["match_id"])
            if not players:
                match = await self.get_match_from_opendota(row["match_id"])
                try:
                    match["players"]
                except KeyError:
                    continue
                else:
                    players = match["players"]
                    players_cache[match["match_id"]] = match["players"]

            player = players[row["player_slot"]]
            is_abandon = bool(player["abandons"])
            query = """
                UPDATE ttv_dota_match_players
                SET abandon = $1
                WHERE match_id = $2 AND friend_id = $3;
            """
            await self.bot.pool.execute(query, is_abandon, row["match_id"], row["friend_id"])
            await self.update_mmr(
                friend_id=row["friend_id"],
                lobby_type=row["lobby_type"],
                player_slot=row["player_slot"],
                outcome=row["outcome"],
                is_abandon=is_abandon,
            )

    #################################
    #    FRIEND PROFILE COMMANDS    #
    #################################

    async def score_response_helper(self, broadcaster_id: str, stream_started_at: datetime.datetime | None = None) -> str:
        """Helper function to get !wl commands response."""
        clause = "AND m.start_time > $2" if stream_started_at else ""
        query = f"""
            SELECT d.friend_id, m.start_time, m.lobby_type, m.game_mode, m.outcome, p.player_slot, p.abandon
            FROM ttv_dota_matches m
            JOIN ttv_dota_match_players p ON m.match_id = p.match_id
            JOIN ttv_dota_accounts d ON d.friend_id = p.friend_id
            WHERE d.twitch_id = $1 {clause}
            ORDER BY m.start_time DESC;
        """
        if stream_started_at:
            rows: list[ScoreQueryRow] = await self.bot.pool.fetch(query, broadcaster_id, stream_started_at)
        else:
            rows: list[ScoreQueryRow] = await self.bot.pool.fetch(query, broadcaster_id)

        if not rows:
            return "0 W - 0 L" if stream_started_at else "0 W - 0 L (No games played in the last 2 days)"

        index: dict[int, dict[dota_enums.ScoreCategory, Score]] = {}

        cutoff_dt = rows[0]["start_time"]
        for row in rows:
            # Let's assume gaming sessions to be separated by 6 hours from each other;
            if row["start_time"] < cutoff_dt - datetime.timedelta(hours=6):
                break
            cutoff_dt = row["start_time"]

            score_category = dota_enums.ScoreCategory.create(row["lobby_type"], row["game_mode"])
            score = index.setdefault(row["friend_id"], {}).setdefault(score_category, Score(0, 0, 0, 0))

            if row["outcome"] == MatchOutcome.RadiantVictory:
                if row["player_slot"] < 5:
                    score.wins += 1
                else:
                    score.losses += 1
            elif row["outcome"] == MatchOutcome.DireVictory:
                if row["player_slot"] > 4:
                    score.wins += 1
                else:
                    score.losses += 1
            elif row["abandon"]:
                score.abandons += 1
            elif row["outcome"] is None:
                score.pending += 1

        def format_results(score: Score) -> str:
            wl = f"{score.wins} W - {score.losses} L"
            if a := score.abandons:
                wl += f", Abandons: {a}"
            if p := score.pending:
                wl += f", Pending: {p}"
            return wl

        response_parts = {
            friend_id: " \N{BULLET} ".join(
                f"{category.name} {format_results(results)}" for category, results in scores.items()
            )
            for friend_id, scores in index.items()
        }

        return " \N{LARGE PURPLE CIRCLE} ".join(
            # Let's make extra query to know name accounts
            f"{u.name if (u := self.bot.dota.get_user(friend_id)) else friend_id}: {part}"
            for friend_id, part in response_parts.items()
        )

    @commands.group(aliases=["wl", "winloss"], invoke_fallback=True)
    async def score(self, ctx: IreContext) -> None:
        """Show streamer's Win - Loss score ratio during the stream."""
        streamer = self.bot.streamers[ctx.broadcaster.id]
        if not streamer.online:
            response = f"Offline score - {await self.score_response_helper(ctx.broadcaster.id)}"
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
        """Set streamer's mmr in the database."""
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

    @commands.command(aliases=["lastseen"])
    async def status(self, ctx: IreContext) -> None:
        """Show the steam account the bot has seen you last online on.

        This account is considered to be queried against for the bot's commands.
        """
        friend = await self.find_friend_account(ctx.broadcaster.id, is_green_online_required=False)
        query = "SELECT last_seen FROM ttv_dota_accounts WHERE friend_id = $1"
        last_seen: datetime.datetime = await self.bot.pool.fetchval(query, friend.steam_user.id)
        delta = datetime.datetime.now(datetime.UTC) - last_seen
        response = (
            f"{friend.steam_user.name} id={friend.steam_user.id} status={friend.rich_presence.status} - "
            f"changed to it {fmt.timedelta_to_words(delta, fmt=fmt.TimeDeltaFormat.Letter)} ago "
            "(while being green-online in Dota 2)"
        )
        await ctx.send(response)

    @commands.command(name="d2pt")
    async def dota2protracker_hero_page(self, ctx: IreContext) -> None:
        """Show Dota 2 Pro Tracker page for the currently played hero."""
        friend = await self.find_friend_account(ctx.broadcaster.id)
        npc_hero_name = friend.rich_presence.raw.get("param2")
        if npc_hero_name:
            hero = Hero.create_from_npc_dota_hero_name(npc_hero_name.removeprefix("#"))
            response = url_parse.quote(f"dota2protracker.com/hero/{hero.display_name}")
        else:
            response = "The streamer has not picked a hero yet."
        await ctx.send(response)

    #################################
    # SPECIAL PEOPLE ONLY COMMANDS  #
    #################################

    # Remember, group guards apply to children.
    @is_allowed_to_add_notable()
    @guards.is_vps()
    @commands.group(name="npm", aliases=["np-dev"], invoke_fallback=True)
    async def npm_dev(self, ctx: IreContext) -> None:
        """A group command for the bot developer to manage list of notable players in the database."""
        await ctx.send('"!npm" is a group command: use it together with its subcommands, i.e. "!npm add 123 Arteezy"')

    @npm_dev.command(name="add", aliases=["edit"])
    async def npm_dev_add(self, ctx: IreContext, steam_user: Annotated[Dota2User, SteamUserConverter], *, name: str) -> None:
        """Add a notable player to the database.

        This command is only available for certain group of people.
        """
        query = """
            INSERT INTO ttv_dota_notable_players
            (friend_id, nickname)
            VALUES ($1, $2)
            ON CONFLICT (friend_id) DO
                UPDATE SET nickname = $2;
        """
        await self.bot.pool.execute(query, steam_user.id, name)
        await ctx.send(f"Added a new notable player <friend_id={steam_user.id}, name={name}>")

    @npm_dev.command(name="help")
    async def npm_dev_help(self, ctx: IreContext) -> None:
        """Show small help for !np-dev commands."""
        response = (
            'To add a notable player into the database - use "!npm add 123 Arteezy" \N{BULLET} '
            'To remove a player - use "!npm remove 123" where 123 is their friend_id.'
        )
        await ctx.send(response)

    @npm_dev.command(name="remove")
    async def npm_dev_remove(self, ctx: IreContext, friend_id: int) -> None:
        """Add a notable player to the database.

        This command is only available for certain group of people.
        """
        query = """
            DELETE FROM ttv_dota_notable_players
            WHERE friend_id = $1
            RETURNING nickname;
        """
        name: str = await self.bot.pool.fetchval(query, friend_id)
        await ctx.send(f"Removed player <friend_id={friend_id}, name={name}> from notable players.")

    #################################
    #          TASK CARE            #
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

    #################################
    #  MORE OR LESS DEBUG COMMANDS  #
    #################################

    async def debug_deliver(self, message: str) -> None:
        """Deliver a debug message directly to Irene's twitch channel.

        Idk, sometimes it's nice to have a direct twitch message for debug purposes.
        """
        if not self.debug:
            return

        partial_user = self.bot.create_partialuser(self.bot.owner_id)
        await partial_user.send_message(sender=self.bot.bot_id, message=f"[debug] {message}")

    @commands.command()
    async def server_steam_id(self, ctx: IreContext) -> None:
        """Show server steam id for the match.

        Useful if I want to manually request `GetRealTimeStats`.
        """
        active_match = await self.find_active_match(ctx.broadcaster.id)
        response = await active_match.server_steam_id_command_response()
        await ctx.send(content=response)

    @ireloop(count=1)
    async def debug_announce_gc_ready(self) -> None:
        """Announce in Irene's twitch chat that Dota 2 GC is ready."""
        await self.bot.dota.wait_until_gc_ready()
        await self.debug_deliver("Connection to Dota 2 Game Coordinator is ready")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Dota2RichPresenceFlow(bot))
