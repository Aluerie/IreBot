from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

__all__ = ("Matches",)


class Matches(TypedDict):
    """Typing Dict for response json for the OpenDota's `GET matches` endpoint.

    I didn't include all fields; just those that I need at the moment.
    """

    players: list[MatchesPlayer]
    match_id: int
    lobby_type: int
    game_mode: int


class MatchesPlayer(TypedDict):
    abandons: Literal[0, 1]
    account_id: NotRequired[int]
