from __future__ import annotations

import datetime
import random
import re
from typing import TYPE_CHECKING, Any, TypedDict

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    import twitchio

    from bot import IreBot

    class KeywordDict(TypedDict):
        aliases: list[str]
        response: str
        dt: datetime.datetime


__all__ = ("Keywords",)


class Keywords(IreComponent):
    """React to specific key word / key phrases with bot's own messages.

    Mostly used to make a small feeling of a crowd - something like many users are Pog-ing.
    """

    def __init__(self, bot: IreBot, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.keywords: list[KeywordDict] = [
            {
                "aliases": aliases,
                "response": response,
                "dt": datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
            }
            for aliases, response in [
                (["Pog", "PogU"], "Pog"),
                (["gg"], "gg"),
                (["GG"], "GG"),
                (["bueno"], "bueno"),
                (
                    ["Pepoga"],
                    "Pepoga 📣 AAAIIIIIIIIIREEEEEEEEEEEEEEEENEE !",
                ),  # # cSpell: ignore AAAIIIIIIIIIREEEEEEEEEEEEEEEENEE
            ]
        ]

    @commands.Component.listener(name="message")
    async def keywords_response(self, message: twitchio.ChatMessage) -> None:
        """Sends a flavour message if a keyword/key phrase was spotted in the chat."""
        if message.chatter.name in const.Bots or not message.text or random.randint(1, 100) > 5:
            return

        now = datetime.datetime.now(datetime.UTC)
        for keyword in self.keywords:
            if (now - keyword["dt"]).seconds < 777:
                # the keyword was recently triggered
                continue

            for word in keyword["aliases"]:
                # TODO: Check if | thing works instead of looping
                if re.search(r"\b" + re.escape(word) + r"\b", message.text):
                    await message.broadcaster.send_message(sender=self.bot.bot_id, message=keyword["response"])
                    keyword["dt"] = now


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Keywords(bot))
