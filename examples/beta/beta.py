#  ruff: noqa: D101, D102, D103, T201

from __future__ import annotations

from examples.beta.base import *


class BetaTest(BetaCog):
    @irenes_loop(count=1)
    async def beta_test(self) -> None:
        pass

    @commands.command()
    async def beta(self, ctx: commands.Context) -> None:
        pass


async def setup(bot: IrenesBot) -> None:
    if __name__ in bot.extensions:
        await bot.add_component(BetaTest(bot))
