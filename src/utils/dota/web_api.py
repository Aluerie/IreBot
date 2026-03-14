from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import orjson

from utils import errors

if TYPE_CHECKING:
    import aiohttp

    from .schemas import web_api as schemas

__all__ = ("SteamWebAPIError", "WebAPIClient")


class SteamWebAPIError(errors.IreBotError):
    """Errors related to Steam Web API."""


class WebAPIClient:
    """A class for interacting with Steam Web API.

    Parameters
    ----------
    api_key: str
        Steam Web API Key. Needed for all requests.
    """

    def __init__(self, *, api_key: str, session: aiohttp.ClientSession) -> None:
        self.api_key: str = api_key
        self.session: aiohttp.ClientSession = session

    async def invoke(
        self,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
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
            raise SteamWebAPIError(msg)

        return result

    async def get_real_time_stats(self, server_steam_id: int) -> schemas.RealTimeStats:
        """Get Real Time Stats from Steam Web API.

        Links
        -----
        * https://steamapi.xpaw.me/#IDOTA2MatchStats_570/GetRealtimeStats.
        """
        return await self.invoke("IDOTA2MatchStats_570/GetRealtimeStats/v1", server_steam_id=server_steam_id)
