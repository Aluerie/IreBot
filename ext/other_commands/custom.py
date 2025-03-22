from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, override

import asyncpg
import twitchio  # noqa: TC002
from twitchio.ext import commands

from bot import IreComponent, ireloop
from utils import const, errors

if TYPE_CHECKING:
    from bot import IreBot, IreContext

    class TwitchCommands(TypedDict):
        """`chat_commands` Table Structure."""

        streamer_id: str
        command_name: str
        content: str


class CustomCommands(IreComponent):
    """Custom commands.

    Commands that are managed on the fly.
    The information is contained within the database and cache.
    """

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.command_cache: dict[str, dict[str, str]] = {}

    @override
    async def component_load(self) -> None:
        self.populate_cache.start()
        await super().component_load()

    @override
    async def component_teardown(self) -> None:
        self.populate_cache.cancel()
        await super().component_teardown()

    @ireloop(count=1)
    async def populate_cache(self) -> None:
        """Populate custom commands cache."""
        query = """
            SELECT streamer_id, command_name, content
            FROM ttv_chat_commands
        """
        rows: list[TwitchCommands] = await self.bot.pool.fetch(query)
        for row in rows:
            self.command_cache.setdefault(row["streamer_id"], {})[row["command_name"]] = row["content"]

    @commands.Component.listener(name="message")
    async def event_message(self, message: twitchio.ChatMessage) -> None:
        """Listen to prefix custom commands.

        This is a bit different from twitchio commands. This one is just for this cog.
        """
        if not message.text.startswith(self.bot.prefixes) or message.chatter.id == const.UserID.Bot:
            return

        channel_commands = self.command_cache.get(message.broadcaster.id, {})
        if not channel_commands:
            # no commands registered for this channel
            return

        # text without !, ?, $
        no_prefix_text = message.text[1:]

        for command_name, command_response in channel_commands.items():
            if no_prefix_text.startswith(command_name):
                await message.broadcaster.send_message(
                    sender=const.UserID.Bot,
                    message=command_response,
                )

    @commands.is_moderator()
    @commands.group(invoke_fallback=True)
    async def cmd(self, ctx: IreContext) -> None:
        """Group command to define cmd."""
        await ctx.send('You need to use this with subcommands, i.e. "cmd add/delete/edit/list"')

    @commands.is_moderator()
    @cmd.command()
    async def add(self, ctx: IreContext, cmd_name: str, *, text: str) -> None:
        """Add custom command."""
        query = """
            INSERT INTO ttv_chat_commands
            (streamer_id, command_name, content)
            VALUES ($1, $2, $3)
        """
        try:
            await self.bot.pool.execute(query, ctx.broadcaster.id, cmd_name, text)
        except asyncpg.UniqueViolationError:
            msg = "There already exists a command with such name."
            raise errors.BadArgumentError(msg) from None

        self.command_cache.setdefault(ctx.broadcaster.id, {})[cmd_name] = text
        await ctx.send(f"Added the command {cmd_name}.")

    @commands.is_moderator()
    @cmd.command(name="del")
    async def delete(self, ctx: IreContext, command_name: str) -> None:
        """Delete custom command by name."""
        query = """
            DELETE FROM ttv_chat_commands
            WHERE streamer_id=$1 AND command_name=$2
            RETURNING command_name
        """
        val = await self.bot.pool.fetchval(query, ctx.broadcaster.id, command_name)
        if val is None:
            msg = "There is no command with such name."
            raise errors.BadArgumentError(msg)

        self.command_cache[ctx.broadcaster.id].pop(command_name)
        await ctx.send(f"Deleted the command {command_name}")

    @commands.is_moderator()
    @cmd.command()
    async def edit(self, ctx: IreContext, command_name: str, *, text: str) -> None:
        """Edit custom command."""
        query = """
            UPDATE ttv_chat_commands
            SET content=$3
            WHERE streamer_id=$1 AND command_name=$2
            RETURNING command_name
        """
        val = await self.bot.pool.fetchval(query, ctx.broadcaster.id, command_name, text)
        if val is None:
            msg = "There is no command with such name."
            raise errors.BadArgumentError(msg)

        self.command_cache[ctx.broadcaster.id][command_name] = text
        await ctx.send(f"Edited the command {command_name}.")

    # TODO: THIS IS KINDA BAD, we need more centralized help, maybe git page
    @cmd.command(name="list")
    async def cmd_list(self, ctx: IreContext) -> None:
        """Get commands list."""
        cache_list = [f"!{name}" for v in self.command_cache.values() for name in v]
        # bot_cmds = [
        # f"!{v.full_name}" for v in self.bot.commands.values() if not v._checks and not isinstance(v, commands.Group)
        # ]
        await ctx.send(", ".join(cache_list))


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(CustomCommands(bot))
