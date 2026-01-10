from __future__ import annotations

import asyncio
import datetime
import importlib.metadata
import logging
import random
import sys
import unicodedata
from typing import TYPE_CHECKING, NamedTuple, TypedDict

import twitchio  # noqa: TC002
from twitchio.ext import commands

from bot import IrePersonalComponent
from config import config
from utils import const, errors, fmt, guards

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from bot import IreBot, IreContext


log = logging.getLogger(__name__)


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
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
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


class StableCommands(IrePersonalComponent):
    """Stable commands.

    Stable in a sense that unlike commands in `temporary.py` or `custom.py` with their dynamic commands
    These are supposed to stay with us for a long time.
    But they couldn't be categorized into other extensions.

    Notes
    -----
    * Commands in this file are sorted alphabetically.
    """

    @commands.command(aliases=["char"])
    async def charinfo(self, ctx: IreContext, *, characters: str) -> None:
        """Shows information about character(-s).

        Only up to a 10 characters at a time though.

        Parameters
        ----------
        characters
            Input up to 10 characters to get format info about.

        """

        def to_string(c: str) -> str:
            name = unicodedata.name(c, None)
            return f"\\N{{{name}}}" if name else "Name not found."

        names = " ".join(to_string(c) for c in characters[:10])
        if len(characters) > 10:
            names += "(Output was too long: displaying only first 10 chars)"
        await ctx.send(names)

    @guards.is_online()
    @commands.command()
    async def clip(self, ctx: IreContext) -> None:
        """Create a clip for last 30 seconds of the stream."""
        clip = await ctx.broadcaster.create_clip(token_for=const.UserID.Bot)
        await ctx.send(f"https://clips.twitch.tv/{clip.id}")

    @commands.command(name="commands", aliases=["help"])
    async def command_list(self, ctx: IreContext) -> None:
        """Get a list of bot commands."""
        await ctx.send("Not implemented yet.")

    @commands.command()
    async def controller(self, ctx: IreContext) -> None:
        """Get Irene's current controller model."""
        await ctx.send("Razer Wolverine V3 Tournament Edition Xbox Black")

    @commands.command()
    async def discord(self, ctx: IreContext) -> None:
        """Link to my discord community server."""
        await ctx.send(f"{const.STV.Discord} discord.gg/K8FuDeP")

    @commands.command()
    async def donate(self, ctx: IreContext) -> None:
        """Link to my Donation page."""
        await ctx.send("donationalerts.com/r/irene_adler__")

    @commands.command()
    async def followage(self, ctx: IreContext) -> None:
        """Get your follow age."""
        # just a small joke to teach people
        await ctx.send("Just click your name 4Head")

    @commands.command(aliases=["hi", "yo", "hallo"])
    async def hello(self, ctx: IreContext) -> None:
        """Hello."""
        await ctx.send(const.STV.hello)

    @commands.command(aliases=["lorem", "ipsum"])
    async def loremipsum(self, ctx: IreContext) -> None:
        """Lorem ipsum."""
        await ctx.send(  # cSpell:disable
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. "
            "Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
            "Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta. Mauris massa. "
            "Vestibulum lacinia arcu eget nulla. Class aptent taciti sociosqu ad litora torquent per conubia nostra, "
            "per inceptos himenaeos. Curabitur sodales ligula in libero. Sed dignissim lacinia nunc. Curabitur tortor. "
            "Pellentesque nibh.",
        )  # cSpell:enable

    @commands.command()
    async def love(self, ctx: IreContext, *, arg: str) -> None:
        """Measure love between chatter and `arg`.

        arg can be a user or anything else.
        """

        def choose_love_emote() -> tuple[int, str]:
            love = random.randint(0, 100)
            if love < 10:
                emote = const.STV.donkSad
            if love < 33:
                emote = const.FFZ.sadKEK
            elif love < 66:
                emote = const.STV.donkHappy
            elif love < 88:
                emote = const.STV.widepeepoHappyRightHeart
            else:
                emote = const.STV.DankL
            return love, emote

        # chr(917504) is a weird "unknown" invisible symbol 7tv appends to the message
        # and the rest is just to get a possible clear name in case chatter was mentioning one
        potential_name = arg.replace(chr(917504), "").strip().removeprefix("@").lower()
        if potential_name in const.Bots:
            await ctx.send("Silly organic, bots cannot know love BibleThump")
        elif potential_name == ctx.chatter.name:
            await ctx.send("pls")
        elif potential_name == const.LowerName.Irene:
            await ctx.send(f"The {ctx.chatter.mention}'s love for our beloved Irene transcends all")
        else:
            love, emote = choose_love_emote()
            await ctx.send(f"{love}% love between {ctx.chatter.mention} and {arg} {emote}")

    @commands.command()
    async def lurk(self, ctx: IreContext) -> None:
        """Make it clear to the chat that you are lurking."""
        await ctx.send(f"{ctx.chatter.mention} is now lurking {const.STV.DankLurk} Have fun {const.STV.donkHappy}")
        # TODO: maybe make something like returning message for them with a time that they lurked

    @commands.command(name="decide", aliases=["ball", "8ball", "answer", "question", "yesno"])
    async def magic_ball(self, ctx: IreContext, *, text: str | None = None) -> None:
        """Get a random answer from a Magic Ball.

        Better than ChatGPT.
        """
        if not text:
            await ctx.send(f"Wrong command usage! You need to ask the bot yes/no question with it {const.FFZ.peepoWTF}")
            return

        options = [
            "69% for sure",
            "Are you kidding?!",
            "Ask again",
            "Better not tell you now",
            "Definitely... not",
            "Don't bet on it",
            "don't count on it",
            "Doubtful",
            "For sure",
            "Forget about it",
            "Hah!",
            "Hells no.",
            "If the Twitch gods grant it",
            "Impossible!In due time",
            "Indubitably!",
            "It is certain",
            "It is so",
            "Leaning towards no",
            "Look deep in your heart and you will see the answer",
            "Most definitely",
            "Most likely",
            "My sources say yes",
            "Never",
            "No way!",
            "No.",
            "Of course!",
            "Outlook good",
            "Outlook not so good",
            "Perhaps",
            "Possibly",
            "Please.",
            "That's a tough one",
            "That's like totally a yes. Duh!",
            "The answer might not be not no",
            "The answer to that isn't pretty",
            "The heavens point to yes",
            "Who knows?",
            "Without a doubt",
            "Yesterday it would've been a yes, but today it's a yep",
            "You will have to wait",
        ]
        await ctx.send(random.choice(options))

    @commands.command()
    async def nomic(self, ctx: IreContext) -> None:
        """No mic."""
        await ctx.send("Please read info below the stream, specifically, FAQ")

    @commands.command()
    async def oversight(self, ctx: IreContext) -> None:
        """Give me the famous Oversight Dark Willow copypaste."""
        await ctx.send(
            "The biggest🙌💯oversight🔭🔍with Dark✊🏾Willow🌳is that she's unbelievably sexy🤤💦🍆. "
            "I can't go on a hour🕐of my day🌞without thinking💭💦about plowing👉👌🚜that tight😳wooden🌳ass💦🍑. "
            "I'd kill🔫😱a man👨 in cold❄️blood😈just to spend💷a minute⏱️with her crotch🍑😫grinding against "
            "my throbbing💦🍆💦manhood💦🍆💦as she whispers🙊😫terribly dirty💩💩things to me in her "
            "geographically🌍🌎ambiguous🌏🗺️accent 🇮🇪",
        )

    @commands.command(aliases=["pcparts", "specs"])
    async def pc(self, ctx: IreContext) -> None:
        """Get Irene's current PC setup."""
        await ctx.send("pcpartpicker.com/user/aluerie/saved/dY497P")

    @commands.command()
    async def playlist(self, ctx: IreContext) -> None:
        """Get the link to my Spotify playlist."""
        await ctx.send("open.spotify.com/playlist/7fVAcuDPLVAUL8555vy8Kz?si=b26cecab2cf24608")  # cSpell: ignore DPLVAUL

    @commands.cooldown(rate=1, per=60, key=commands.BucketType.channel)
    @commands.command(aliases=["rr", "russianroulette"])
    async def roulette(self, ctx: IreContext) -> None:
        """Play russian roulette."""
        mention = ctx.chatter.mention

        for phrase in [
            f"/me places the revolver to {mention}'s head {const.FFZ.monkaGIGAGUN}",
            f"{const.DIGITS[3]} {const.Global.monkaS} ... ",
            f"{const.DIGITS[2]} {const.FFZ.monkaH} ... ",
            f"{const.DIGITS[1]} {const.FFZ.monkaGIGA} ... The trigger is pulled... ",
        ]:
            await ctx.send(phrase)
            await asyncio.sleep(0.87)

        if ctx.chatter.moderator:
            # Special case: we will not kill any moderators
            await ctx.send(f"Revolver malfunctions! {mention} is miraculously alive! {const.STV.PogChampPepe}")
        elif random.randint(0, 1):
            await ctx.send(f"Revolver clicks! {mention} has lived to survive roulette! {const.STV.POGCRAZY}")
        else:
            await ctx.send(f"Revolver fires! {mention} lies dead in chat {const.STV.Deadge}")

            await ctx.broadcaster.timeout_user(
                moderator=const.UserID.Bot,
                user=ctx.chatter.id,
                duration=30,
                reason="Lost in !russianroulette",
            )

    @commands.command()  # maybe the name "since" isn't the best but "uptime", "online" are already taken
    async def since(self, ctx: IreContext) -> None:
        """🔬 Get the bot's uptime.

        Uptime is time for which the bot has been online without any crashes or reboots.
        """
        await ctx.send(
            f"Last reboot {self.bot.launch_time.strftime('%H:%M %d/%b/%y')}; "
            f"It's been {fmt.timedelta_to_words(datetime.datetime.now(datetime.UTC) - self.bot.launch_time)}."
        )

    @guards.is_online()
    @commands.is_moderator()
    @commands.command(aliases=["so"])
    async def shoutout(self, ctx: IreContext, user: twitchio.User) -> None:
        """Do /shoutout to a user."""
        await ctx.broadcaster.send_shoutout(to_broadcaster=user.id, moderator=const.UserID.Bot)

    @commands.cooldown(rate=1, per=10, key=commands.BucketType.channel)
    @commands.command()
    async def song(self, ctx: IreContext) -> None:
        """Get currently played song on Spotify."""
        url = f"https://spotify.aidenwallis.co.uk/u/{config['TOKENS']['SPOTIFY_AIDENWALLIS']}"
        async with self.bot.session.get(url) as resp:
            msg = await resp.text()

        if not resp.ok:
            answer = f"Irene needs to login + authorize for the tool to work {const.STV.dankFix}"

        if msg == "User is currently not playing any music on Spotify.":
            answer = f"{const.STV.Erm} No music is being played"
        elif msg.startswith("Error:"):
            # not sure how else to handle "Error: Request failed with status code 429" and such
            # if this keeps happening - we can scrape the overlay page for the song title / artist lol;
            # but we need selenium bcs the text is generated by JavaScript which is extremely over
            # the top to include as dependency for this
            # f"https://nowplaying.aidenwallis.co.uk/{config['TOKENS']['SPOTIFY_AIDENWALLIS']}"
            answer = (
                f"{const.STV.DankReading} {msg} {const.STV.DankThink} "
                "You can probably look the song title on the screen in one of the corners."
            )
        else:
            answer = f"{const.STV.donkJam} {msg}"

        await ctx.send(answer)

    @commands.command()
    async def source(self, ctx: IreContext) -> None:
        """Get the link to the bot's GitHub repository."""
        await ctx.send(f"github.com/Aluerie/IreBot {const.STV.DankReading}")

    @commands.command()
    async def translate(self, ctx: IreContext, *, text: str) -> None:
        """Translate given text to English.

        Uses Google Translate. Autodetects source language.

        Sources
        -------
        * My own discord bot (but the code there is also taken from other places)
            https://github.com/Aluerie/AluBot/blob/main/ext/educational/language/translation.py
        """
        result = await translate(text, session=self.bot.session)
        answer = f"{const.STV.ApuBritish} [{result.source_lang} to {result.target_lang}] {result.translated}"
        await ctx.send(answer)

    @commands.command(aliases=["id", "twitchid"])
    async def twitch_id(self, ctx: IreContext, *, user: twitchio.User) -> None:
        """Get mentioned @user numeric twitch_id."""
        await ctx.send(f"Twitch ID for {user.mention}: {user.id}")

    @commands.command()
    async def uptime(self, ctx: IreContext) -> None:
        """Get stream uptime."""
        stream = await self.bot.irene.stream()
        if stream is None:
            await ctx.send(f"Stream is offline {const.BTTV.Offline}")
        else:
            uptime = datetime.datetime.now(datetime.UTC) - stream.started_at
            await ctx.send(f"{fmt.timedelta_to_words(uptime)} {const.STV.peepoDapper}")

    @commands.command(aliases=["seppuku"])
    async def vanish(self, ctx: IreContext) -> None:
        """Allows for chatters to vanish from the chat by time-outing themselves."""
        if ctx.chatter.moderator:
            if "seppuku" in ctx.message.text:
                msg = f"Emperor Kappa does not allow you this honour, {ctx.chatter.mention} (bcs you're a moderator)"
            else:
                msg = "Moderators can't vanish"
            await ctx.send(msg)
        else:
            await ctx.broadcaster.timeout_user(
                moderator=const.UserID.Bot,
                user=ctx.chatter.id,
                duration=1,
                reason="Used !vanish",
            )

    @commands.command(aliases=["version", "packages", "libraries"])
    async def versions(self, ctx: IreContext) -> None:
        """🔬 Get info bot's main Python Packages."""
        curious_packages = [
            "twitchio",
        ]  # list of packages versions of which I'm interested the most
        pv = sys.version_info  # python version

        await ctx.send(
            f"Python {pv.major}.{pv.minor}.{pv.micro} | "
            + " | ".join(f"{package}: {importlib.metadata.version(package)}" for package in curious_packages)
        )

    @commands.command()
    async def vods(self, ctx: IreContext) -> None:
        """Get the link to youtube vods archive."""
        await ctx.send(f"youtube.com/@AluerieVODS/ {const.STV.Cinema}")


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(StableCommands(bot))
