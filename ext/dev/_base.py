from __future__ import annotations

from typing import TYPE_CHECKING, override

from bot import IreComponent

if TYPE_CHECKING:
    from twitchio.ext import commands


class BaseDevComponent(IreComponent):
    """A base Dev Cog class.

    Double-ensures that commands have owner-only check.
    """

    @override
    async def component_before_invoke(self, ctx: commands.Context) -> bool:
        return ctx.is_owner()
