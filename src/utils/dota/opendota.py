from __future__ import annotations

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    import aiohttp

    from .schemas import opendota as schemas

__all__ = ("OpenDotaClient",)


class OpenDotaClient:
    """A class for interacting with OpenDota API."""

    def __init__(self, *, session: aiohttp.ClientSession) -> None:
        self.session: aiohttp.ClientSession = session

    async def invoke(
        self,
        endpoint: str,
        argument: int,
    ) -> Any:
        """Invoke a request to OpenDota API."""
        url = f"https://api.opendota.com/api/{endpoint}/{argument}"
        async with self.session.get(url=url) as resp:
            return await resp.json(loads=orjson.loads)

    async def matches(self, match_id: int) -> schemas.Matches:
        """Get match from opendota API via GET matches endpoint."""
        return await self.invoke("matches", match_id)
