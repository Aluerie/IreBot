from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

__all__ = ("Match",)


class Match(TypedDict):
    """Typing Dict for response json for opendota GET matches endpoint.

    I didn't include all fields; just those that I need at the moment.
    """

    players: list[Player]
    match_id: int
    lobby_type: int
    game_mode: int


class Player(TypedDict):
    abandons: Literal[0, 1]
    account_id: NotRequired[int]
