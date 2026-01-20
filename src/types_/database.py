from typing import Any, override

import asyncpg


class PoolTypedWithAny(asyncpg.Pool[asyncpg.Record]):
    """Fake Type Class.

    For typing purposes, our `bot.pool` will be "type-ignore"'d-as `PoolTypedWithAny`
    that allows us to properly type the return values via narrowing like mentioned in instructions above
    without hundreds of "type: ignore" notices for each TypedDict.

    I could use Protocol to type it all, but `async-stubs` provide a good job in typing most of the stuff
    and we also don't lose doc-string this way.

    * Right now, asyncpg is untyped so this is better than the current status quo
    * If we ever need the regular Pool type we have `bot.database` without any shenanigans.
    """

    # all methods below were changed from "asyncpg.Record" to "Any"

    @override
    async def fetch(self, query: str, *args: Any, timeout: float | None = None) -> list[Any]: ...

    @override
    async def fetchrow(self, query: str, *args: Any, timeout: float | None = None) -> Any: ...
