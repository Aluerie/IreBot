from __future__ import annotations

from typing import TYPE_CHECKING

from .meta import MetaCommands

if TYPE_CHECKING:
    from bot import IreBot


class UncategorizedPublicCommands(
    MetaCommands,
):
    """Uncategorized Public Commands.

    These commands just do not belong to any specific "categorized" public component
    so they found their place here.
    """


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(UncategorizedPublicCommands(bot))
