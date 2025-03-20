from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Self, override

from steam.enums import Enum, classproperty
from steam.ext.dota2 import GameMode, LobbyType, MatchOutcome

if TYPE_CHECKING:
    from collections.abc import Mapping

    from steam.ext.dota2 import MatchHistoryMatch, MatchMinimal


class Team(IntEnum):
    """Enum representing Dota 2 Team."""

    Radiant = MatchOutcome.RadiantVictory
    Dire = MatchOutcome.DireVictory


class PlayerMatchOutcome(IntEnum):
    Loss = 0
    Win = 1
    Abandon = 21
    NotScored = 66
    Other = 99

    @property
    def valid(self) -> bool:
        """Whether match properly ended and the result is properly scored: win or loss."""
        return self.value < 2  # hardcoded value, scary :o

    def mmr_change(self, lobby_type: int) -> int:
        if lobby_type == 7 and self.valid:
            # "2 * boolean - 1" is just a fancy way to do {true -> 1, false -> -1} mapping
            return (2 * self.value - 1) * 25
        return 0

    # @classmethod
    # def create(cls, minimal_match: MatchMinimal, bool: bool) -> PlayerMatchOutcome:

    # @classmethod
    # def create(cls, minimal_match: MatchMinimal, team: Team) -> PlayerMatchOutcome:
    #     outcome = minimal_match.outcome
    #     if outcome == MatchOutcome.RadiantVictory or outcome == MatchOutcome.DireVictory:
    #         return PlayerMatchOutcome(int(team == outcome))
    #     else:
    #         return PlayerMatchOutcome.Other

    @classmethod
    def create_from_history(cls, minimal_match: MatchMinimal, history_match: MatchHistoryMatch) -> PlayerMatchOutcome:
        if history_match.abandon:
            return PlayerMatchOutcome.Abandon
        outcome = minimal_match.outcome
        if outcome in {MatchOutcome.RadiantVictory, MatchOutcome.DireVictory}:
            return PlayerMatchOutcome(int(history_match.win))
        if minimal_match.outcome >= MatchOutcome.NotScoredPoorNetworkConditions:
            return PlayerMatchOutcome.NotScored
        return PlayerMatchOutcome.Other


class WinLossCategory(IntEnum):
    """Match categories for !winloss (!wl) command.

    The bot will group matches into !wl command by this parameter, i.e. !wl -> "Ranked 3 W - 1 L, Turbo 2 W - 0 L."
    """

    Ranked = 1
    Unranked = 2
    Turbo = 3
    NewPlayerMode = 4
    Other = 5

    @classmethod
    def create(cls, lobby_type: int, game_mode: int) -> WinLossCategory:
        """Creates !wl command category from `lobby_type` and `game_mode`.

        Dota Matches naturally in API data are described by those attributes.
        This allows categorizing dota matches for !wl command.
        """
        match lobby_type:
            case LobbyType.Ranked:
                category = WinLossCategory.Ranked
            case LobbyType.Unranked:
                category = WinLossCategory.Turbo if game_mode == GameMode.Turbo else WinLossCategory.Unranked
            case LobbyType.NewPlayerMode:
                category = WinLossCategory.NewPlayerMode
            case _:
                category = WinLossCategory.Other
        return category

    def display_name(self, lobby_type: LobbyType, game_mode: GameMode) -> str:
        mapping = {1: "Ranked", 3: "Turbo", 4: "New Player Mode"}

        display_name = mapping.get(self.value, None)
        if display_name:
            return display_name
        return f"{lobby_type.display_name} ({game_mode.display_name})"


class MyStrEnum(Enum, str):
    """An enumeration where all the values are integers, emulates `enum.StrEnum`."""

    if TYPE_CHECKING:

        def __new__(cls, value: str) -> Self: ...

        @override
        @classmethod
        def try_value(cls, value: str) -> Self: ...


class RPStatus(MyStrEnum):
    """Enum describing "status" field in Steam's Rich Presence."""

    # MY OWN ADDITIONS
    Offline = "#MY_Offline"
    """^ Offline is considered as when Rich Presence is None"""
    NoStatus = "#MY_NoStatus"
    """^ Somehow "status" field is missing from Rich Presence"""

    # DOTA_RP
    Idle = "#DOTA_RP_IDLE"
    MainMenu = "#DOTA_RP_INIT"
    Finding = "#DOTA_RP_FINDING_MATCH"
    WaitingToLoad = "#DOTA_RP_WAIT_FOR_PLAYERS_TO_LOAD"
    HeroSelection = "#DOTA_RP_HERO_SELECTION"
    Strategy = "#DOTA_RP_STRATEGY_TIME"
    PreGame = "#DOTA_RP_PRE_GAME"
    Playing = "#DOTA_RP_PLAYING_AS"
    Spectating = "#DOTA_RP_SPECTATING"
    PrivateLobby = "#DOTA_RP_PRIVATE_LOBBY"
    BotPractice = "#DOTA_RP_BOTPRACTICE"
    Coaching = "#DOTA_RP_COACHING"
    WatchingTournament = "#DOTA_RP_WATCHING_TOURNAMENT"

    # EXTRA
    CustomGame = "#DOTA_RP_GAME_IN_PROGRESS_CUSTOM"

    @classproperty
    def KNOWN_DISPLAY_NAMES(cls: type[Self]) -> Mapping[RPStatus, str]:  # type: ignore # noqa: N802, N805
        return {
            cls.Offline: "Offline/Invisible",
            cls.Idle: "Main Menu (Idle)",
            cls.MainMenu: "Main Menu",
            cls.Finding: "Finding A Match",
            cls.WaitingToLoad: "Waiting For Players to Load",
            cls.HeroSelection: "Hero Selection",
            cls.Strategy: "Strategy Phase",
            cls.PreGame: "PreGame",
            cls.Playing: "Playing",
            cls.Spectating: "Spectating",
            cls.PrivateLobby: "Private Lobby",
            cls.BotPractice: "Bot Practice",
            cls.Coaching: "Coaching",
            cls.WatchingTournament: "Watching Tournament",
            cls.CustomGame: "Custom Game",
        }

    @property
    def display_name(self) -> str:
        try:
            return self.KNOWN_DISPLAY_NAMES[self]
        except KeyError:
            # will still return "#DEADLOCK_RP_SOMETHING"
            return self.value


class LobbyParam0(StrEnum):
    DemoMode = "#demo_hero_mode_name"
    BotMatch = "#DOTA_lobby_type_name_bot_match"
