from __future__ import annotations

import asyncio
import datetime
import random
import unicodedata
from typing import TYPE_CHECKING

import twitchio  # noqa: TC002
from twitchio.ext import commands

from bot import IreComponent
from config import config
from utils import const, formats, guards

if TYPE_CHECKING:
    from bot import IreBot


class SimpleCommands(IreComponent):
    """Simple commands.

    Simple in a sense that they are just somewhat static and their implementation is simple.
    Probably a better name would be "uncategorised code commands"
    because they are defined here in code, instead of
    sitting in the database like commands from `custom_commands.py` do.
    """

    @guards.is_online()
    @commands.command()
    async def clip(self, ctx: commands.Context) -> None:
        """Create a clip for last 30 seconds of the stream."""
        clip = await ctx.broadcaster.create_clip(token_for=const.UserID.Bot)
        await ctx.send(f"https://clips.twitch.tv/{clip.id}")

    @commands.command(name="commands", aliases=["help"])
    async def command_list(self, ctx: commands.Context) -> None:
        """Get a list of bot commands."""
        await ctx.send("Not implemented yet.")

    @commands.command()
    async def discord(self, ctx: commands.Context) -> None:
        """Link to my discord community server."""
        await ctx.send(f"{const.STV.Discord} discord.gg/K8FuDeP")

    @commands.command()
    async def donate(self, ctx: commands.Context) -> None:
        """Link to my Donation page."""
        await ctx.send("donationalerts.com/r/irene_adler__")

    @commands.command()
    async def followage(self, ctx: commands.Context) -> None:
        """Get your follow age."""
        # just a small joke to teach people
        await ctx.send("Just click your name 4Head")

    @commands.command(aliases=["hi", "yo", "hallo"])
    async def hello(self, ctx: commands.Context) -> None:
        """Hello."""
        await ctx.send(const.STV.hello)

    @commands.command()
    async def love(self, ctx: commands.Context, *, arg: str) -> None:
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

    @commands.command(aliases=["lorem", "ipsum"])
    async def loremipsum(self, ctx: commands.Context) -> None:
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
    async def lurk(self, ctx: commands.Context) -> None:
        """Make it clear to the chat that you are lurking."""
        await ctx.send(f"{ctx.chatter.mention} is now lurking {const.STV.DankLurk} Have fun {const.STV.donkHappy}")
        # TODO: maybe make something like returning message for them with a time that they lurked

    @commands.command(name="decide", aliases=["ball", "8ball", "answer", "question", "yesno"])
    async def magic_ball(self, ctx: commands.Context, *, text: str | None = None) -> None:
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
            "No wais",
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
    async def nomic(self, ctx: commands.Context) -> None:
        """No mic."""
        await ctx.send("Please read info below the stream, specifically, FAQ")

    @commands.command()
    async def oversight(self, ctx: commands.Context) -> None:
        """Give me the famous Oversight Dark Willow copypaste."""
        await ctx.send(
            "The biggest🙌💯oversight🔭🔍with Dark✊🏾Willow🌳is that she's unbelievably sexy🤤💦🍆. "
            "I can't go on a hour🕐of my day🌞without thinking💭💦about plowing👉👌🚜that tight😳wooden🌳ass💦🍑. "
            "I'd kill🔫😱a man👨 in cold❄️blood😈just to spend💷a minute⏱️with her crotch🍑😫grinding against "
            "my throbbing💦🍆💦manhood💦🍆💦as she whispers🙊😫terribly dirty💩💩things to me in her "
            "geographically🌍🌎ambiguous🌏🗺️accent 🇮🇪",
        )

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Ping the bot.

        Currently doesn't provide any useful info.
        """
        await ctx.send("\N{TABLE TENNIS PADDLE AND BALL} Pong!")

    @commands.command()
    async def playlist(self, ctx: commands.Context) -> None:
        """Get the link to my Spotify playlist."""
        await ctx.send("open.spotify.com/playlist/7fVAcuDPLVAUL8555vy8Kz?si=b26cecab2cf24608")  # cSpell: ignore DPLVAUL

    @commands.cooldown(rate=1, per=60, key=commands.BucketType.channel)
    @commands.command(aliases=["rr", "russianroulette"])
    async def roulette(self, ctx: commands.Context) -> None:
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

    @guards.is_online()
    @commands.is_moderator()
    @commands.command(aliases=["so"])
    async def shoutout(self, ctx: commands.Context, user: twitchio.User) -> None:
        """Do /shoutout to a user."""
        await ctx.broadcaster.send_shoutout(
            to_broadcaster=user.id,
            moderator=const.UserID.Bot,
            token_for=const.UserID.Bot,
        )

    @commands.command()
    async def song(self, ctx: commands.Context) -> None:
        """Get currently played song on Spotify."""
        url = f"https://spotify.aidenwallis.co.uk/u/{config['TOKENS']['SPOTIFY_AIDENWALLIS']}"
        async with self.bot.session.get(url) as resp:
            msg = await resp.text()

        if not resp.ok:
            answer = f"Irene needs to login + authorize {const.STV.dankFix}"
        if msg == "User is currently not playing any music on Spotify.":
            answer = f"{const.STV.Erm} No music is being played"
        else:
            answer = f"{const.STV.donkJam} {msg}"
        await ctx.send(answer)

    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        """A bit bio information about the bot."""
        await ctx.send(f"I'm a personal Irene's bot, made by Irene. {const.STV.AYAYA}")

    @commands.command()
    async def source(self, ctx: commands.Context) -> None:
        """Get the link to the bot's GitHub repository."""
        await ctx.send(f"github.com/Aluerie/IreBot {const.STV.DankReading}")

    @commands.command()
    async def uptime(self, ctx: commands.Context) -> None:
        """Get stream uptime."""
        stream = await self.bot.irene_stream()
        if stream is None:
            await ctx.send(f"Stream is offline {const.BTTV.Offline}")
        else:
            uptime = datetime.datetime.now(datetime.UTC) - stream.started_at
            await ctx.send(f"{formats.timedelta_to_words(uptime)} {const.STV.peepoDapper}")

    @commands.command(aliases=["seppuku"])
    async def vanish(self, ctx: commands.Context) -> None:
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

    @commands.command()
    async def vods(self, ctx: commands.Context) -> None:
        """Get the link to youtube vods archive."""
        await ctx.send(f"youtube.com/@AluerieVODS/ {const.STV.Cinema}")

    @commands.command(aliases=["char"])
    async def charinfo(self, ctx: commands.Context, *, characters: str) -> None:
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

    @commands.command(aliases=["id", "twitchid"])
    async def twitch_id(self, ctx: commands.Context, *, user: twitchio.User) -> None:
        """Get mentioned @user numeric twitch_id."""
        await ctx.send(f"Twitch ID for {user.mention}: {user.id}")

    @commands.command(aliases=["pcparts", "specs"])
    async def pc(self, ctx: commands.Context) -> None:
        """Get Irene's current PC setup."""
        await ctx.send("pcpartpicker.com/user/aluerie/saved/dY497P")


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(SimpleCommands(bot))
