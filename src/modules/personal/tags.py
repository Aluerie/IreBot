from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import asyncpg
from twitchio.ext import commands

from core import IrePersonalComponent
from utils import const, errors

if TYPE_CHECKING:
    from core import IreBot, IreContext

    class TagQueryRow(TypedDict):
        tag_name: str
        tag_content: str


__all__ = ("Tags",)


class Tags(IrePersonalComponent):
    """Commands to fetch something by a tag name."""

    def tag_does_not_exist_message(self, tag_name: str) -> str:
        return f"There is no tag with name '{tag_name}' {const.STV.uuhAcktshucally}"

    @commands.is_moderator()
    @commands.group(invoke_fallback=True, aliases=["tags", "t"])
    async def tag_group(self, ctx: IreContext, tag_name: str) -> None:
        """Group command for `!tag`.

        Without a subcommand this fetches a tag.
        """
        query = """
            SELECT tag_content FROM ttv_tags
            WHERE tag_name = $1;
        """
        tag_content: str | None = await self.bot.pool.fetchval(query, tag_name)
        await ctx.send(self.tag_does_not_exist_message(tag_name) if tag_content is None else tag_content)

    @tag_group.command(aliases=["a", "create"])
    async def tag_add(self, ctx: IreContext, tag_name: str, *, tag_content: str) -> None:
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

    @tag_group.command(aliases=["del", "remove", "d"])
    async def tag_delete(self, ctx: IreContext, tag_name: str) -> None:
        """Delete tag by name."""
        query = """
            DELETE FROM ttv_tags
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name)
        await ctx.send(
            self.tag_does_not_exist_message(tag_name)
            if val is None
            else f"Deleted tag '{tag_name}' {const.STV.uuhAcktshucally}"
        )

    @tag_group.command(aliases=["e"])
    async def tag_edit(self, ctx: IreContext, tag_name: str, *, tag_content: str) -> None:
        """Edit tag."""
        query = """
            UPDATE ttv_tags
            SET tag_content=$2
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name, tag_content)
        await ctx.send(
            self.tag_does_not_exist_message(tag_name)
            if val is None
            else f"Edited tag '{tag_name}' {const.STV.uuhAcktshucally}"
        )

    @tag_group.command(aliases=["r"])
    async def tag_rename(self, ctx: IreContext, tag_name: str, new_tag_name: str) -> None:
        """Rename tag."""
        query = """
            UPDATE ttv_tags
            SET tag_name=$2
            WHERE tag_name=$1
            RETURNING tag_name;
        """
        val: str | None = await self.bot.pool.fetchval(query, tag_name, new_tag_name)
        await ctx.send(
            self.tag_does_not_exist_message(tag_name)
            if val is None
            else f"Renamed tag '{tag_name}' into '{new_tag_name}' {const.STV.uuhAcktshucally}"
        )

    @tag_group.command(aliases=["n"])
    async def tag_names(self, ctx: IreContext) -> None:
        """Tag names list."""
        query = """
            SELECT tag_name FROM ttv_tags;
        """
        tag_names: list[str] = [r for (r,) in await self.bot.pool.fetch(query)]
        await ctx.send(
            f"{const.STV.uuhAcktshucally} {', '.join(tag_names)}"
            if tag_names
            else f"No tags were created yet {const.STV.uuhAcktshucally}"
        )

    @tag_group.command(name="list", aliases=["l", "all"])
    async def tag_list(self, ctx: IreContext) -> None:
        """Tag list."""
        query = """
            SELECT tag_name, tag_content FROM ttv_tags;
        """
        tag_rows: list[TagQueryRow] = [r for (r,) in await self.bot.pool.fetch(query)]
        if tag_rows:
            for tag_row in tag_rows:
                await ctx.send(f"{const.STV.uuhAcktshucally} {tag_row['tag_name']}: {tag_row['tag_content']}")
        else:
            await ctx.send(f"No tags were created yet {const.STV.uuhAcktshucally}")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Tags(bot))
