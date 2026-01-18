from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from twitchio.ext import commands

from bot import IrePersonalComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreBot, IreContext

    class RunDict(TypedDict):
        keywords: list[str]
        game: str
        desc: str


__all__ = ("TemporaryCommands",)


class TemporaryCommands(IrePersonalComponent):
    """Miscellaneous commands.

    Commands that are likely to be removed in future or edited a lot.
    """

    @commands.command(name="sekirodoc")
    async def sekiro_doc(self, ctx: IreContext) -> None:
        """Get a link to one of my sekiro notes."""
        await ctx.send("docs.google.com/document/d/1rjp7lhvP0vwwlO7bC7TyFAjKcGDovFuo2EYUaX66QiA")

    @commands.command()
    async def rules(self, ctx: IreContext) -> None:
        """ER Run rules."""
        msg = (
            'Hybrid challenge "the best of both Speed/Hitless"'
            f" 1️⃣Minimize time in running sections: only speed-leaderboard picks-ups are allowed {const.STV.Speedge}"
            f" 2️⃣Only hits vs bosses count {const.STV.actually}"
            f" 3️⃣We use a custom-made but sensible starting class with fashion/weapon I choose {const.STV.forsenCD}"
            f" 4️⃣No direct damage buffs allowed {const.STV.POLICE}"
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
        await ctx.send(f"Failed yolo gunfort? {const.STV.classic} {stats} {const.STV.buenoFail}")

    @commands.is_owner()
    @gunfort.command()
    async def yes(self, ctx: IreContext) -> None:
        """Count a successful Yolo Gunfort attempt in."""
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Yolo Gunfort is easy {const.STV.EZdodge} {stats} {const.STV.buenoSuccess}")

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
        msg = "omg how to deflect Vilehand's Sabimaru omg fml chat omg HOOOOOOOOOOOW omg "
        await ctx.send(msg)

    @commands.is_owner()
    @commands.command()
    async def brb(self, ctx: IreContext) -> None:
        """BRB."""
        gone_text = "—————————————————————— imGlitch streamer is gone, time to plink ——————————————————————"
        await ctx.send(gone_text)

    @commands.is_owner()
    @commands.command()
    async def back(self, ctx: IreContext) -> None:
        """BACK."""
        back_text = "—————————————————————— imGlitch streamer is back, act normal uuh ——————————————————————"
        await ctx.send(back_text)

    @commands.command()
    async def abc(self, ctx: IreContext) -> None:
        """Send all possible *uh emotes to the chat."""
        # fmt: off
        alphabet = [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"
        ]
        # fmt: on
        text = " ".join(f"{letter}uh" for letter in alphabet)
        await ctx.send(text)


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(TemporaryCommands(bot))
