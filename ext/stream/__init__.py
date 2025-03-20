from __future__ import annotations

from typing import TYPE_CHECKING

from .edit_information import EditInformation
from .emotes_check import EmoteChecker

if TYPE_CHECKING:
    from bot import IreBot


class Stream(
    EditInformation,
    EmoteChecker,
):
    """Developer functionality.

    These features are to be used by the developers only.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Stream(bot))
