"""TRANSLATION COMMAND.

Sources
-------
* My own discord bot (but the code there is also taken from other places)
    https://github.com/Aluerie/AluBot/blob/main/ext/educational/language/translation.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TypedDict

from twitchio.ext import commands

from bot import IreComponent
from utils import const, errors

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from bot import IreBot


__all__ = ("Translations",)


class TranslatedSentence(TypedDict):
    """TranslatedSentence."""

    trans: str
    orig: str


class TranslateResult(NamedTuple):
    """TranslatedResult."""

    original: str
    translated: str
    source_lang: str
    target_lang: str


async def translate(
    text: str,
    *,
    source_lang: str = "auto",
    target_lang: str = "en",
    session: ClientSession,
) -> TranslateResult:
    """Google Translate."""
    query = {
        "dj": "1",
        "dt": ["sp", "t", "ld", "bd"],
        "client": "dict-chrome-ex",  # Needs to be dict-chrome-ex or else you'll get a 403 error.
        "sl": source_lang,
        "tl": target_lang,
        "q": text,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/104.0.0.0 Safari/537.36"
        ),
    }

    async with session.get("https://clients5.google.com/translate_a/single", params=query, headers=headers) as resp:
        if resp.status != 200:
            raise errors.TranslateError(resp.status, text=await resp.text())

        data = await resp.json()
        src = data.get("src", "Unknown")
        sentences: list[TranslatedSentence] = data.get("sentences", [])
        if not sentences:
            msg = "Google translate returned no information"
            raise RuntimeError(msg)

        return TranslateResult(
            original="".join(sentence.get("orig", "") for sentence in sentences),
            translated="".join(sentence.get("trans", "") for sentence in sentences),
            source_lang=src.upper(),
            target_lang=target_lang.upper(),
        )


class Translations(IreComponent):
    """Translation command component."""

    @commands.command()
    async def translate(self, ctx: commands.Context, *, text: str) -> None:
        """Translate to English.

        Uses Google Translate. Autodetects source language.
        """
        result = await translate(text, session=self.bot.session)
        answer = f"{const.STV.ApuBritish} [{result.source_lang} to {result.target_lang}] {result.translated}"
        await ctx.send(answer)


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Translations(bot))
