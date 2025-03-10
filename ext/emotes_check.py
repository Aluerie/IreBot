from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, override

from discord import Embed

from bot import IreComponent, lueloop
from utils import const

if TYPE_CHECKING:
    from enum import StrEnum

    from bot import IreBot


class EmoteChecker(IreComponent):
    """Check if emotes from 3rd party services like 7TV, FFZ, BTTV are valid.

    Usable in case I remove an emote that is used in bot's responses.
    Bot will notify me that emote was used so I can make adjustments.
    """

    def __init__(self, bot: IreBot) -> None:
        super().__init__(bot)

    @override
    async def component_load(self) -> None:
        self.check_emotes.start()

    @override
    async def component_teardown(self) -> None:
        self.check_emotes.cancel()

    async def send_error_embed(self, emote: str, service: str, colour: int) -> None:
        """Helper function to send a ping to Aluerie that something is wrong with emote services."""
        content = self.bot.error_ping
        embed = Embed(
            title=f"Problem with {service} emotes",
            description=f"Looks like emote `{emote}` is no longer present in the channel.",
            colour=colour,
        ).set_footer(text="but it was previously used for @AlueBot emotes")
        await self.bot.error_webhook.send(content=content, embed=embed)

    async def cross_check_emotes(self, api_emotes: list[str], bot_emotes: type[StrEnum], colour: int) -> None:
        """Cross check between emote list in `utils.const` and list from 3rd party emote service API."""
        for emote in bot_emotes:
            if emote not in api_emotes:
                await self.send_error_embed(emote, bot_emotes.__name__, colour)

    @lueloop(time=[datetime.time(hour=5, minute=59)])
    async def check_emotes(self) -> None:
        """The task to check emotes."""
        if datetime.datetime.now(datetime.UTC).weekday() != 5:
            # simple way to make a task run once/week
            return

        # SEVEN TV
        async with self.bot.session.get(f"https://7tv.io/v3/users/twitch/{const.UserID.Irene}") as resp:
            stv_json = await resp.json()
            stv_emote_list = [emote["name"] for emote in stv_json["emote_set"]["emotes"]]
            await self.cross_check_emotes(stv_emote_list, const.STV, 0x3493EE)

        # FFZ
        async with self.bot.session.get(f"https://api.frankerfacez.com/v1/room/id/{const.UserID.Irene}") as resp:
            ffz_json = await resp.json()  # if we ever need this "654554" then it exists as `ffz_json["room"]["set"]`
            ffz_emote_list = [emote["name"] for emote in ffz_json["sets"]["654554"]["emoticons"]]
            await self.cross_check_emotes(ffz_emote_list, const.FFZ, 0x271F3E)

        # BTTV
        async with self.bot.session.get(
            f"https://api.betterttv.net/3/cached/users/twitch/{const.UserID.Irene}",
        ) as resp:
            bttv_json = await resp.json()
            bttv_emote_list = [emote["code"] for emote in bttv_json["channelEmotes"] + bttv_json["sharedEmotes"]]
            await self.cross_check_emotes(bttv_emote_list, const.BTTV, 0xD50014)


async def setup(bot: IreBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(EmoteChecker(bot))
