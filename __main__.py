from __future__ import annotations

import asyncio
import logging
import sys

import aiohttp
import click

from bot import LueBot, setup_logging
from utils.database import create_pool

try:
    import uvloop  # type: ignore
except ImportError:
    # WINDOWS
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    # LINUX
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


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
        LueBot(session=session, pool=pool) as irenesbot,
    ):
        await irenesbot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
def main(click_ctx: click.Context) -> None:
    """Launches the bot."""
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            try:
                asyncio.run(start_the_bot())
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201


if __name__ == "__main__":
    main()
