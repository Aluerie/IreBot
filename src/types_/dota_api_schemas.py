"""API Schemas for `utils.dota.api_clients`."""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

__all__ = (
    "OpendotaMatches",
    "SteamWebRealTimeStats",
    "StratzItems",
)

####################
#   1. OPENDOTA    #
####################


class OpendotaMatches(TypedDict):
    """Typing Dict for response json for the OpenDota's `GET matches` endpoint.

    I didn't include all fields; just those that I need at the moment.
    """

    players: list[OpendotaMatchesPlayer]
    match_id: int
    lobby_type: int
    game_mode: int


class OpendotaMatchesPlayer(TypedDict):
    abandons: Literal[0, 1]
    account_id: NotRequired[int]


####################
#    2. STRATZ     #
####################


class StratzItems(TypedDict):
    """Schema for Stratz GraphQL `get_items` response."""

    data: StratzItemData


class StratzItemData(TypedDict):
    constants: StratzItemConstants


class StratzItemConstants(TypedDict):
    items: list[StratzItem]


class StratzItem(TypedDict):
    id: int
    displayName: str


####################
# 3. STEAM WEB API #
####################


class SteamWebRealTimeStats(TypedDict):
    """Schema for `get_real_time_stats` response."""

    match: SteamWebRealTimeStatsMatch
    teams: list[SteamWebRealTimeStatsTeam]
    buildings: list[SteamWebRealTimeStatsBuilding]
    graph_data: SteamWebRealTimeStatsGraphData


class SteamWebRealTimeStatsMatch(TypedDict):
    server_steam_id: str
    match_id: str
    timestamp: int
    game_time: int
    game_mode: int
    league_id: int
    league_node_id: int
    game_state: int
    lobby_type: int
    start_timestamp: int


class SteamWebRealTimeStatsTeam(TypedDict):
    team_number: Literal[2, 3]
    team_id: int
    team_name: str
    team_tag: str
    team_logo: str
    score: int
    net_worth: int
    team_logo_url: str
    players: list[SteamWebRealTimeStatsTeamPlayer]


class SteamWebRealTimeStatsTeamPlayer(TypedDict):
    accountid: int
    playerid: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    name: str
    team: Literal[2, 3]
    heroid: int
    level: int
    kill_count: int
    death_count: int
    assists_count: int
    denies_count: int
    lh_count: int
    gold: int
    x: float
    y: float
    net_worth: int
    abilities: list[int]
    items: list[int]
    team_slot: Literal[0, 1, 2, 3, 4]


class SteamWebRealTimeStatsBuilding(TypedDict):
    team: Literal[2, 3]
    heading: float
    type: int
    lane: int
    tier: int
    x: float
    y: float
    destroyed: bool


class SteamWebRealTimeStatsGraphData(TypedDict):
    graph_gold: list[int]
