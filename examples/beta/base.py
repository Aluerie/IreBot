#  pyright: basic

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

import aiohttp
import twitchio
from twitchio.ext import commands

import config
from bot import LueComponent, lueloop
from utils import const

if TYPE_CHECKING:
    from bot import LueBot


class BetaCog(LueComponent):
    """Base Class for BetaTest cog.

    Used to test random code snippets.
    """

    def __init__(self, bot: LueBot) -> None:
        super().__init__(bot)
        self.beta_test.start()

    @lueloop(count=1)
    async def beta_test(self) -> None:
        """Task that is supposed to run just once to test stuff out."""
        ...
