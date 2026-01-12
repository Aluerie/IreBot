from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, override

import discord
from discord.ext import tasks
from discord.utils import MISSING

if TYPE_CHECKING:
    import datetime

    from bot import IreBot

    class HasBotAttribute(Protocol):
        bot: IreBot


log = logging.getLogger(__name__)

__all__ = ("ireloop",)


_func = Callable[..., Coroutine[Any, Any, Any]]
LF = TypeVar("LF", bound=_func)


class IreLoop(tasks.Loop[LF]):
    """My subclass for discord.ext.tasks.Loop.

    Just extra boilerplate functionality.

    Notes
    -----
    Sorry to twitchio guys, but at the moment of writing this `discord.ext.tasks` is way more fleshed out
    and offers a bit more functionality than `twitchio.ext.routines`.

    Warning
    -------
    The task should be initiated in a class that has `.bot` of IreBot type. Otherwise, it will just fail.
    All my tasks (and all my code is in cogs that do have `.bot` but still)

    """

    def __init__(
        self,
        coro: LF,
        seconds: float,
        hours: float,
        minutes: float,
        time: datetime.time | Sequence[datetime.time],
        count: int | None,
        *,
        reconnect: bool,
        name: str | None,
        wait_for_ready: bool = False,
    ) -> None:
        super().__init__(coro, seconds, hours, minutes, time, count, reconnect, name)
        if wait_for_ready:
            self._before_loop = self._wait_for_ready

    async def _wait_for_ready(self, cog: HasBotAttribute) -> None:  # *args: Any
        await cog.bot.wait_until_ready()

    @override
    async def _error(self, cog: HasBotAttribute, exception: Exception) -> None:
        """Same `_error` as in parent class but with `exc_manager` integrated."""
        embed = (
            discord.Embed(title=self.coro.__name__, colour=0x1A7A8A)
            .set_author(name=f"{self.coro.__module__}: {self.coro.__qualname__}")
            .set_footer(text=f"{self.__class__.__name__}: {self.coro.__name__}")
        )
        await cog.bot.exc_manager.register_error(exception, embed)


@discord.utils.copy_doc(tasks.loop)
def ireloop(
    *,
    seconds: float = MISSING,
    minutes: float = MISSING,
    hours: float = MISSING,
    time: datetime.time | Sequence[datetime.time] = MISSING,
    count: int | None = None,
    reconnect: bool = True,
    name: str | None = None,
    wait_for_ready: bool = False,
) -> Callable[[LF], IreLoop[LF]]:
    """Copy-pasted `loop` decorator from `discord.ext.tasks` corresponding to AluLoop class.

    Notes
    -----
    * if `discord.ext.tasks` gets extra cool features which will be represented in a change of `tasks.loop`
        decorator/signature we would need to manually update this function (or maybe even AluLoop class)

    """

    def decorator(func: LF) -> IreLoop[LF]:
        return IreLoop(
            func,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            count=count,
            time=time,
            reconnect=reconnect,
            name=name,
            wait_for_ready=wait_for_ready,
        )

    return decorator
