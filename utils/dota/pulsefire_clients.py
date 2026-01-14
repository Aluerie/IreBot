from __future__ import annotations

import collections
import logging
import random
import time
from typing import TYPE_CHECKING, Any, override

import orjson
from pulsefire.clients import BaseClient
from pulsefire.middlewares import http_error_middleware, json_response_middleware
from pulsefire.ratelimiters import BaseRateLimiter

from config import config

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pulsefire.invocation import Invocation

    from .schemas import steam_web_api, stratz

    type HeaderRateLimitInfo = Mapping[str, Sequence[tuple[int, int]]]


__all__ = (
    "SteamWebAPIClient",
    "StratzClient",
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SteamWebAPIClient(BaseClient):
    """Pulsefire client to work with Steam Web API."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.steampowered.com/",
            default_params={},
            default_headers={},
            default_queries={"key": config["TOKENS"]["STEAM"]},
            middlewares=[
                json_response_middleware(orjson.loads),
                http_error_middleware(),
            ],
        )

    async def get_real_time_stats(self, server_steam_id: int) -> steam_web_api.RealTimeStatsResponse:
        """GET /IDOTA2Match_570/GetMatchDetails/v1/.

        https://steamapi.xpaw.me/#IDOTA2MatchStats_570/GetRealtimeStats.
        """
        queries = {"server_steam_id": server_steam_id}  # noqa: F841
        return await self.invoke("GET", "/IDOTA2MatchStats_570/GetRealtimeStats/v1/")  # pyright: ignore[reportReturnType]


class DotaAPIsRateLimiter(BaseRateLimiter):
    """Dota 2 APIs rate limiter.

    This rate limiter can be served stand-alone for centralized rate limiting.
    """

    def __init__(self) -> None:
        self._track_syncs: dict[str, tuple[float, list[Any]]] = {}
        self.rate_limits_string: str = "Not Set Yet"
        self.rate_limits_ratio: float = 1.0
        self._index: dict[tuple[str, int, Any, Any, Any], tuple[int, int, float, float, float]] = (
            collections.defaultdict(lambda: (0, 0, 0, 0, 0))
        )

    @override
    async def acquire(self, invocation: Invocation) -> float:
        wait_for = 0
        pinging_targets = []
        requesting_targets = []
        request_time = time.time()
        for target in [
            ("app", 0, invocation.params.get("region", ""), invocation.method, invocation.urlformat),
            ("app", 1, invocation.params.get("region", ""), invocation.method, invocation.urlformat),
        ]:
            count, limit, expire, latency, pinged = self._index[target]
            pinging = pinged and request_time - pinged < 10
            if pinging:
                wait_for = max(wait_for, 0.1)
            elif request_time > expire:
                pinging_targets.append(target)
            elif request_time > expire - latency * 1.1 + 0.01 or count >= limit:
                wait_for = max(wait_for, expire - request_time)
            else:
                requesting_targets.append(target)
        if wait_for <= 0:
            if pinging_targets:
                self._track_syncs[invocation.uid] = (request_time, pinging_targets)
                for pinging_target in pinging_targets:
                    self._index[pinging_target] = (0, 0, 0, 0, time.time())
                wait_for = -1
            for requesting_target in requesting_targets:
                count, *values = self._index[requesting_target]
                self._index[requesting_target] = (count + 1, *values)  # type: ignore[reportArgumentType]

        return wait_for

    @override
    async def synchronize(self, invocation: Invocation, headers: dict[str, str]) -> None:
        response_time = time.time()
        request_time, pinging_targets = self._track_syncs.pop(invocation.uid, [None, None])
        if request_time is None:
            return

        if random.random() < 0.1:
            for prev_uid, (prev_request_time, _) in self._track_syncs.items():
                if response_time - prev_request_time > 600:
                    self._track_syncs.pop(prev_uid, None)

        try:
            header_limits, header_counts = self.analyze_headers(headers)
        except KeyError:
            for pinging_target in pinging_targets:  # type: ignore[reportArgumentType]
                self._index[pinging_target] = (0, 0, 0, 0, 0)
            return
        for scope, idx, *subscopes in pinging_targets:  # type: ignore[reportArgumentType]
            if idx >= len(header_limits[scope]):
                self._index[scope, idx, *subscopes] = (0, 10**10, response_time + 3600, 0, 0)
                continue
            self._index[scope, idx, *subscopes] = (
                header_counts[scope][idx][0],
                header_limits[scope][idx][0],
                header_limits[scope][idx][1] + response_time,
                response_time - request_time,
                0,
            )

    def analyze_headers(self, headers: dict[str, str]) -> tuple[HeaderRateLimitInfo, HeaderRateLimitInfo]:
        raise NotImplementedError


class StratzAPIRateLimiter(DotaAPIsRateLimiter):
    @override
    def analyze_headers(self, headers: dict[str, str]) -> tuple[HeaderRateLimitInfo, HeaderRateLimitInfo]:
        self.rate_limits_string = "\n".join(
            [
                f"{timeframe}: "
                f"{headers[f'X-RateLimit-Remaining-{timeframe}']}/{headers[f'X-RateLimit-Limit-{timeframe}']}"
                for timeframe in ("Second", "Minute", "Hour", "Day")
            ],
        )
        self.rate_limits_ratio = int(headers["X-RateLimit-Remaining-Day"]) / int(headers["X-RateLimit-Limit-Day"])

        periods = [
            ("Second", 1),
            ("Minute", 60),
            ("Hour", 60 * 60),
            ("Day", 60 * 60 * 24),
        ]
        header_limits = {"app": [(int(headers[f"X-RateLimit-Limit-{name}"]), period) for name, period in periods]}
        header_counts = {"app": [(int(headers[f"X-RateLimit-Remaining-{name}"]), period) for name, period in periods]}
        return header_limits, header_counts


class StratzClient(BaseClient):
    """Pulsefire client to boilerplate work with Stratz GraphQL queries.

    You can play around with queries here: https://api.stratz.com/graphiql/
    Note "i" means it's a fancy UI version.
    """

    def __init__(self) -> None:
        self.rate_limiter = StratzAPIRateLimiter()
        super().__init__(
            base_url="https://api.stratz.com/graphql",
            default_params={},
            default_headers={
                "User-Agent": "STRATZ_API",
                "Authorization": f"Bearer {config['TOKENS']['STRATZ_BEARER']}",
                "Content-Type": "application/json",
            },
            default_queries={},
            middlewares=[
                json_response_middleware(orjson.loads),
                http_error_middleware(),
                # rate_limiter_middleware(self.rate_limiter),
            ],
        )

    async def get_items(self) -> stratz.ItemsResponse:
        """Queries Dota 2 Hero Item Constants."""
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
        json = {"query": query}  # noqa: F841
        return await self.invoke("POST", "")  # pyright: ignore[reportReturnType]
