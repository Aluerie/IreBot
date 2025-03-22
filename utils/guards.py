from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Any

from twitchio.ext import commands

from . import const, errors

if TYPE_CHECKING:
    from bot import IreContext


def is_vps() -> Any:
    """Allow the command to be completed only on VPS machine.

    A bit niche, mainly used for developer commands to interact with VPS machine such as
    kill the bot process or reboot it.
    """

    def predicate(_: IreContext) -> bool:
        if platform.system() == "Windows":
            # wrong PC
            msg = f"Only production bot allows usage of this command {const.FFZ.peepoPolice}"
            raise errors.GuardError(msg)
        return True

    return commands.guard(predicate)


def is_online() -> Any:
    """Allow the command to be completed only when Irene's stream is online."""

    def predicate(ctx: IreContext) -> bool:
        return ctx.bot.irene_online

    return commands.guard(predicate)
