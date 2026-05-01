from __future__ import annotations

import abc
import asyncio
from typing import TYPE_CHECKING, Any, override

import orjson

from ..errors import IreBotError

if TYPE_CHECKING:
    import aiohttp

    from types_.dota_api_schemas import OpendotaMatches, SteamWebRealTimeStats, StratzItems

__all__ = ("APIClientError", "OpenDotaClient", "SteamWebAPIClient", "StratzClient")


class APIClientError(IreBotError):
    """Errors related to API Client."""


class APIClient(abc.ABC):
    def __init__(self, *, session: aiohttp.ClientSession) -> None:
        self.session: aiohttp.ClientSession = session

    @abc.abstractmethod
    async def invoke(self) -> Any: ...


class OpenDotaClient(APIClient):
    """A class for interacting with OpenDota API."""

    @override
    async def invoke(self, endpoint: str, argument: int) -> Any:
        """Invoke a request to OpenDota API."""
        url = f"https://api.opendota.com/api/{endpoint}/{argument}"
        async with self.session.get(url=url) as resp:
            return await resp.json(loads=orjson.loads)

    async def matches(self, match_id: int) -> OpendotaMatches:
        """Get match from opendota API via GET matches endpoint."""
        return await self.invoke("matches", match_id)


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
            return await resp.json(loads=orjson.loads)

    async def get_items(self) -> StratzItems:
        """Get Constants for Dota 2 Items."""
        query = """
query Items {
    constants {
        items {
            id
            displayName
        }
    }
}
        """
        return await self.invoke(query)


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

    async def get_real_time_stats(self, server_steam_id: int) -> SteamWebRealTimeStats:
        """Get Real Time Stats from Steam Web API.

        Links
        -----
        * https://steamapi.xpaw.me/#IDOTA2MatchStats_570/GetRealtimeStats.
        """
        return await self.invoke("IDOTA2MatchStats_570/GetRealtimeStats/v1", server_steam_id=server_steam_id)
