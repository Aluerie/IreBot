from __future__ import annotations

import asyncio
import logging
import platform
from typing import TYPE_CHECKING, TypedDict, override

import discord
import twitchio
from twitchio import eventsub
from twitchio.ext import commands

# from twitchio.web import StarletteAdapter
from config import config, replace_secrets
from ext import EXTENSIONS
from ext.dota.api import Dota2Client
from utils import const, errors

from .bases import ireloop
from .exc_manager import ExceptionManager

if TYPE_CHECKING:
    import asyncpg
    from aiohttp import ClientSession

    from types_.database import PoolTypedWithAny

    class LoadTokensQueryRow(TypedDict):
        user_id: str
        token: str
        refresh: str


__all__ = ("IreBot",)

log = logging.getLogger(__name__)


class IreBot(commands.Bot):
    """Main class for IreBot.

    Essentially subclass over TwitchIO's Client.
    Used to interact with the Twitch API, EventSub and more.
    Includes TwitchIO's `ext.commands` extension to organize components/commands framework.

    Note on the name
    ----
    The name `IrenesBot` is used mainly for display purposes here:
        * the bot's twitch account user name (just so it's clear that it's Aluerie's bot);
        * the bot's Steam account's display name;

    Name `IreBot` is pretty much used elsewhere:
        * the GitHub repository name and `README.md` file.
        * class name;
        * folder name;
        * systemd service name;
        * discord notifications webhook names;
        * category name in my own ToDo list;
        * etc :D

    Maybe I will change this in future to be less confusing, but I think current situation is fine.
    """

    if TYPE_CHECKING:
        logs_via_webhook_handler: logging.Handler
        dota: Dota2Client

    def __init__(
        self,
        *,
        session: ClientSession,
        pool: asyncpg.Pool[asyncpg.Record],
    ) -> None:
        """Initiate IreBot."""
        self.prefixes: tuple[str, ...] = ("!", "?", "$")
        # adapter: StarletteAdapter = StarletteAdapter(
        #     host="0.0.0.0",
        #     domain="https://parrot-thankful-trivially.ngrok-free.app",
        #     eventsub_secret=config.EVENTSUB_SECRET,
        # )
        super().__init__(
            client_id=config["TWITCH"]["CLIENT_ID"],
            client_secret=config["TWITCH"]["CLIENT_SECRET"],
            bot_id=const.UserID.Bot,
            owner_id=const.UserID.Irene,
            prefix=self.prefixes,
            # adapter=adapter,
            # TODO: fill in scopes= argument once we figure out what it's used for :x
        )
        self.database: asyncpg.Pool[asyncpg.Record] = pool
        # asyncpg typehinting crutch, read `utils.database` for more
        self.pool: PoolTypedWithAny = pool  # pyright: ignore[reportAttributeAccessIssue]
        self.session: ClientSession = session
        self.extensions: tuple[str, ...] = EXTENSIONS

        self.exc_manager = ExceptionManager(self)

        self.irene_online: bool = False

    def print_bot_oauth(self) -> None:
        """Print a link for me (developer) to click and authorize the bot scopes for the bot account.

        Required for proper work of Twitch Eventsub events and API requests.
        """
        scopes = "%20".join(
            [
                "user:read:chat",
                "user:write:chat",
                "user:bot",
                "moderator:read:followers",
                "moderator:manage:shoutouts",
                "moderator:manage:announcements",
                "moderator:manage:banned_users",
                "clips:edit",
            ],
        )
        link = f"http://localhost:4343/oauth?scopes={scopes}&force_verify=true"
        print(f"🤖🤖🤖 BOT OAUTH LINK: 🤖🤖🤖\n{link}")  # noqa: T201

    def print_broadcaster_oauth(self) -> None:
        """Print a link for streamers to click and authorize the scopes for the bot.

        Required for proper work of Twitch Eventsub events and API requests.

        Notes
        -----
        * Currently my developer console has localhost as a callback: http://localhost:4343/oauth/callback
            But if we ever switch to multi-streams setup then I already have some things set up with
            * https://parrot-thankful-trivially.ngrok-free.app/oauth/callback (in developer console)
            * `ngrok http --url=parrot-thankful-trivially.ngrok-free.app 80` (in my/vps terminal)
            Look ngrok dashboard for more.

            With it a user needs to go to a link like this:
            https://parrot-thankful-trivially.ngrok-free.app/oauth?scopes=channel:bot&force_verify=true
        """
        scopes = "%20".join(
            [
                "channel:bot",
                "channel:read:ads",
                "channel:moderate",
                "channel:read:redemptions",
                "channel:manage:broadcast",
                "channel:read:subscriptions",
            ],
        )
        link = f"http://localhost:4343/oauth?scopes={scopes}&force_verify=true"
        print(f"🎬🎬🎬 BROADCASTER OAUTH LINK: 🎬🎬🎬\n{link}")  # noqa: T201

    @override
    async def setup_hook(self) -> None:
        """
        Setup Hook. Method called after `.login` has been called but before the bot is ready.

        TwitchIO OAuth Tokens Magic
        ---------------------------
        In order to get the required oath tokens into the database when running the bot
        for the first time (or after adding extra scopes):
            1. Uncomment three first lines in this function;
            2. Run the bot;
            3. Click generated links using proper accounts:
                (i.e. broadcaster = the browser with streamer account logged in);
            4. The bot will update the tokens in the database automatically;
            5. Comment the lines back. In normal state, they should be commented.

        """
        # self.print_bot_oauth()  # noqa: ERA001, RUF100
        # self.print_broadcaster_oauth()  # noqa: ERA001, RUF100
        # return  # noqa: ERA001, RUF100

        for ext in self.extensions:
            (await self.load_module(ext))

        await self.create_eventsub_subscriptions()
        self.check_if_online.start()

    async def create_eventsub_subscriptions(self) -> None:
        """Subscribe to all EventSub subscriptions that are required for the bot to work.

        The function also includes (in code) a table showcasing which subscriptions/scopes are required for what.
        For more links:

        TwitchDev Docs
        --------------
            * Eventsub: https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types
            * Scopes:   https://dev.twitch.tv/docs/authentication/scopes/

        TwitchIO  Docs
        --------------
            * Events:   https://twitchio.dev/en/dev-3.0/references/events.html
            * Models:   https://twitchio.dev/en/dev-3.0/references/eventsub_models.html
        """
        # it's just a personal bot so things are relatively simple about broadcaster<->bot relation ;)
        broadcaster = const.UserID.Irene
        bot = const.UserID.Bot

        # EventSub Subscriptions Table (order - function name sorted by alphabet).
        # Subscription Name                     Permission
        # ------------------------------------------------------
        # ✅ Ad break begin                        channel:read:ads
        sub = eventsub.AdBreakBeginSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub, token_for=broadcaster, as_bot=False)
        # Bans                                  channel:moderate
        sub = eventsub.ChannelBanSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub, token_for=broadcaster, as_bot=False)
        # ✅ Follows                               moderator:read:followers
        sub = eventsub.ChannelFollowSubscription(broadcaster_user_id=broadcaster, moderator_user_id=bot)
        await self.subscribe_websocket(payload=sub)
        # ✅ Channel Points Redeem                 channel:read:redemptions or channel:manage:redemptions
        sub = eventsub.ChannelPointsRedeemAddSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub, token_for=broadcaster, as_bot=False)
        # ✅ Message                               user:read:chat from the chatting user, channel:bot from broadcaster
        sub = eventsub.ChatMessageSubscription(broadcaster_user_id=broadcaster, user_id=bot)
        await self.subscribe_websocket(payload=sub)
        # ❓ Raids to the channel                  No authorization required
        sub = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub)
        # ✅ Stream went offline                   No authorization required
        sub = eventsub.StreamOfflineSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub)
        # ✅ Stream went live                      No authorization required
        sub = eventsub.StreamOnlineSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub)
        # ✅ Channel Update (title/game)           No authorization required
        sub = eventsub.ChannelUpdateSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub)
        # ❓ Channel Subscribe (paid)              channel:read:subscriptions
        sub = eventsub.ChannelSubscribeSubscription(broadcaster_user_id=broadcaster)
        await self.subscribe_websocket(payload=sub, token_for=broadcaster, as_bot=False)

    @override
    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens internally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
            INSERT INTO ttv_tokens (user_id, token, refresh)
            VALUES ($1, $2, $3)
            ON CONFLICT(user_id)
            DO UPDATE SET
                token = excluded.token,
                refresh = excluded.refresh;
        """
        await self.pool.execute(query, resp.user_id, token, refresh)
        log.info("Added token to the database for user: %s", resp.user_id)
        return resp

    @override
    async def load_tokens(self, _: str | None = None) -> None:  # _ is `path`
        # We don't need to call this manually, it is called in .login() from .start() internally...

        rows: list[LoadTokensQueryRow] = await self.pool.fetch("""SELECT * from ttv_tokens""")
        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    @override
    async def start(self) -> None:
        if "ext.dota" in self.extensions:
            self.dota = Dota2Client(self)
            await asyncio.gather(
                super().start(),
                self.dota.login(),
            )
        else:
            await super().start()

    @override
    async def close(self) -> None:
        if hasattr(self, "dota"):
            await self.dota.close()
        await super().close()

    # @override  # interesting that it's not an override
    async def event_ready(self) -> None:
        """Event that is dispatched when the `Client` is ready and has completed login."""
        log.info("%s is ready as bot_id = %s", self.__class__.__name__, self.bot_id)
        if hasattr(self, "dota"):
            await self.dota.wait_until_ready()

    @override
    async def event_command_error(self, payload: commands.CommandErrorPayload) -> None:
        """Called when error happens during command invoking."""
        command = payload.context.command
        if command and command.has_error and payload.context.error_dispatched:
            return

        ctx = payload.context
        error = payload.exception

        # we aren't interested in the chain traceback:
        error = error.original if isinstance(error, commands.CommandInvokeError) and error.original else error

        match error:
            case errors.IreBotError():
                # errors defined by me - just send the string
                await ctx.send(str(error))
            case commands.CommandNotFound():
                #  otherwise we just spam console with commands from other bots and from my event thing
                log.info("CommandNotFound: %s", payload.exception)
            case commands.GuardFailure():
                guard_mapping = {
                    "is_moderator.<locals>.predicate": (
                        f"Only moderators are allowed to use this command {const.FFZ.peepoPolice}"
                    ),
                    "is_vps.<locals>.predicate": (
                        f"Only production bot allows usage of this command {const.FFZ.peepoPolice}"
                    ),
                    "is_owner.<locals>.predicate": (
                        f"Only Irene is allowed to use this command {const.FFZ.peepoPolice}"
                    ),
                    "is_online.<locals>.predicate": (
                        f"This commands is only allowed when stream is online {const.FFZ.peepoPolice}"
                    ),
                }
                await ctx.send(guard_mapping.get(error.guard.__qualname__, str(error)))
            case twitchio.HTTPException():
                await ctx.send(
                    f"{error.extra.get('error', 'Error')} "
                    f"{error.extra.get('status', 'XXX')}: "
                    f"{error.extra.get('message', 'Unknown')} {const.STV.dankFix}",
                )
            case commands.MissingRequiredArgument():
                await ctx.send(
                    f'You need to provide "{error.param.name}" argument for this command {const.FFZ.peepoPolice}',
                )
            case commands.CommandOnCooldown():
                command_name = f"{ctx.prefix}{command.name}" if command else "this command"
                await ctx.send(f"Command {command_name} is on cooldown! Try again in {error.remaining:.0f} sec.")

            # case commands.BadArgument():
            #     log.warning("%s %s", error.name, error)
            #     await ctx.send(f"Couldn't find any {error.name} like that")
            # case commands.ArgumentError():
            #     await ctx.send(str(error))

            case _:
                await ctx.send(f"{error.__class__.__name__}: {replace_secrets(str(error))}")

                command_name = getattr(ctx.command, "name", "unknown")

                embed = (
                    discord.Embed(
                        colour=ctx.chatter.colour.code if ctx.chatter.colour else 0x890620,
                        title=f"Error in `!{command_name}`",
                    )
                    .add_field(
                        name="Command Args",
                        value=(
                            "```py\n" + "\n".join(f"[{name}]: {value!r}" for name, value in ctx.kwargs.items()) + "```"
                            if ctx.kwargs
                            else "```py\nNo arguments```"
                        ),
                        inline=False,
                    )
                    .set_author(
                        name=ctx.chatter.display_name,
                        icon_url=(await ctx.chatter.user()).profile_image,
                    )
                    .set_footer(
                        text=f"event_command_error: {command_name}",
                        icon_url=(await ctx.broadcaster.user()).profile_image,
                    )
                )
                await self.exc_manager.register_error(error, embed=embed)

    @override
    async def event_error(self, payload: twitchio.EventErrorPayload) -> None:
        embed = (
            discord.Embed()
            .add_field(name="Exception", value=f"`{payload.error.__class__.__name__}`")
            .set_footer(text=f"event_error: `{payload.listener.__qualname__}`")
        )
        await self.exc_manager.register_error(payload.error, embed=embed)

    def webhook_from_url(self, url: str) -> discord.Webhook:
        """A shortcut function with filled in discord.Webhook.from_url args."""
        return discord.Webhook.from_url(url=url, session=self.session)

    @discord.utils.cached_property
    def logger_webhook(self) -> discord.Webhook:
        """A webhook in hideout's #logger channel."""
        return self.webhook_from_url(config["WEBHOOKS"]["LOGGER"])

    @discord.utils.cached_property
    def error_webhook(self) -> discord.Webhook:
        """A webhook in hideout server to send errors/notifications to the developer(-s)."""
        return self.webhook_from_url(config["WEBHOOKS"]["ERROR"])

    @discord.utils.cached_property
    def error_ping(self) -> str:
        """Error Role ping used to notify the developer(-s) about some errors."""
        return "<@&1306631362870120600>" if platform.system() == "Windows" else "<@&1116171071528374394>"

    async def irene_stream(self) -> twitchio.Stream | None:
        """Shortcut to get @Irene's stream."""
        return next(iter(await self.fetch_streams(user_ids=[const.UserID.Irene])), None)

    @ireloop(count=1)
    async def check_if_online(self) -> None:
        """Check if aluerie is online - used to make my own (proper) online event instead of twitchio's."""
        await asyncio.sleep(1.0)  # just in case;
        if await self.irene_stream():
            self.irene_online = True
            self.dispatch("aluerie_online")

    async def event_stream_online(self, _: twitchio.StreamOnline) -> None:
        """Instead of the twitchio event - dispatch my own online event.

        The difference is that my event accounts for the state of my stream when the bot restarts.
        """
        self.irene_online = True
        self.dispatch("aluerie_online")

    async def event_stream_offline(self, _: twitchio.StreamOffline) -> None:
        """Instead of the twitchio event - dispatch my own offline event."""
        self.irene_online = False
        self.dispatch("aluerie_offline")

    # def show_oauth(self) -> None:
    #     oauth = twitchio.authentication.OAuth(
    #         client_id=config.TTV_DEV_CLIENT_ID,
    #         client_secret=config.TTV_DEV_CLIENT_SECRET,
    #         redirect_uri="http://localhost:4343/oauth/callback",
    #         scopes=twitchio.Scopes(
    #             [
    #                 "channel:bot",
    #                 "channel:read:ads",
    #                 "channel:moderate",
    #                 "moderator:read:followers",
    #                 "channel:read:redemptions",
    #             ]
    #         ),
    #     )
    #     #
    #     #  # Generate the authorization URL
    #     auth_url = oauth.get_authorization_url(force_verify=True)
    #     print(auth_url)  # noa: T201
