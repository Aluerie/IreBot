"""
Base class for BetaCog for `modules.beta.py`.

It's a silly way to quickly beta-test some things, but this way
`modules.beta.py` can be done in the least amount of lines as all the imports and chores
are handled in this base file instead.

For an example of how `modules.beta.py` looks - you can look in `examples` folder.
"""

#  pyright: basic

from __future__ import annotations

import asyncio
import itertools
import logging
import platform
from typing import TYPE_CHECKING, Any, Literal

import aiohttp
import twitchio
from twitchio.ext import commands

from config import config
from core import IreDevComponent, ireloop
from utils import const, errors

if TYPE_CHECKING:
    from core import IreBot, IreContext

log = logging.getLogger(__name__)


class BetaCog(IreDevComponent):
    """Base Class for BetaTest cog.

    Used to test random code snippets.
    """

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)
        self.beta_test.start()

    @ireloop(count=1)
    async def beta_test(self) -> None:
        """Task that is supposed to run just once to test stuff out."""
