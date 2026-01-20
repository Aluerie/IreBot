from __future__ import annotations

import contextlib
import datetime
from typing import TYPE_CHECKING, Any, TypedDict

import twitchio
from twitchio.ext import commands

from core import IrePersonalComponent, ireloop
from utils import const, fmt, guards

if TYPE_CHECKING:
    from core import IreBot, IreContext

    class Tracked(TypedDict):
        game: str
        title: str
        game_dt: datetime.datetime
        title_dt: datetime.datetime


__all__ = ("EditInformation",)


class EditInformation(IrePersonalComponent):
    @commands.is_moderator()
    @title_group.command(name="restore", aliases=["prev", "previous"])
    async def title_restore(self, ctx: IreContext, offset: int = 1) -> None:
        """Restore title for the stream from the database.

        Database keeps some recent titles (cleans up up to last 2 days on stream-offline event).
        Useful when we switch the title for some activity, i.e. "watching anime" and then
        go back to Elden Ring so we just !title restore and it sets to my previous relevant Elden Ring title.

        Parameters
        ----------
        offset
            The number representing how old the title should be as in ordinal, i.e. !title restore 5 means
            restore 5th newest title from the database. "Previous" = 1 for this logic (and default).
        """
        query = """
            SELECT title FROM ttv_stream_titles
            ORDER BY edit_time DESC
            LIMIT 1
            OFFSET $1;
        """
        title: str | None = await self.bot.pool.fetchval(query, offset)
        if title is None:
            await ctx.send("No change: the database doesn't keep such title.")
        else:
            await self.update_title(ctx.broadcaster, title=title)
            await ctx.send(f"Set the title to {fmt.ordinal(offset)} in history: {title}")

    @commands.is_moderator()
    @title_group.command(name="history")
    async def title_history(self, ctx: IreContext, number: int = 3) -> None:
        """Shows some title history so you can remember/edit what we had before.

        Parameters
        ----------
        number
            amount of entries (newest titles) to pull out from the database.

        """
        query = """
            SELECT title FROM ttv_stream_titles
            ORDER BY edit_time DESC
            LIMIT $1
            OFFSET 1
        """
        history_titles: list[str] = [r for (r,) in await self.bot.pool.fetch(query, number)]
        if history_titles:
            for count, saved_title in enumerate(history_titles, start=1):
                await ctx.send(f"{count}. {saved_title}")
        else:
            await ctx.send("Database doesn't have any titles saved.")

    @commands.Component.listener(name="stream_offline")
    async def clear_the_database(self, offline: twitchio.StreamOffline) -> None:
        """Clear the database from old enough titles.

        I guess stream end is a good event for it - it's rare enough and we don't need old titles after stream is over.
        """
        if not self.is_owner(offline.broadcaster.id):
            return

        cutoff_dt = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)
        query = "DELETE FROM ttv_stream_titles WHERE edit_time < $1"
        await self.bot.pool.execute(query, cutoff_dt)

    @commands.Component.listener(name="channel_update")
    async def channel_update(self, update: twitchio.ChannelUpdate) -> None:
        # ...
        if self.title != update.title:
            # we need to record the title into the database
            query = """
                INSERT INTO ttv_stream_titles
                (title, edit_time)
                VALUES ($1, $2)
                ON CONFLICT (title) DO
                    UPDATE SET edit_time = $2;
            """
            await self.bot.pool.execute(query, update.title, now)



async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(EditInformation(bot))
