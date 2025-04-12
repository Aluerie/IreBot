from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreBot, IreContext


class MiscellaneousCommands(IreComponent):
    """Miscellaneous commands.

    Commands that are likely to be removed in future.
    """

    @commands.command()
    async def notes(self, ctx: IreContext, *, game: Literal["sekiro", "er"]) -> None:
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
    async def run(self, ctx: IreContext) -> None:
        """Explanation of my first Sekiro hitless run."""
        msg = (
            "Bosses I like %."
            "On paper, it's Immortal Severance with 10 extra bosses including loading a save file "
            "for Inner Father, Fire Isshin and Emma reflections. "
            "DB NKC LL NC GL. Sword+Shuriken Focused."
            "The only boss that I blast with MDs is Ape (I hate that boss). "
            "My notes (kinda chaotic): !notes sekiro."
        )
        await ctx.send(msg)

    @commands.group(invoke_fallback=True)
    async def gunfort(self, ctx: IreContext) -> None:
        """Commands to count my successful and failed Yolo Gunfort attempts."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"{const.STV.science} Yolo Gunfort {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def no(self, ctx: IreContext) -> None:
        """Count a failed Yolo Gunfort attempt in."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Failed yolo gunfort? {const.STV.classic} {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def yes(self, ctx: IreContext) -> None:
        """Count a successful Yolo Gunfort attempt in."""
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Yolo Gunfort is easy {const.STV.EZdodge} {stats}")

    @commands.command(name="is")
    async def immortal_severance(self, ctx: IreContext) -> None:
        """Print a proper speed-run order for IS dialog."""
        msg = (
            "👶 Kuro: "
            "1. Quit "
            '2. Skip → Ask "About the flower" → Skip until item → Quit '
            "3. Skip until item → Quit "
            "4. Quit "
            "5. Skip until item → Quit "
            "💃 Emma: "
            "Quit 3 dialogs "
            "👶 Kuro again: "
            "1. Quit "
            "2. Burn incense → Skip till cutscene → Quit"
        )
        await ctx.send(msg)

    @commands.command(name="iss")
    async def immortal_severance_short(self, ctx: IreContext) -> None:
        """Print a proper speed-run order for IS dialog."""
        msg = "Kuro: 1️⃣🟥2️⃣🟩🌸🟩3️⃣🟩4️⃣🟥5️⃣🟩 → Emma:🟥3x → Kuro:1️⃣🟥2️⃣🔥🟩 "
        await ctx.send(msg)

    @commands.command()
    async def headless(self, ctx: IreContext) -> None:
        """Headless."""
        msg = (
            "One day we will start practicing mini bosses 4Head "
            "clueless Surely practice headless too 4Head "
            "Maybe let's just remove him from the run 4Head "
            "fok this boss 4Head"
        )
        await ctx.send(msg)

    @commands.command()
    async def centipede(self, ctx: IreContext) -> None:
        """Centipede."""
        msg = (
            "I don't understand this boss BabyRage "
            "How to stop ADHD'ing on Quickie BabyRage "
            "Why do I get a block on 9th hit in combo all the time BabyRage "
            "I don't understand BabyRage "
            "Should we just MD this trash BabyRage"
        )
        await ctx.send(msg)

    @commands.command()
    async def vilehand(self, ctx: IreContext) -> None:
        """Vilehand."""
        msg = (
            "omg how to deflect Vilehand's Sabimaru omg "
            "fml chat it's so fast omg "
            "HOOOOOOOOOOOW omg "
            "It's literally light fast omg "
        )
        await ctx.send(msg)


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(MiscellaneousCommands(bot))
