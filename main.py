from __future__ import annotations

import asyncio
import logging
import platform
import sys

import aiohttp
import asyncpg
import click

from bot import IreBot, setup_logging
from config import config

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


async def start_the_bot() -> None:
    """Start the bot."""
    log = logging.getLogger()
    try:
        pool = await create_pool()
    except Exception:
        click.echo("Could not set up PostgreSQL. Exiting.", file=sys.stderr)
        log.exception("Could not set up PostgreSQL. Exiting.")
        return

    async with (
        aiohttp.ClientSession() as session,
        pool as pool,
        IreBot(session=session, pool=pool) as irebot,
    ):
        await irebot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
def main(click_ctx: click.Context) -> None:
    """Launches the bot."""
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            try:
                RUNTIME(start_the_bot())
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201


if __name__ == "__main__":
    main()
