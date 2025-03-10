from __future__ import annotations

import asyncio
import datetime
import logging
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

    import discord

    from .bot import IreBot


log = logging.getLogger("exc_manager")


class ExceptionManager:
    """Exception Manager that."""

    __slots__: tuple[str, ...] = (
        "_lock",
        "_most_recent",
        "bot",
        "cooldown",
        "errors_cache",
    )

    def __init__(self, bot: IreBot, *, cooldown: datetime.timedelta = datetime.timedelta(seconds=5)) -> None:
        self.bot: IreBot = bot
        self.cooldown: datetime.timedelta = cooldown

        self._lock: asyncio.Lock = asyncio.Lock()
        self._most_recent: datetime.datetime | None = None

    def _yield_code_chunks(self, iterable: str, *, chunks_size: int = 2000) -> Generator[str, None, None]:
        codeblocks: str = "```py\n{}```"
        max_chars_in_code = chunks_size - (len(codeblocks) - 2)  # chunks_size minus code blocker size

        for i in range(0, len(iterable), max_chars_in_code):
            yield codeblocks.format(iterable[i : i + max_chars_in_code])

    async def register_error(self, error: BaseException, embed: discord.Embed, *, mention: bool = True) -> None:
        """Register, analyse error and put it into queue to send to developers."""
        log.error("%s: `%s`.", error.__class__.__name__, embed.footer.text, exc_info=error)

        traceback_string = "".join(traceback.format_exception(error)).replace(str(Path.cwd()), "IreBot")

        async with self._lock:
            if self._most_recent and (delta := datetime.datetime.now(datetime.UTC) - self._most_recent) < self.cooldown:
                # We have to wait
                total_seconds = delta.total_seconds()
                log.debug("Waiting %s seconds to send the error.", total_seconds)
                await asyncio.sleep(total_seconds)

            self._most_recent = datetime.datetime.now(datetime.UTC)
            await self.send_error(traceback_string, embed, mention=mention)

    async def send_error(self, traceback: str, embed: discord.Embed, *, mention: bool) -> None:
        """Send an error to the webhook.

        It is not recommended to call this yourself, call `register_error` instead.
        """
        code_chunks = list(self._yield_code_chunks(traceback))

        if mention:
            await self.bot.error_webhook.send(self.bot.error_ping)

        for chunk in code_chunks:
            await self.bot.error_webhook.send(chunk)

        if mention:
            await self.bot.error_webhook.send(embed=embed)
