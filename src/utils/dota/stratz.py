from __future__ import annotations

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    import aiohttp

    from .schemas import stratz as schemas

__all__ = ("StratzClient",)


class StratzClient:
    """A class for interacting with Stratz GraphQL API."""

    def __init__(self, *, bearer_token: str, session: aiohttp.ClientSession) -> None:
        self.bearer_token: str = bearer_token
        self.session: aiohttp.ClientSession = session

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

    async def get_items(self) -> schemas.Items:
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
