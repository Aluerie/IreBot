from __future__ import annotations

from typing import TYPE_CHECKING, override

from bot import IrePublicComponent, ireloop
from config import config

if TYPE_CHECKING:
    from bot import IreBot


class GameFlowNew(IrePublicComponent):
    """Component responsible for Dota 2 related commands and stats tracker.

    This functionality is pretty much analogical to common dotabod, 9kmmrbot features.
    """

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)

    @override
    async def component_load(self) -> None:
        self.rich_presence_gameflow_loop.start()

    @override
    async def component_teardown(self) -> None:
        self.rich_presence_gameflow_loop.cancel()

    @ireloop(seconds=20)
    async def rich_presence_gameflow_loop(self) -> None:
        todo_steam_id64 = config["STEAM"]["IRENE_ID64"]
        await self.update_rich_presence_states(1)

    async def update_rich_presence_states(self, steam_id64: int):
        for friend in await self.bot.dota.user.friends():
            print(friend.rich_presence)

        user = self.bot.dota.get_user(steam_id64)


