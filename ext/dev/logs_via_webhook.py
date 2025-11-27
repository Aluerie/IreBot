from __future__ import annotations

import asyncio
import datetime
import logging
import textwrap
from typing import TYPE_CHECKING, Any, override

import discord
from twitchio.ext import commands

from bot import ireloop
from utils import const

from ._base import BaseDevComponent

if TYPE_CHECKING:
    from collections.abc import Mapping

    from bot import IreBot

log = logging.getLogger(__name__)


class LoggingHandler(logging.Handler):
    """Extra Logging Handler to output info/warning/errors to a discord webhook."""

    def __init__(self, cog: LogsViaWebhook) -> None:
        self.cog: LogsViaWebhook = cog
        super().__init__(logging.INFO)

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out some somewhat pointless messages so we don't spam the channel as much."""
        messages_to_ignore = ("Webhook ID 1280488051776163903 is rate limited.",)
        if any(msg in record.message for msg in messages_to_ignore):  # noqa: SIM103
            return False
        return True

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.cog.add_record(record)


class LogsViaWebhook(BaseDevComponent):
    """Mirroring logs to discord webhook messages.

    This cog is responsible for rate-limiting, formatting, fine-tuning and sending the log messages.
    """

    EXACT_AVATAR_MAPPING: Mapping[str, str] = {
        "bot.bot": "https://i.imgur.com/6XZ8Roa.png",  # lady Noir
        "exc_manager": "https://em-content.zobj.net/source/microsoft/378/sos-button_1f198.png",
    }
    INCLUSIVE_AVATAR_MAPPING: Mapping[str, str] = {
        "twitchio.": "https://raw.githubusercontent.com/Aluerie/AluBot/main/assets/images/logo/twitchio.png",
    }
    DOLPHIN_IMAGE: str = "https://em-content.zobj.net/source/microsoft/407/dolphin_1f42c.png"

    EMOJIS: Mapping[str, str] = {
        "INFO": "\N{INFORMATION SOURCE}\ufe0f",
        "WARNING": "\N{WARNING SIGN}\ufe0f",
        "ERROR": "\N{CROSS MARK}",
    }
    COLORS: Mapping[str, discord.Color | int] = {
        "INFO": 0x03A9F4,
        "WARNING": 0xFBC02D,
        "ERROR": 0x800000,
    }

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self._logging_queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue()

        # cooldown attrs
        self._lock: asyncio.Lock = asyncio.Lock()
        self.cooldown: datetime.timedelta = datetime.timedelta(seconds=5)
        self._most_recent: datetime.datetime | None = None

    @override
    async def component_load(self) -> None:
        self.logging_worker.start()
        self.logs_handler = LoggingHandler(self)
        logging.getLogger().addHandler(self.logs_handler)
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.logging_worker.stop()
        log.warning("Tearing down logger via webhook.")
        logging.getLogger().removeHandler(self.logs_handler)
        del self.logs_handler
        await super().component_teardown()

    def add_record(self, record: logging.LogRecord) -> None:
        """Add a record to a logging queue."""
        self._logging_queue.put_nowait(record)

    def get_avatar(self, username: str) -> str:
        """Helper function to get an avatar ulr based on a webhook username to send the record with."""
        # exact name
        if avatar_url := self.EXACT_AVATAR_MAPPING.get(username):
            return avatar_url
        # inclusions
        for search_name, candidate in self.INCLUSIVE_AVATAR_MAPPING.items():
            if username.startswith(search_name):
                return candidate
        # else
        return discord.utils.MISSING

    async def send_log_record(self, record: logging.LogRecord) -> None:
        """Send Log record to discord webhook."""
        emoji = self.EMOJIS.get(record.levelname, "\N{WHITE QUESTION MARK ORNAMENT}")
        color = self.COLORS.get(record.levelname)

        dt = datetime.datetime.fromtimestamp(record.created, datetime.UTC)
        msg = textwrap.shorten(f"{emoji} {discord.utils.format_dt(dt, style='T')} {record.message}", width=1995)
        avatar_url = self.get_avatar(record.name)
        username = record.name.replace("discord", "disсоrd")  # cSpell: ignore disсоrd  # noqa: RUF003

        embed = discord.Embed(color=color, description=msg)
        await self.bot.logger_webhook.send(content=username)
        await self.bot.logger_webhook.send(embed=embed, username=username, avatar_url=avatar_url)

    @ireloop(seconds=0.0)
    async def logging_worker(self) -> None:
        """Task responsible for mirroring logging messages to a discord webhook."""
        record = await self._logging_queue.get()

        async with self._lock:
            if self._most_recent and (delta := datetime.datetime.now(datetime.UTC) - self._most_recent) < self.cooldown:
                # We have to wait
                total_seconds = delta.total_seconds()
                log.debug("Waiting %s seconds to send the error.", total_seconds)
                await asyncio.sleep(total_seconds)

            self._most_recent = datetime.datetime.now(datetime.UTC)
            await self.send_log_record(record)

    @commands.Component.listener(name="ready")
    async def announce_reloaded(self) -> None:
        """Announce that bot is successfully reloaded/restarted."""
        await self.irene.deliver(f"{const.STV.hi} the bot is reloaded.")


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    if __name__ in bot.extensions:
        # check if the extension is listed in extensions

        cog = LogsViaWebhook(bot)
        await bot.add_component(cog)
