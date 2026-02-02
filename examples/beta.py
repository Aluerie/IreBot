#  ruff: noqa: D101, D102, D103

from __future__ import annotations

from beta_base import *


class BetaTest(BetaCog):
    @ireloop(count=1)
    async def beta_test(self) -> None:
        pass

    @commands.command(name="test", aliases=["beta"])
    async def test(self, ctx: IreContext) -> None:
        await ctx.send("test")


async def setup(bot: IreBot) -> None:
    await bot.add_component(BetaTest(bot))
