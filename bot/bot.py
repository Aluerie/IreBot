from __future__ import annotations

import asyncio
import datetime
import logging
import platform
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict, override

import discord
import twitchio
from twitchio import eventsub
from twitchio.ext import commands
from twitchio.web import StarletteAdapter

from config import config, replace_secrets
from ext import get_extensions
from utils import const, errors
from utils.dota import Dota2Client

from .bases import IreContext
from .exc_manager import ExceptionManager

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from types_.database import PoolTypedWithAny

    class LoadTokensQueryRow(TypedDict):
        user_id: str
        token: str
        refresh: str

    class GetMemberAccountsQueryRow(TypedDict):
        user_id: str


__all__ = (
    "IreBot",
    "Streamer",
    "get_eventsub_subscriptions",
)

log = logging.getLogger(__name__)


def get_public_subscriptions(member: str, bot: str) -> list[twitchio.eventsub.SubscriptionPayload]:
    """Get member EventSub subscriptions.

    Public accounts are people who are only allowed to use public features.
    Their accounts do not need all EventSub models activated.
    """
    return [
        eventsub.ChatMessageSubscription(broadcaster_user_id=member, user_id=bot),
        eventsub.StreamOfflineSubscription(broadcaster_user_id=member),
        eventsub.StreamOnlineSubscription(broadcaster_user_id=member),
    ]


async def get_eventsub_subscriptions(pool: PoolTypedWithAny, owner: str) -> list[twitchio.eventsub.SubscriptionPayload]:
    """Get all EventSub subscriptions that are required for the bot's EventSub related features to work.

    The function also includes (in code) a table showcasing which subscriptions/scopes are required for what.
    For more links:

    More links
    ----------
    TwitchDev Docs
        * Eventsub:        https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types
        * Scopes:          https://dev.twitch.tv/docs/authentication/scopes/
    TwitchIO  Docs
        * Event Reference: https://twitchio.dev/en/latest/references/events/events.html
        * Models:          https://twitchio.dev/en/latest/references/eventsub/index.html
    """
    bot = const.UserID.Bot
    subscriptions: list[eventsub.SubscriptionPayload] = []

    # 1. My personal account to have all the features on.
    subscriptions.extend(
        [
            # EventSub Subscriptions Table (order - function name sorted by alphabet).
            # Subscription Name                     Permission
            # ------------------------------------------------------
            # ✅ Ad break begin                         channel:read:ads
            eventsub.AdBreakBeginSubscription(broadcaster_user_id=owner),
            # ✅ Bans                                   channel:moderate
            eventsub.ChannelBanSubscription(broadcaster_user_id=owner),
            # ✅ Follows                                moderator:read:followers
            eventsub.ChannelFollowSubscription(broadcaster_user_id=owner, moderator_user_id=bot),
            # ✅ Channel Points Redeem                  channel:read:redemptions or channel:manage:redemptions
            eventsub.ChannelPointsRedeemAddSubscription(broadcaster_user_id=owner),
            # ✅ Message                                user:read:chat from the chatbot, channel:bot from broadcaster
            eventsub.ChatMessageSubscription(broadcaster_user_id=owner, user_id=bot),
            # ✅ Raids to the channel                   No authorization required
            eventsub.ChannelRaidSubscription(to_broadcaster_user_id=owner),
            # ✅ Stream went offline                    No authorization required
            eventsub.StreamOfflineSubscription(broadcaster_user_id=owner),
            # ✅ Stream went live                       No authorization required
            eventsub.StreamOnlineSubscription(broadcaster_user_id=owner),
            # ✅ Channel Update (title/game)            No authorization required
            eventsub.ChannelUpdateSubscription(broadcaster_user_id=owner),
            # ❓ Channel Subscribe (paid)               channel:read:subscriptions
            eventsub.ChannelSubscribeSubscription(broadcaster_user_id=owner),
            # ❓ Channel Subscribe Message (paid)       channel:read:subscriptions
            eventsub.ChannelSubscribeMessageSubscription(broadcaster_user_id=owner),
        ]
    )

    # 2. Public member accounts (i.e. other people using my bot) only have some public features on
    # so we only need a subset of eventsub-subscriptions.
    query = """
        SELECT t.user_id
        FROM ttv_tokens t
        JOIN ttv_streamers s ON t.user_id = s.user_id
        WHERE active = TRUE AND t.user_id != ANY($1)
    """
    exclude_ids = {const.UserID.Aluerie, const.UserID.Irene, const.UserID.Bot}
    public_rows: list[GetMemberAccountsQueryRow] = await pool.fetch(query, exclude_ids)
    for user in public_rows:
        subscriptions.extend(get_public_subscriptions(user["user_id"], bot))
    return subscriptions


@dataclass
class Streamer:
    """#TODO."""

    id: str
    online: bool = False
    started_dt: datetime.datetime | None = None


