from __future__ import annotations

from typing import TYPE_CHECKING, override

import asyncpg
from twitchio.ext import commands

from core import IrePersonalComponent
from utils import const, errors

if TYPE_CHECKING:
    from core import IreBot, IreContext


__all__ = ("Tags",)


class Tags(IrePersonalComponent):
    """Commands to fetch something by a tag name.

    Dev notes
    ---------
    * In this component I use `assert val is not None, tag_name` purely for type-checking memes
    over some `tag_exists_check` function.
    """

    @override
    async def component_command_error(self, payload: commands.CommandErrorPayload) -> bool | None:
        """Event called when an error occurs in a command in this Component."""
        if isinstance(exc := payload.exception, AssertionError):
            msg = str(exc)
            raise errors.RespondWithError(msg)
        return None

    def tag_does_not_exist_message(self, tag_name: str) -> str:
        return f"There is no tag with name '{tag_name}' {const.STV.uuhAcktshucally}"

    @commands.is_moderator()
    @commands.group(invoke_fallback=True, aliases=["tags", "t"])
    async def tag(self, ctx: IreContext, tag_name: str) -> None:
        """Group command for `!tag`.

        Without a subcommand this fetches a tag.
        """
        query = """
            SELECT tag_content FROM ttv_tags
            WHERE tag_name = $1;
        """
        tag_content: str | None = await self.bot.pool.fetchval(query, tag_name)
        assert tag_content is not None, self.tag_does_not_exist_message(tag_name)
        await ctx.send(tag_content)

    @tag.command(aliases="a")
    async def add(self, ctx: IreContext, tag_name: str, *, tag_content: str) -> None:
        """Add tag."""
        if tag_name in ("delete", "remove", "del", "add", "list", "edit", "a", "d", "r", "e", "l"):
            msg = f"This tag_name is reserved {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg) from None
        try:
            query = """
                INSERT INTO ttv_tags
                (tag_name, tag_content)
                VALUES ($1, $2);
            """
            await self.bot.pool.execute(query, tag_name, tag_content)
            await ctx.send(f"Created tag '{tag_name}' {const.STV.uuhAcktshucally}")
        except asyncpg.UniqueViolationError:
            msg = f"There already exists a tag with name '{tag_name}' {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg) from None

    @tag.command(aliases=["del", "remove", "d"])
    async def delete(self, ctx: IreContext, tag_name: str) -> None:
        """Delete tag by name."""
        query = """
            DELETE FROM ttv_tags
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name)
        assert val is not None, self.tag_does_not_exist_message(tag_name)
        await ctx.send(f"Deleted tag '{tag_name}' {const.STV.uuhAcktshucally}")

    @tag.command(aliases=["e"])
    async def edit(self, ctx: IreContext, tag_name: str, *, tag_content: str) -> None:
        """Edit tag."""
        query = """
            UPDATE ttv_tags
            SET tag_content=$2
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name, tag_content)
        assert val is not None, self.tag_does_not_exist_message(tag_name)
        await ctx.send(f"Edited tag '{tag_name}' {const.STV.uuhAcktshucally}")

    @tag.command(aliases=["r"])
    async def rename(self, ctx: IreContext, tag_name: str, new_tag_name: str) -> None:
        """Rename tag."""
        query = """
            UPDATE ttv_tags
            SET tag_name=$2
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name, new_tag_name)
        assert val is not None, self.tag_does_not_exist_message(tag_name)
        await ctx.send(f"Renamed tag '{tag_name}' into 'new_tag_name' {const.STV.uuhAcktshucally}")

    @tag.command(aliases=["l"])
    async def list(self, ctx: IreContext) -> None:
        """Tag list."""
        query = """
            SELECT tag_name FROM ttv_tags;
        """
        tag_names: list[str] = [r for (r,) in await self.bot.pool.fetch(query)]
        if tag_names:
            await ctx.send(f"{const.STV.uuhAcktshucally} {', '.join(tag_names)}")
        else:
            await ctx.send(f"No tags were created yet {const.STV.uuhAcktshucally}")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Tags(bot))
