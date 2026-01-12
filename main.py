from __future__ import annotations

import asyncio
import logging
import platform
import sys
from typing import TYPE_CHECKING, Literal

import aiohttp
import asyncpg
import click

from bot import IreBot, get_eventsub_subscriptions, setup_logging
from config import config
from utils import const

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


async def start_the_bot(*, scopes_only: bool, owner_id: str, force_subscribe: bool, ngrok: bool) -> None:
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

    subscriptions = await get_eventsub_subscriptions(pool, owner_id)

    async with (
        aiohttp.ClientSession() as session,
        pool as pool,
        IreBot(
            session=session,
            pool=pool,
            subscriptions=subscriptions,
            scopes_only=scopes_only,
            owner_id=owner_id,
            force_subscribe=force_subscribe,
            ngrok=ngrok,
        ) as irebot,
    ):
        await irebot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
@click.option(
    "--scopes-only",
    "-s",
    is_flag=True,
    default=True,
    help="Show oath urls with scopes for broadcaster and bot accounts to authorize with (bot features won't be activated)",
)
@click.option(
    "--owner",
    "-o",
    type=click.Choice(["irene", "aluerie"]),
    default="irene",
    help="Which account to assume as the bot owner's account.",
)
@click.option(
    "--force-subscribe",
    "-f",
    is_flag=True,
    default=False,
    help="Which value to pass into `force_subscribe` bot's kwarg",
)
@click.option(
    "--ngrok",
    "-n",
    is_flag=True,
    default=True,  # False
    help="Whether to use adapter with ngrok's app or localhost (default).",
)
def main(
    click_ctx: click.Context,
    *,
    scopes_only: bool,
    owner: Literal["irene", "aluerie"],
    force_subscribe: bool,
    ngrok: bool,
) -> None:
    """Launches the bot.

    Parameters
    ----------
    owner: str
        Which account to consider as bot's owner. Two options: `irene` or `aluerie`.
        Sometimes I switch between those accounts.
        The bot makes personal EventSubs subscriptions for the chosen account.
        Also changes the logic of "is_owner" condition.

    WARNING!!!
    ----------
    If we switch `owner` parameter or default value - we have to run the bot with `force_subscribe=True` once.
    The conduits stay alive only for 72 hours.
    """
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            owner_id: str = {"irene": const.UserID.Irene, "aluerie": const.UserID.Aluerie}[owner]
            try:
                RUNTIME(
                    start_the_bot(scopes_only=scopes_only, owner_id=owner_id, force_subscribe=force_subscribe, ngrok=ngrok)
                )
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201


if __name__ == "__main__":
    main()
