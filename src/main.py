"""
Python Launcher file for the bot.

Generally, it's preferred to use `make run` to run this bot, however you can use
`uv run src/main.py`, `python src/main.py`, etc. directly, if you like.
CLI supported flags can be viewed with `--help` flag.

License
-------
* This Source Code Form is subject to the terms of the [Mozilla Public License v2.0](<http://mozilla.org/MPL/2.0/>).
* Copyright (C) 2020-present [Aluerie](<https://github.com/Aluerie>).
"""

# uvloop existing only for Linux makes that reportMissingImports to be invalid for Linux, but valid for Windows
# TODO: is there any better way to approach this dilemma?
# pyright: reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

import asyncio
import logging
import platform
import sys
from typing import TYPE_CHECKING, Literal

import aiohttp
import asyncpg
import click

from config import env
from core import IreBot, get_eventsub_subscriptions, setup_logging
from utils import const

if TYPE_CHECKING:
    from types_.database import PoolTypedWithAny

try:
    import uvloop  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    # WINDOWS - uvloop does not support Windows
    RUNTIME = asyncio.run  # pyright: ignore[reportConstantRedefinition]
else:
    # LINUX
    RUNTIME = uvloop.run  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


async def create_pool() -> asyncpg.Pool[asyncpg.Record]:
    """Create AsyncPG Pool."""
    postgres_url = env.POSTGRES_VPS if platform.system() == "Linux" else env.POSTGRES_HOME
    return await asyncpg.create_pool(postgres_url, command_timeout=60, min_size=10, max_size=10, statement_cache_size=0)


async def start_the_bot(*, scopes_only: bool, owner_id: str, force_subscribe: bool, local: bool) -> None:
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
            local=local,
        ) as irebot,
    ):
        await irebot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
@click.option(
    "--scopes-only",
    "-s",
    is_flag=True,
    default=False,  # usual default: False ✅
    help=(
        "Launches the bot without any functionality except for Auth Token management."
        "This also show OATH urls with scopes for a bot account, the bot owner and broadcasters to authorize with."
        "The bot will add their tokens to the database upon authorization thanks to Auth Token management being on."
    ),
)
@click.option(
    "--owner",
    "-o",
    type=click.Choice(["irene", "aluerie"]),
    default="irene",  # usual default: "irene" ✅
    help=(
        "Which account to consider as bot's owner. Two options: `irene` or `aluerie`."
        "Sometimes I switch between those accounts."
        "The bot makes personal EventSubs subscriptions for the chosen account."
        "Also changes the logic of `is_owner` condition."
    ),
)
@click.option(
    "--force-subscribe",
    "-f",
    is_flag=True,
    default=False,  # usual default: False ✅
    help="Which value to pass into `force_subscribe` bot's kwarg",
)
@click.option(
    "--local",
    "-l",
    is_flag=True,
    default=True,  # usual default: True ✅
    help="Whether to use adapter with localhost (default) or remote host (currently ngrok-free for testing purposes).",
)
def main(
    click_ctx: click.Context,
    *,
    scopes_only: bool,
    owner: Literal["irene", "aluerie"],
    force_subscribe: bool,
    local: bool,
) -> None:
    """Launches the bot."""
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            owner_id: str = {"irene": const.UserID.Irene, "aluerie": const.UserID.Aluerie}[owner]
            try:
                RUNTIME(
                    start_the_bot(scopes_only=scopes_only, owner_id=owner_id, force_subscribe=force_subscribe, local=local)
                )
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201
            except asyncio.CancelledError:
                print("Aborted! The bot was interrupted with `asyncio.CancelledError`!")  # noqa: T201


if __name__ == "__main__":
    main()
