from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Self, override

from steam.enums import Enum, classproperty
from steam.ext.dota2 import GameMode, LobbyType

if TYPE_CHECKING:
    from collections.abc import Mapping


class MyStrEnum(Enum, str):
    """An enumeration where all the values are integers, emulates `enum.StrEnum`."""

    __slots__ = ()

    if TYPE_CHECKING:

        @override
        def __new__(cls, value: str) -> Self: ...

        @override
        @classmethod
        def try_value(cls, value: str) -> Self: ...


class Status(MyStrEnum):
    """Enum describing "status" field in Steam's Rich Presence."""

    # MY OWN ADDITIONS
    RichPresenceNone = "#MY_RP_NONE"
    """^ Offline is considered as when Rich Presence is None"""
    NoStatus = "#MY_NO_STATUS"
    """^ Somehow "status" field is missing from Rich Presence"""

    # DOTA_RP
    Idle = "#DOTA_RP_IDLE"  # ✅
    MainMenu = "#DOTA_RP_INIT"  # ✅
    Finding = "#DOTA_RP_FINDING_MATCH"  # ✅
    WaitingForMapToLoad = "#DOTA_RP_WAIT_FOR_MAP_TO_LOAD"
    WaitingToLoad = "#DOTA_RP_WAIT_FOR_PLAYERS_TO_LOAD"  # ✅
    HeroSelection = "#DOTA_RP_HERO_SELECTION"  # ✅
    Strategy = "#DOTA_RP_STRATEGY_TIME"  # ✅
    PreGame = "#DOTA_RP_PRE_GAME"  # ❓
    Playing = "#DOTA_RP_PLAYING_AS"  # ✅
    Spectating = "#DOTA_RP_SPECTATING"  # ✅
    PrivateLobby = "#DOTA_RP_PRIVATE_LOBBY"  # ✅
    BotPractice = "#DOTA_RP_BOTPRACTICE"  # ❓
    Coaching = "#DOTA_RP_COACHING"  # ❓
    WatchingTournament = "#DOTA_RP_WATCHING_TOURNAMENT"  # ✅
    CustomGameProgress = "#DOTA_RP_GAME_IN_PROGRESS_CUSTOM"  # ✅
    CustomGameLobby = "#DOTA_RP_LOBBY_CUSTOM"  # ✅

    @classproperty
    def KNOWN_DISPLAY_NAMES(cls: type[Self]) -> Mapping[Status, str]:  # type: ignore[GeneralTypeIssue] # noqa: N802, N805
        """Mapping between RPStatus enum and human-readable display names for them."""
        return {
            cls.RichPresenceNone: "Offline/Invisible",
            cls.NoStatus: "No Status (yet)",
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
            cls.CustomGameProgress: "Custom Game",
        }

    @property
    def display_name(self) -> str:
        """Get a chat-send friendly display name, if present."""
        try:
            return self.KNOWN_DISPLAY_NAMES[self]
        except KeyError:
            # will still return "#DEADLOCK_RP_SOMETHING"
            return self.value


class ScoreCategory(IntEnum):
    """Match categories for !score (!wl !winloss) command.

    The bot will group matches into !wl command by this parameter, i.e. !wl -> "Ranked 3 W - 1 L, Turbo 2 W - 0 L."
    """

    Ranked = 1
    Unranked = 2
    Turbo = 3
    Other = 4

    @classmethod
    def create(cls, lobby_type: int, game_mode: int) -> ScoreCategory:
        """Creates !wl command category from `lobby_type` and `game_mode`.

        Dota Matches naturally in API data are described by those attributes.
        This allows categorizing dota matches for !wl command.
        """
        match lobby_type:
            case LobbyType.Ranked:
                return ScoreCategory.Ranked
            case LobbyType.Unranked:
                return ScoreCategory.Turbo if game_mode == GameMode.Turbo else ScoreCategory.Unranked
            case _:
                return ScoreCategory.Other


class LobbyParam0(StrEnum):
    """Known Lobby Param 0."""

    DemoMode = "#demo_hero_mode_name"
    BotMatch = "#DOTA_lobby_type_name_bot_match"
