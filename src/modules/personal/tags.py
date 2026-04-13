from __future__ import annotations

from typing import TYPE_CHECKING

import asyncpg
from twitchio.ext import commands

from core import IrePersonalComponent
from utils import const, errors

if TYPE_CHECKING:
    from core import IreBot, IreContext


__all__ = ("Tags",)


class Tags(IrePersonalComponent):
    """Commands to fetch something by a tag name."""

    @commands.is_moderator()
    @commands.group(invoke_fallback=True, aliases=["tags"])
    async def tag(self, ctx: IreContext, *, tag_name: str) -> None:
        """Group command for `!tag`.

        Without a subcommand this fetches a tag.
        """
        query = """
            SELECT tag_content FROM ttv_tags
            WHERE tag_name = $1;
        """
        tag_content: str | None = await self.bot.pool.fetchval(query, tag_name)
        if tag_content:
            await ctx.send(tag_content)
        else:
            await ctx.send(f"There is no tag under '{tag_name}' name {const.STV.uuhAcktshucally}")

    @tag.command()
    async def add(self, ctx: IreContext, tag_name: str, *, tag_content: str) -> None:
        """Add tag."""
        if tag_name in ("delete", "remove", "del", "add", "list", "edit"):
            msg = f"This tag_name is reserved {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg) from None
        try:
            query = """
                INSERT INTO ttv_tags
                (tag_name, tag_content)
                VALUES ($1, $2);
            """
            await self.bot.pool.execute(query, tag_name, tag_content)
            await ctx.send(f"Created tag {tag_name} {const.STV.uuhAcktshucally}")
        except asyncpg.UniqueViolationError:
            msg = f"There already exists a tag with such name {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg) from None

    @tag.command(aliases=["del", "remove"])
    async def delete(self, ctx: IreContext, tag_name: str) -> None:
        """Delete tag by name."""
        query = """
            DELETE FROM ttv_tags
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name)
        if val is None:
            msg = f"There is no tag with such name {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg)

        await ctx.send(f"Deleted tag '{tag_name}' {const.STV.uuhAcktshucally}")

    @tag.command()
    async def edit(self, ctx: IreContext, command_name: str, *, text: str) -> None:
        """Edit tag."""
        query = """
            UPDATE ttv_tags
            SET tag_content=$3
            WHERE tag_name
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, command_name, text)
        if val is None:
            msg = f"There is no tag with such name {const.STV.uuhAcktshucally}"
            raise errors.RespondWithError(msg)

        await ctx.send(f"Edited tag '{command_name}' {const.STV.uuhAcktshucally}")

    @tag.command()
    async def list(self, ctx: IreContext) -> None:
        """Tag list."""
        query = """
            SELECT tag_name FROM ttv_tags;
        """
        tag_names: list[str] = [r for (r,) in await self.bot.pool.fetch(query)]
        if tag_names:
            await ctx.send(", ".join(tag_names))
        else:
            await ctx.send(f"No tags were created yet {const.STV.uuhAcktshucally}")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Tags(bot))
