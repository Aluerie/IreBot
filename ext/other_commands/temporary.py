from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreBot


class MiscellaneousCommands(IreComponent):
    """Miscellaneous commands.

    Commands that are likely to be removed in future.
    """

    @commands.command()
    async def notes(self, ctx: commands.Context, *, game: Literal["sekiro", "er"]) -> None:
        """Get a link to one of my notes."""
        mapping = {
            "sekiro": "docs.google.com/document/d/1rjp7lhvP0vwwlO7bC7TyFAjKcGDovFuo2EYUaX66QiA",
            "er": "docs.google.com/document/d/19vTJVS7k1zdmShOAcO41KBWepfybMsTprQ208O7HpLU",
        }
        await ctx.send(mapping[game.lower()])

    @notes.error
    async def notes_error(self, payload: commands.CommandErrorPayload) -> None:
        """XD."""
        if isinstance(exc := payload.exception, commands.BadArgument):
            await payload.context.send(f'Bad argument: "{exc.value}". Supported notes: "sekiro", "er".')
        else:
            raise payload.exception

    @commands.command()
    async def run(self, ctx: commands.Context) -> None:
        """Explanation of my first Sekiro hitless run."""
        msg = (
            "Bosses I like %, Sword+Shuriken Focused. "
            "On paper, it's Immortal Severance with 7 extra bosses including loading a save file "
            "with Inner Father, Fire Isshin and Emma reflections. "
            "DB NKC LL NC GL. "
            "The only boss that I blast with MDs is Ape. "
            "My notes: !notes sekiro."
        )
        await ctx.send(msg)

    @commands.group(invoke_fallback=True)
    async def gunfort(self, ctx: commands.Context) -> None:
        """Commands to count my successful and failed Yolo Gunfort attempts."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"{const.STV.science} Yolo Gunfort {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def no(self, ctx: commands.Context) -> None:
        """Count a failed Yolo Gunfort attempt in."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Failed yolo gunfort? {const.STV.classic} {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def yes(self, ctx: commands.Context) -> None:
        """Count a successful Yolo Gunfort attempt in."""
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Yolo Gunfort is easy {const.STV.EZdodge} {stats}")


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(MiscellaneousCommands(bot))
