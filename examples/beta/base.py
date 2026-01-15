#  pyright: basic

from __future__ import annotations

import asyncio
import itertools
import logging
import platform
from typing import TYPE_CHECKING, Literal

import aiohttp
import twitchio
from twitchio.ext import commands

from bot import IrePersonalComponent, ireloop
from config import config
from utils import const

if TYPE_CHECKING:
    from bot import IreBot, IreContext

log = logging.getLogger(__name__)


class BetaCog(IrePersonalComponent):
    """Base Class for BetaTest cog.

    Used to test random code snippets.
    """

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)
        self.beta_test.start()

    @ireloop(count=1)
    async def beta_test(self) -> None:
        """Task that is supposed to run just once to test stuff out."""
