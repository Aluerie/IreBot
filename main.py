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
    help="Show oath urls with scopes for broadcaster and bot accounts to authorize with (bot features won't be activated)",
)
@click.option(
    "--owner",
    "-o",
    type=click.Choice(["irene", "aluerie"]),
    default="irene",  # usual default: "irene" ✅
    help="Which account to assume as the bot owner's account.",
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
    """Launches the bot.

    Parameters
    ----------
    owner: str
        Which account to consider as bot's owner. Two options: `irene` or `aluerie`.
        Sometimes I switch between those accounts.
        The bot makes personal EventSubs subscriptions for the chosen account.
        Also changes the logic of "is_owner" condition.

    local: bool
        Whether to use adapter with localhost (default behavior) or with remote host.
        Currently I'm using ngrok-free as a free domain app is being used for testing purposes.

    DISCLAIMERS FOR FUTURE !!!
    --------------------------
    1.  If we switch `owner` parameter or default value - we have to run the bot with `force_subscribe=True` once.
        The conduits stay alive only for 72 hours.
        So it's almost certain the subscriptions will be dead for the other account when we decide to switch.

    A small guide for adapter-host setup (I will forget).
    -----------------------------------------------------
    Step 0. Decide whether we use local adapter (localhost) or remote (currently - ngrok);
        Remote allows other people to authorize the bot permissions, but requires a web app running.
    Step 1. Twitch Developer Console at Irene_Adler__ account -> OAuths Redirect URLs:
        local: http://localhost:4343/oauth/callback
        ngrok: https://parrot-thankful-trivially.ngrok-free.app/oauth/callback
    Step 2.
        local: no actions needed;
        ngrok:
            Run `ngrok http --url=parrot-thankful-trivially.ngrok-free.app 4343` in PC/VPS's terminal.
            Note that the port should be 4343, as twitchio adapter works on it as well.
            Ignore ngrok dashboard saying port 80, it's just an example.
    Step 3.
        Simply run the bot, i.e. `uv run main.py`.
        Now  users should be able to visit a link like this
            local: http://localhost:4343/oauth?scopes=channel:bot&force_verify=true
            ngrok: https://parrot-thankful-trivially.ngrok-free.app/oauth?scopes=channel:bot&force_verify=true
        to authorize the bot. Note, to get a proper link with ALL proper scopes - launch the bot in `scopes-only` mode.


    """
    if click_ctx.invoked_subcommand is None:
        with setup_logging():
            owner_id: str = {"irene": const.UserID.Irene, "aluerie": const.UserID.Aluerie}[owner]
            try:
                RUNTIME(
                    start_the_bot(
                        scopes_only=scopes_only,
                        owner_id=owner_id,
                        force_subscribe=force_subscribe,
                        local=local,
                    )
                )
            except KeyboardInterrupt:
                print("Aborted! The bot was interrupted with `KeyboardInterrupt`!")  # noqa: T201


if __name__ == "__main__":
    main()
