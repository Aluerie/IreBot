from __future__ import annotations

from typing import TYPE_CHECKING, override

from bot import IrePersonalComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreContext


class BaseDevComponent(IrePersonalComponent):
    """A base Dev Cog class.

    Double-ensures that commands have owner-only check.
    """

    @override
    async def component_before_invoke(self, ctx: IreContext) -> bool:
        return ctx.chatter.id in const.BOT_OWNERS
