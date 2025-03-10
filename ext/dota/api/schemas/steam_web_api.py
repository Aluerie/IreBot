"""Schemas representing data structure for Steam WEB API."""

from __future__ import annotations

from typing import Literal, TypedDict

__all__ = ("RealTimeStatsResponse",)


# 1. GET REAL TIME STATS


class RealTimeStatsResponse(TypedDict):
    match: Match
    teams: list[Team]
    buildings: list[Building]
    graph_data: GraphData


class Match(TypedDict):
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


class Team(TypedDict):
    team_number: Literal[2, 3]
    team_id: int
    team_name: str
    team_tag: str
    team_logo: str
    score: int
    net_worth: int
    team_logo_url: str
    players: list[TeamPlayer]


class TeamPlayer(TypedDict):
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


class Building(TypedDict):
    team: Literal[2, 3]
    heading: float
    type: int
    lane: int
    tier: int
    x: float
    y: float
    destroyed: bool


class GraphData(TypedDict):
    graph_gold: list[int]
