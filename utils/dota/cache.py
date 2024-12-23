from __future__ import annotations

import asyncio
import logging
import random
from time import perf_counter
from typing import TYPE_CHECKING, Any, TypedDict

from bot import lueloop
from utils import errors

from .pulsefire_clients import ODotaConstantsClient

if TYPE_CHECKING:
    from bot import LueBot

    class DotaCacheDict(TypedDict):
        item_by_id: dict[int, str]  # id -> item name


__all__ = ("DotaKeyCache",)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class DotaKeyCache:
    if TYPE_CHECKING:
        oconst: ODotaConstantsClient

    def __init__(self, bot: LueBot) -> None:
        self.bot: LueBot = bot
        self.lock: asyncio.Lock = asyncio.Lock()
        self._update_data.add_exception_type(errors.ResponseNotOK)
        # random times just so we don't have a possibility of all cache being updated at the same time
        self._update_data.change_interval(hours=24, minutes=random.randint(1, 59))
        self._update_data.start()

    @lueloop()
    async def _update_data(self) -> None:
        """The task responsible for keeping the data up-to-date."""
        # log.debug("Trying to update Cache %s.", self.__class__.__name__)
        async with self.lock:
            start_time = perf_counter()
            self.cached_data = await self._fill_data()
            log.debug("Dota Cache %s is updated in %.5f", self.__class__.__name__, perf_counter() - start_time)

    @_update_data.before_loop
    async def _start_pulsefire(self) -> None:
        if not hasattr(self, "oconst"):
            self.oconst = ODotaConstantsClient()
            await self.oconst.__aenter__()

    @_update_data.after_loop
    async def _close_pulsefire(self) -> None:
        if hasattr(self, "oconst"):
            await self.oconst.__aexit__()

    async def _fill_data(self) -> DotaCacheDict:
        items = await self.oconst.get_items()

        data: DotaCacheDict = {
            "item_by_id": {-1: "Empty"} | {item["id"]: item.get("dname", key) for key, item in items.items()},
        }

        return data

    async def _get_value(self, category: str, key: Any) -> Any:
        try:
            return self.cached_data[category][key]
        except (KeyError, AttributeError):
            await self._update_data()
            return self.cached_data[category][key]

    async def item_by_id(self, item_id: int) -> str:
        return await self._get_value("item_by_id", item_id)
