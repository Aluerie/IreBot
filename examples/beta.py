#  ruff: noqa: D101, D102, D103

from __future__ import annotations

from beta_base import *


class BetaTest(BetaCog):
    @ireloop(count=1)
    async def beta_test(self) -> None:
        pass

    @commands.command()
    async def beta(self, ctx: IreContext) -> None:
        pass


async def setup(bot: IreBot) -> None:
    await bot.add_component(BetaTest(bot))
