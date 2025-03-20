from __future__ import annotations

from typing import TYPE_CHECKING

from steam import ID

from utils import errors

if TYPE_CHECKING:
    from steam.ext.dota2 import ProfileCard


def convert_id3_to_id64(steam_id3: str) -> int:
    """Get `steam_id` in a id64 format from steam_id in id3 format.

    Example
    -------
    Steam Web API uses Steam IDs for servers in id64 format, but Rich Presence provides them in id3.
    [A:1:3513917470:30261] -> 90201966066671646.
    """
    steam_id = ID.from_id3(steam_id3)
    if steam_id is None:
        msg = "Failed to get steam ID from id3."
        raise errors.PlaceholderRaiseError(msg)
    return steam_id.id64


def rank_medal_display_name(profile_card: ProfileCard) -> str:
    display_name = profile_card.rank_tier.division
    if stars := profile_card.rank_tier.stars:
        display_name += f" \N{BLACK STAR}{stars}"
    if number_rank := profile_card.leaderboard_rank:
        display_name += f" #{number_rank}"
    return display_name
