from __future__ import annotations

import abc
import asyncio
import json
import logging
import pathlib
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, override

import aiohttp
import discord

from bot import ireloop

if TYPE_CHECKING:
    from bot import IreBot

    class DotaCacheDict(TypedDict):
        item_by_id: dict[int, str]  # id -> item name


__all__ = (
    "GameDataStorage",
    "Items",
)


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


CDN_REACT = "https://cdn.akamai.steamstatic.com/apps/dota2/images/dota_react/"


class GameDataStorage[VT, PseudoVT](abc.ABC):
    """Game Data Storage.

    Used for fetching and storing data from public API and JSONs.
    The concept is the data gets updated/refreshed once a day.

    if KeyError arises - there is an attempt to refresh the data, otherwise it's assumed that the data is fine enough
    (yes, it can backfire with an update where, for example, some item icon changes,
    but we still update storage once per day, so whatever).
    """

    if TYPE_CHECKING:
        cached_data: dict[int, VT]

    def __init__(self, bot: IreBot) -> None:
        """__init__.

        Parameters
        ----------
        bot
            need it just so @ireloop task can use `exc_manager` to send an error notification.
        """
        self.bot: IreBot = bot
        self.lock: asyncio.Lock = asyncio.Lock()

    def start(self) -> None:
        """Start the storage tasks."""
        # self.update_data.add_exception_type(errors.ResponseNotOK)
        # random times just so we don't have a possibility of all cache being updated at the same time
        self.update_data.change_interval(hours=24, minutes=random.randint(1, 59))
        self.update_data.start()

    def close(self) -> None:
        """Cancel the storage tasks."""
        self.update_data.cancel()

    @abc.abstractmethod
    async def fill_data(self) -> dict[int, VT]:
        """Fill self.cached_data with the data from various json data.

        This function is supposed to be implemented by subclasses.
        We get the data and sort it out into a convenient dictionary to cache.
        """

    @ireloop()
    async def update_data(self) -> None:
        """The task responsible for keeping the data up-to-date."""
        log.debug("Updating Storage %s.", self.__class__.__name__)
        async with self.lock:
            start_time = time.perf_counter()
            self.cached_data = await self.fill_data()
            log.debug(
                "Storage %s %s is updated in %.3fs",
                __package__.split(".")[-1].capitalize() if __package__ else "",
                self.__class__.__name__,
                time.perf_counter() - start_time,
            )
            # Make a back up for fun
            await asyncio.sleep(60 * 60)
            with pathlib.Path(f".temp/{self.__class__.__name__}.json").open("w", encoding="utf-8") as f:
                json.dump(self.cached_data, f, ensure_ascii=False, indent=4, default=str)

    async def get_cached_data(self) -> dict[int, VT]:
        """Get the whole cached data."""
        try:
            return self.cached_data
        except AttributeError:
            await self.update_data()
            return self.cached_data

    async def get_value(self, object_id: int) -> VT:
        """Get value by the `key` from `self.cached_data`."""
        try:
            return self.cached_data[object_id]
        except (KeyError, AttributeError):
            # let's try to update the cache in case it's a KeyError due to
            # * new patch or something
            # * the data is not initialized then we will get stuck in self.lock waiting for the data.
            await self.update_data()
            return self.cached_data[object_id]

    async def send_unknown_value_report(self, object_id: int) -> None:
        """Send a notification to the developers when unknown value appears to be requested."""
        embed = discord.Embed(
            color=discord.Colour.red(),
            title=f"Unknown {self.__class__.__name__} appeared!",
            description=f"```py\nid={object_id}\n```",
        ).set_footer(text=f"Package: {__package__}")
        await self.bot.error_webhook.send(embed=embed)

    @staticmethod
    @abc.abstractmethod
    def generate_unknown_object(object_id: int) -> PseudoVT:
        """Generate unknown object."""

    async def by_id(self, object_id: int) -> VT | PseudoVT:
        """Get storage object by its ID."""
        try:
            storage_object = await self.get_value(object_id)
        except KeyError:
            return self.generate_unknown_object(object_id)
        else:
            return storage_object

    async def all(self) -> list[VT | PseudoVT]:
        """Get all objects in the storage."""
        data = await self.get_cached_data()
        return list(data.values())


@dataclass
class Item:
    id: int
    display_name: str

    @override
    def __str__(self) -> str:
        return self.display_name or ""  # Sometimes, Stratz actually sends `None`` into display_name

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} {self.display_name}>"


class Items(GameDataStorage[Item, Item]):
    """Storage for Dota 2 Items."""

    @override
    async def fill_data(self) -> dict[int, Item]:
        try:
            items = await self.bot.dota.stratz.get_items()
            return {item["id"]: Item(item["id"], item["displayName"]) for item in items["data"]["constants"]["items"]}
        except aiohttp.ClientResponseError as err:
            log.exception("%s: `%s`.", err.__class__.__name__, exc_info=err)
            try:
                with pathlib.Path(f".temp/{self.__class__.__name__}.json").open(encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                raise err from None

    @override
    @staticmethod
    def generate_unknown_object(item_id: int) -> Item:
        return Item(id=item_id, display_name="Unknown Item")

    @override
    async def by_id(self, item_id: int) -> Item:
        """Get Item by its ID."""
        # special case
        if item_id == 0:
            return Item(0, "Empty Slot")
        return await super().by_id(item_id)
