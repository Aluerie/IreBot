from __future__ import annotations

import abc
import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypedDict, override

import orjson

from utils import errors

from ..errors import IreBotError

if TYPE_CHECKING:
    import aiohttp

    from types_ import dota_api_schemas

    class GraphQLData(TypedDict):
        data: Any


__all__ = (
    "APIClientError",
    "OpenDotaClient",
    "SteamWebAPIClient",
    "StratzClient",
)
log = logging.getLogger(__name__)


class APIClientError(IreBotError):
    """Errors related to API Client."""


class APIClient(abc.ABC):
    def __init__(self, *, session: aiohttp.ClientSession) -> None:
        self.session: aiohttp.ClientSession = session

    @abc.abstractmethod
    async def invoke(self, *args: Any, **kwargs: Any) -> Any: ...


class OpenDotaClient(APIClient):
    """A class for interacting with OpenDota API."""

    @override
    async def invoke(self, endpoint: str) -> Any:
        """Invoke a request to OpenDota API."""
        url = f"https://api.opendota.com/api/{endpoint}"
        async with self.session.get(url=url) as resp:
            return await resp.json(loads=orjson.loads)

    async def matches(self, match_id: int) -> dota_api_schemas.OpendotaMatches:
        """Get match from opendota API via GET matches endpoint."""
        return await self.invoke(f"matches/{match_id}")

    async def get_items(self) -> dota_api_schemas.OpendotaItemsQuery:
        """Get Opendota constants items.

        Links
        -----
        * https://api.opendota.com/api/constants/items
        * https://raw.githubusercontent.com/odota/dotaconstants/master/build/items.json
        """
        log.debug("🍋 Opendota Constants API: getting items.")
        return await self.invoke("constants/items")


class StratzClient(APIClient):
    """A class for interacting with Stratz GraphQL API."""

    def __init__(self, *, bearer_token: str, session: aiohttp.ClientSession) -> None:
        super().__init__(session=session)
        self.bearer_token: str = bearer_token

    @override
    async def invoke(self, query: str) -> Any:
        """Invoke a request to Stratz GraphQL API."""
        async with self.session.post(
            url="https://api.stratz.com/graphql",
            json={"query": query},
            headers={
                "User-Agent": "STRATZ_API",
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
        ) as resp:
            graphql_json: GraphQLData = await resp.json(loads=orjson.loads)
            try:
                return graphql_json["data"]
            except KeyError:
                msg = "Stratz GraphQL API Error:"
                raise errors.APIDataError(msg, graphql_json) from None

    async def get_items(self) -> list[dota_api_schemas.StratzItem]:
        """Get Constants for Dota 2 Items."""
        log.debug("🍋 Stratz GraphQL API: getting items.")
        query = """
        query AllItemsQuery {
            constants {
                items {
                    id
                    displayName
                }
            }
        }
        """
        data: dota_api_schemas.StratzItemData = await self.invoke(query)
        return data["constants"]["items"]


class SteamWebAPIClient(APIClient):
    """A class for interacting with Steam Web API.

    Parameters
    ----------
    api_key: str
        Steam Web API Key. Needed for all requests.
    """

    def __init__(self, *, api_key: str, session: aiohttp.ClientSession) -> None:
        super().__init__(session=session)
        self.api_key: str = api_key

    @override
    async def invoke(self, endpoint: str, **kwargs: Any) -> Any:
        """Invoke a request to Steam Web API."""
        queries = "&".join(f"{k}={v}" for k, v in kwargs.items())
        url = f"https://api.steampowered.com/{endpoint}/?key={self.api_key}&{queries}"
        max_failures = 10
        for attempt in range(max_failures):
            async with self.session.get(url) as resp:
                # encoding='utf-8' errored out one day, it seems Valve have misconfigured some servers' content types
                # Or maybe they have to because all the unique characters in player names?
                # I'm not sure if this "ISO-8859-1" encoding solves all problems;
                # meta shows utf-8 though so idk.
                result = await resp.json(loads=orjson.loads, content_type=None, encoding="ISO-8859-1")
                if result:
                    break
                # Valve, why does it return an empty dict `{}` on the very first request for every match...
                # It's a problem even in the actual game client.
                # So we have to ask again hence this silly for loop.
                # some lazy exp backoff:
                await asyncio.sleep(0.49 * 1.7**attempt)
                continue
        else:
            msg = f'Response "{url}" was empty {max_failures} times in a row.'
            raise APIClientError(msg)

        return result

    async def get_real_time_stats(self, server_steam_id: int) -> dota_api_schemas.SteamWebRealTimeStats:
        """Get Real Time Stats from Steam Web API.

        Links
        -----
        * https://steamapi.xpaw.me/#IDOTA2MatchStats_570/GetRealtimeStats.
        """
        return await self.invoke("IDOTA2MatchStats_570/GetRealtimeStats/v1", server_steam_id=server_steam_id)
