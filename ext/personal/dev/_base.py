from __future__ import annotations

from typing import TYPE_CHECKING, override

from bot import IrePersonalComponent

if TYPE_CHECKING:
    from bot import IreContext


class BaseDevComponent(IrePersonalComponent):
    """A base Dev Cog class.

    Double-ensures that commands have owner-only check.
    """

    @override
    async def component_before_invoke(self, ctx: IreContext) -> bool:
        return ctx.chatter.id == ctx.bot.owner_id