class IreBot(commands.AutoBot):
    """Main class for IreBot.

    Essentially subclass over TwitchIO's Client.
    Used to interact with the Twitch API, EventSub and more.
    Includes TwitchIO's `ext.commands` extension to organize components/commands framework.

    Note on the name
    ----------------
    The name `IrenesBot` is used mainly for display purposes here:
        * the bot's twitch account user name (just so it's clear that it's Irene's bot);
        * the bot's Steam account's display name;

    Name `IreBot` is pretty much used elsewhere:
        * the GitHub repository name and `README.md` file.
        * class name;
        * folder name;
        * systemd service name;
        * discord notifications webhook names;
        * category name in my own ToDo list;
        * etc.

    Maybe I will change this in future to be less confusing, but I think current situation is fine.
    """

    if TYPE_CHECKING:
        dota: Dota2Client
        launch_time: datetime.datetime
        logs_via_webhook_handler: logging.Handler
        owner_id: str  # it's "str | None" in twitchio, but we do supply it directly.

    def __init__(
        self,
        *,
        session: ClientSession,
        pool: PoolTypedWithAny,
        subscriptions: list[eventsub.SubscriptionPayload],
        scopes_only: bool,
        owner_id: str,
        force_subscribe: bool,
        local: bool,
    ) -> None:
        """Initiate IreBot."""
        self.prefixes: tuple[str, ...] = ("!", "?", "$")
        if local:
            self.domain = "http://localhost:4343"
            adapter = None
        else:
            self.domain = "https://parrot-thankful-trivially.ngrok-free.app"
            adapter = StarletteAdapter(
                host="0.0.0.0",  # noqa: S104
                domain=self.domain,
                eventsub_secret=config["TOKENS"]["EVENTSUB"],
            )
        super().__init__(
            client_id=config["TWITCH"]["CLIENT_ID"],
            client_secret=config["TWITCH"]["CLIENT_SECRET"],
            bot_id=const.UserID.Bot,
            owner_id=owner_id,
            prefix=self.prefixes,
            adapter=adapter,  # pyright: ignore[reportArgumentType], it's hinted as `NotRequired` while I need to use `None`.
            subscriptions=subscriptions,
            force_subscribe=force_subscribe,  # Set to `True` if we need urgent manual refreshing eventsub subs.
        )
        self.session: ClientSession = session
        self.pool: PoolTypedWithAny = pool
        self.scopes_only: bool = scopes_only

        self.test: bool = platform.system() == "Windows"  # TODO: I don't like it;
        self.extensions: tuple[str, ...] = get_extensions(test=self.test)
        self.exc_manager = ExceptionManager(self)

        self.streamers: dict[str, Streamer] = {}

    def show_oauth_helper(self, scopes: list[str], prefix: str) -> str:
        """Helper function for `show_bot_oauth`, `show_personal_oauth`, `show_public_oauth`.

        The authorization is required for proper work of Twitch Eventsub events and API requests.
        Currently, we separate bot features into two categories:
        * Personal - that are only used by me;
        * Public - that I allow to be used by everybody;
        They require different sets of scopes. And also, we need a separate oauth for the bot account.
        Therefore, we have 3 distinct links depending on which account should click on it.

        """
        link = f"{self.domain}/oauth?scopes={'+'.join(scopes)}&force_verify=true"
        return f"{prefix}\n{link}"

    def show_bot_oauth(self) -> str:
        """Print a link for me (developer) to click and authorize the bot scopes for the bot account.

        Note, that we need to login with the bot account (do not use this link for personal accounts).
        Required for proper work of Twitch Eventsub events and API requests.
        """
        scopes = [
            "user:read:chat",
            "user:write:chat",
            "user:bot",
            "moderator:read:followers",
            "moderator:manage:shoutouts",
            "moderator:manage:announcements",
            "moderator:manage:banned_users",
            "clips:edit",
        ]
        return self.show_oauth_helper(scopes, "🤖🤖🤖 BOT OAUTH LINK: 🤖🤖🤖")

    def show_personal_oauth(self) -> str:
        """Print a link for me (personal bot user with all the features) to click and authorize the scopes for the bot."""
        scopes = [
            "channel:bot",
            "channel:read:ads",
            "channel:moderate",
            "channel:read:redemptions",
            "channel:manage:redemptions",
            "channel:manage:broadcast",
            "channel:read:subscriptions",
        ]
        return self.show_oauth_helper(scopes, "🎬🎬🎬 PERSONAL OAUTH LINK: 🎬🎬🎬")

    def show_public_oauth(self) -> str:
        """Print a link for public streamers to click and authorize the scopes for the bot."""
        scopes = [
            "channel:bot",
        ]
        return self.show_oauth_helper(scopes, "🌈🌈🌈 PUBLIC OAUTH LINK: 🌈🌈🌈")

    @override
    async def setup_hook(self) -> None:
        """
        Setup Hook. Method called after `.login` has been called but before the bot is ready.

        TwitchIO OAuth Tokens Magic
        ---------------------------
        In order to get the required oath tokens into the database when running the bot
        for the first time (or after adding extra scopes):
            1. Run the bot with `uv run main.py -s`;
            2. Click generated links using proper accounts:
                * bot - bot account (@IrenesBot)
                * personal - my own account
                * public - public accounts
            3. The bot will update the tokens in the database automatically;
            4. Run the bot normally (with `uv run main.py`).

        """
        if self.scopes_only:
            msg = (
                "Scopes Only Mode: print oauth urls and start the bot in adapter-only mode (no extensions/commands enabled)."
                "\n"
                f"{self.show_bot_oauth()}\n"
                f"{self.show_personal_oauth()}\n"
                f"{self.show_public_oauth()}\n"
            )
            log.warning(msg)
        else:
            for ext in self.extensions:
                await self.load_module(ext)

    @override
    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        """Triggered when a (new) user authorizes the bot scopes using oauth link.

        Conduits require subscribing to new users or updated oauth scopes urls.
        Otherwise we need to use `force_subscribe` bot kwarg.

        Source
        ------
        Example `basic_conduits.py` by TwitchIO:
        * https://github.com/PythonistaGuild/TwitchIO/blob/main/examples/basic_conduits/main.py
        """
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        subs: list[eventsub.SubscriptionPayload] = get_public_subscriptions(payload.user_id, self.bot_id)
        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            log.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    @override
    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        """Add token to the twitchio client and into the bot's database.

        Source
        ------
        Quickstart guide by TwitchIO:
        * https://twitchio.dev/en/latest/getting-started/quickstart.html
        """
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
        if "ext.public.dota" in self.extensions:  # TODO: CHANGE !!!!!!!!!!!!!!!
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

    @override
    def get_context(self, payload: twitchio.ChatMessage, *, cls: Any = IreContext) -> IreContext:
        # they have channel points commands but I'm not using it (yet)
        return super().get_context(payload, cls=cls)

    # @override  # interesting that it's not an override
    async def event_ready(self) -> None:
        """Event that is dispatched when the `Client` is ready and has completed login."""
        log.info("%s is ready as bot_id = %s", self.__class__.__name__, self.bot_id)

        if not hasattr(self, "launch_time"):
            # who knows maybe it triggers many times like `discord.py`
            self.launch_time = datetime.datetime.now(datetime.UTC)
        if hasattr(self, "dota"):
            await self.dota.wait_until_ready()

    @override
    async def event_command_error(self, payload: commands.CommandErrorPayload) -> None:
        """Called when error happens during command invoking."""
        command = payload.context.command
        ctx: IreContext = payload.context  # type: ignore[reportAssignmentType] Channel Point commands lead to these things.
        error = payload.exception

        if command and command.has_error and ctx.error_dispatched:
            return

        # we aren't interested in the chain traceback:
        error = error.original if isinstance(error, commands.CommandInvokeError) and error.original else error

        match error:
            case errors.IreBotError():
                # errors defined by me - just send the string
                await ctx.send(str(error))
            case commands.CommandNotFound():
                #  otherwise we just spam console with commands from other bots and from my event thing
                log.info("CommandNotFound: %s", error)
            case commands.GuardFailure():
                guard_mapping = {
                    "is_moderator.<locals>.predicate": (
                        f"Only moderators are allowed to use this command {const.FFZ.peepoPolice}"
                    ),
                    "is_vps.<locals>.predicate": (
                        f"Only production bot allows usage of this command {const.FFZ.peepoPolice}"
                    ),
                    "is_owner.<locals>.predicate": (
                        f"Only Irene Adler is allowed to use this command {const.FFZ.peepoPolice}"
                    ),
                    "is_broadcaster.<locals>.predicate": (
                        f"Only broadcaster is allowed to use this command {const.FFZ.peepoPolice}"
                    ),
                    "is_online.<locals>.predicate": (
                        f"This commands is only allowed when stream is online {const.FFZ.peepoPolice}"
                    ),
                }
                await ctx.send(guard_mapping.get(error.guard.__qualname__, str(error)))
            case twitchio.HTTPException():
                await ctx.send(
                    f"{error.__class__.__name__} - "
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
                await ctx.send(
                    f"Sorry {const.Global.FeelsDankMan} "
                    f"Something went wrong {const.Global.FeelsDankMan} "
                    "but I've notified Irene about the error."
                )
                # await ctx.send(f"{error.__class__.__name__}: {replace_secrets(str(error))}")

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

    # SHORTCUTS

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
        return "<@&1337106675433340990>" if self.test else "<@&1116171071528374394>"

    # UTILITIES

    def is_online(self, user_id: str) -> bool:
        """#TODO."""
        return s.online if (s := self.streamers.get(user_id, None)) else False
