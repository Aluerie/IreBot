from __future__ import annotations

import asyncio
import logging
import platform
import sys
from typing import TYPE_CHECKING

import aiohttp
import asyncpg
import click

from bot import IreBot, get_eventsub_subscriptions, setup_logging
from config import config

if TYPE_CHECKING:
    from types_.database import PoolTypedWithAny

try:
    import uvloop  # pyright: ignore[reportMissingImports]
except ImportError:
    # WINDOWS
    RUNTIME = asyncio.run  # pyright: ignore[reportConstantRedefinition]
else:
    # LINUX
    RUNTIME = uvloop.run


async def create_pool() -> asyncpg.Pool[asyncpg.Record]:
    """Create AsyncPG Pool."""
    postgres_url = config["POSTGRES"]["VPS"] if platform.system() == "Linux" else config["POSTGRES"]["HOME"]
    return await asyncpg.create_pool(
        postgres_url,
        command_timeout=60,
        min_size=10,
        max_size=10,
        statement_cache_size=0,
    )


async def start_the_bot(*, scopes_only: bool) -> None:
    """Start the bot."""
    log = logging.getLogger()
    try:
        # Unfortunate `asyncpg` typing crutch. Read `types_.database` for more
        pool: PoolTypedWithAny = await create_pool()  # pyright: ignore[reportAssignmentType]
    except Exception:
        msg = "Could not set up PostgreSQL. Exiting."
        click.echo(msg, file=sys.stderr)
        log.exception(msg)
        return

    subscriptions = await get_eventsub_subscriptions(pool)

    async with (
        aiohttp.ClientSession() as session,
        pool as pool,
        IreBot(
            session=session,
            pool=pool,
            subscriptions=subscriptions,
            scopes_only=scopes_only,
        ) as irebot,
    ):
        await irebot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
@click.option(
    "--scopes-only",
    "-s",
    is_flag=True,
    default=False,
    help="Show oath urls with scopes for broadcaster and bot accounts to authorize with (bot features won't be activated)",
)
def main(click_ctx: click.Context, *, scopes_only: bool) -> None:
    """Launches the bot."""
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            try:
                RUNTIME(start_the_bot(scopes_only=scopes_only))
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201


if __name__ == "__main__":
    main()
