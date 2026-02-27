from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, override

import steam
from steam.ext.dota2 import Hero, User as Dota2User
from twitchio.ext import commands

try:
    from utils import const, errors, fuzzy
except ModuleNotFoundError:
    import sys

    # Just for lazy testing (in the end of this file);
    sys.path.append("D:/CODE/IreBot/src")

    from utils import const, errors, fuzzy

if TYPE_CHECKING:
    from steam.ext.dota2 import ProfileCard

    from core import IreContext


__all__ = (
    "PARTY_MEMBERS_PATTERN",
    "SteamUserConverter",
    "SteamUserNotFound",
    "extract_hero_index",
    "rank_medal_display_name",
)

PARTY_MEMBERS_PATTERN = re.compile(r"members\s{\ssteam_id:\s([0-9]+)")

# /* cSpell:disable */
HERO_ALIASES = {
    # HERO ALIASES.
    #
    # The list mainly for !profile/!items command so people can just write "!items CM"
    # and the bot will send Crystal Maiden's items.
    #
    # The list includes mostly
    # * abbreviations, i.e. "cm";
    # * persona names i.e. "wei";
    # * dota 1 names , i.e. "traxex"
    # * official names, i.e. "beastmaster";
    # * short forms of any from above, i.e. "cent";
    # * just nicknames, aliases or common names that people sometimes *actually* use for Dota 2 heroes ;
    #
    # It doesn't include aliases that people don't use
    # i.e. nobody calls techies as "Squee, Spleen & Spoon"
    #
    Hero.Abaddon: ["abaddon", "aba"],
    Hero.Alchemist: ["alch", "alchemist"],
    Hero.AncientApparition: ["aa", "apparition", "ancient apparition"],
    Hero.AntiMage: ["am", "wei", "magina", "anti-mage", "antimage"],
    Hero.ArcWarden: ["aw", "arc", "zett", "arc warden"],
    Hero.Axe: ["axe"],
    Hero.Bane: ["bane"],
    Hero.Batrider: ["bat", "batrider"],
    Hero.Beastmaster: ["bm", "beastmaster"],
    Hero.Bloodseeker: ["bs", "strygwyr", "seeker", "blood", "bloodseeker"],
    Hero.BountyHunter: ["bh", "gondar", "bounty hunter"],
    Hero.Brewmaster: ["brew", "brewmaster"],
    Hero.Bristleback: ["bb", "bristle", "bristleback"],
    Hero.Broodmother: ["brood", "spider", "broodmother"],
    Hero.CentaurWarrunner: ["centaur", "cent", "centaur warrunner"],
    Hero.ChaosKnight: ["ck", "chaos", "chaos knight"],
    Hero.Chen: ["chen"],
    Hero.Clinkz: ["clinkz"],
    Hero.Clockwerk: ["clock", "clockwerk"],
    Hero.CrystalMaiden: ["cm", "rylai", "crystal maiden"],
    Hero.DarkSeer: ["ds", "dark seer"],
    Hero.DarkWillow: ["dw", "mireska", "oversight", "dark willow"],
    Hero.Dawnbreaker: ["dawnbreaker", "valora", "dawn"],
    Hero.Dazzle: ["dazzle"],
    Hero.DeathProphet: ["dp", "krobelus", "death prophet"],
    Hero.Disruptor: ["dis", "disruptor"],
    Hero.Doom: ["doom"],
    Hero.DragonKnight: ["dk", "davion", "dragon knight"],
    Hero.DrowRanger: ["traxex", "drow", "drow ranger"],
    Hero.EarthSpirit: ["es", "kaolin", "earth", "earth spirit"],
    Hero.Earthshaker: ["es", "earthshaker"],
    Hero.ElderTitan: ["et", "elder titan"],
    Hero.EmberSpirit: ["xin", "ember", "es", "ember spirit"],
    Hero.Enchantress: ["ench", "enchantress"],
    Hero.Enigma: ["nigma", "enigma"],
    Hero.FacelessVoid: ["fv", "faceless void"],
    Hero.Grimstroke: ["grim", "grimstroke"],
    Hero.Gyrocopter: ["gyro", "gyrocopter"],
    Hero.Hoodwink: ["hood", "hw", "hoodwink"],
    Hero.Huskar: ["huskar"],
    Hero.Invoker: ["invo", "invoker"],
    Hero.Io: ["wisp", "io"],
    Hero.Jakiro: ["thd", "twin headed dragon", "jakiro"],
    Hero.Juggernaut: ["yurnero", "jugg", "juggernaut"],
    Hero.KeeperOfTheLight: ["keeper", "ezalor", "kotl", "keeper of the light"],
    Hero.Kez: ["kez"],
    Hero.Kunkka: ["admiral", "kunkka"],
    Hero.Largo: ["largo"],
    Hero.LegionCommander: ["tresdin", "legion", "lc", "legion commander"],
    Hero.Leshrac: ["lesh", "leshrac"],
    Hero.Lich: ["lich"],
    Hero.Lifestealer: ["ls", "naix", "lifestealer"],
    Hero.Lina: ["slayer", "lina"],
    Hero.Lion: ["demon witch", "lion"],
    Hero.LoneDruid: ["ld", "lone druid"],
    Hero.Luna: ["moon rider", "luna"],
    Hero.Lycan: ["lycan"],
    Hero.Magnus: ["mag", "magnus"],
    Hero.Marci: ["marci"],
    Hero.Mars: ["mars"],
    Hero.Medusa: ["medusa"],
    Hero.Meepo: ["meepo"],
    Hero.Mirana: ["potm", "mirana"],
    Hero.MonkeyKing: ["mk", "wukong", "monkey king"],
    Hero.Morphling: ["morph", "morphling"],
    Hero.Muerta: ["muerta"],
    Hero.NagaSiren: ["naga", "naga siren"],
    Hero.NaturesProphet: ["np", "furion", "nature's prophet"],
    Hero.Necrophos: ["necro", "necrophos"],
    Hero.NightStalker: ["ns", "balanar", "night stalker"],
    Hero.NyxAssassin: ["nyx", "nyx assassin"],
    Hero.OgreMagi: ["ogre", "ogre magi"],
    Hero.Omniknight: ["omniknight"],
    Hero.Oracle: ["oracle"],
    Hero.OutworldDestroyer: ["od", "outworld destroyer"],
    Hero.Pangolier: ["ar", "pango", "pangolier"],
    Hero.PhantomAssassin: ["pa", "mortred", "phantom assassin"],
    Hero.PhantomLancer: ["pl", "phantom lancer"],
    Hero.Phoenix: ["phoenix"],
    Hero.PrimalBeast: ["pb", "primal beast"],
    Hero.Puck: ["puck"],
    Hero.Pudge: ["butcher", "pudge"],
    Hero.Pugna: ["pugna"],
    Hero.QueenOfPain: ["qop", "akasha", "queen of pain", "queen"],
    Hero.Razor: ["razor"],
    Hero.Riki: ["riki"],
    Hero.Ringmaster: ["ringmaster"],
    Hero.Rubick: ["rubick"],
    Hero.SandKing: ["sk", "sand king"],
    Hero.ShadowDemon: ["sd", "shadow demon"],
    Hero.ShadowFiend: ["sf", "nevermore", "shadow fiend"],
    Hero.ShadowShaman: ["ss", "rhasta", "shaman", "shadow shaman"],
    Hero.Silencer: ["silencer"],
    Hero.SkywrathMage: ["sky", "skywrath mage"],
    Hero.Slardar: ["slardar"],
    Hero.Slark: ["slark"],
    Hero.Snapfire: ["snap", "snapfire"],
    Hero.Sniper: ["sniper"],
    Hero.Spectre: ["spectre"],
    Hero.SpiritBreaker: ["sb", "bara", "spirit breaker"],
    Hero.StormSpirit: ["ss", "storm", "storm spirit"],
    Hero.Sven: ["sven"],
    Hero.Techies: ["techies"],
    Hero.TemplarAssassin: ["ta", "lanaya", "templar assassin"],
    Hero.Terrorblade: ["tb", "terrorblade"],
    Hero.Tidehunter: ["th", "tidehunter"],
    Hero.Timbersaw: ["timber", "timbersaw"],
    Hero.Tinker: ["tinker"],
    Hero.Tiny: ["tiny"],
    Hero.TreantProtector: ["tree", "treant", "treant protector"],
    Hero.TrollWarlord: ["troll", "troll warlord"],
    Hero.Tusk: ["tusk"],
    Hero.Underlord: ["pitlord", "underlord"],
    Hero.Undying: ["dirge", "undying"],
    Hero.Ursa: ["ursa"],
    Hero.VengefulSpirit: ["vs", "venge", "vengeful spirit"],
    Hero.Venomancer: ["veno", "venomancer"],
    Hero.Viper: ["viper"],
    Hero.Visage: ["visage"],
    Hero.VoidSpirit: ["void", "vs", "void spirit"],
    Hero.Warlock: ["warlock"],
    Hero.Weaver: ["weaver"],
    Hero.Windranger: ["wr", "lyralei", "windranger"],
    Hero.WinterWyvern: ["ww", "winter wyvern"],
    Hero.WitchDoctor: ["wd", "witch doctor"],
    Hero.WraithKing: ["wk", "wraith king"],
    Hero.Zeus: ["zuus", "zeus"],
}
# /* cSpell:enable */


COLOR_ALIASES = {
    0: ["blue"],
    1: ["teal"],
    2: ["purple"],
    3: ["yellow"],
    4: ["orange"],
    5: ["pink"],
    6: ["olive", "grey"],  # it was originally grey in WC3, but idk, it's easy to confuse with lightblue I feel like.
    7: ["lightblue", "white"],
    8: ["darkgreen", "green"],
    9: ["brown"],
}


class SteamUserNotFound(commands.BadArgument):
    """For when a matching user cannot be found."""

    def __init__(self, argument: str) -> None:
        self.argument = argument
        super().__init__(f"User {argument!r} not found.", value=argument)


class SteamUserConverter(commands.Converter[Dota2User]):
    """Simple Steam User converter."""

    @override
    async def convert(self, ctx: IreContext, argument: str) -> Dota2User:
        try:
            return await ctx.bot.dota.fetch_user(steam.utils.parse_id64(argument))
        except steam.InvalidID:
            id64 = await steam.utils.id64_from_url(argument)
            if id64 is None:
                raise SteamUserNotFound(argument) from None
            return await ctx.bot.dota.fetch_user(id64)
        except TimeoutError:
            raise SteamUserNotFound(argument) from None


def rank_medal_display_name(profile_card: ProfileCard) -> str:
    """Get human-readable rank medal string out of player's Dota 2 Profile Card."""
    display_name = profile_card.rank_tier.division
    if stars := profile_card.rank_tier.stars:
        display_name += f" \N{BLACK STAR}{stars}"
    if number_rank := profile_card.leaderboard_rank:
        display_name += f" #{number_rank}"
    return display_name


def is_allowed_to_add_notable() -> Any:
    """Allow !npm add/remove/rename to only be invoked by certain people."""

    def predicate(ctx: IreContext) -> bool:
        # Maybe we will edit this to be some proper dynamic database thing;
        allowed_ids = (const.UserID.Irene, const.UserID.Aluerie, const.UserID.Xas)
        if ctx.chatter.id in allowed_ids:
            return True
        msg = f"You are not allowed to add notable players into the bot's database {const.FFZ.peepoPolice}"
        raise errors.RespondWithError(msg)

    return commands.guard(predicate)


def extract_hero_index(argument: str, heroes: list[Hero]) -> tuple[Hero, int]:
    """Convert command argument provided by user (twitch chatter) into a player_slot in the match.

    Uses fuzzy match to extract the likely match.

    It supports
    * player slot as digits;
    * player colors;
    * hero aliases (which include hero localized names, abbreviations and some common nicknames);

    Returns
    -------
    tuple[Hero, int]
        Matched hero as well as its index in the provided `heroes` list.
        This is because usually when this function is called, the `player slot` is also of a big interest.
    """
    if argument.isnumeric():
        # then the user typed only a number and our life is easy because it is a player slot
        # let's consider users normal: they start enumerating slots from 1 instead of 0.
        index = int(argument) - 1
        if index < 0:
            msg = f'Detected numeric input "{argument}" but player slot cannot be a negative number.'
            raise errors.RespondWithError(msg)

        try:
            return heroes[index], index
        except IndexError:
            msg = (
                f"Detected numeric input for player slot #{argument} but there are only {len(heroes)} players in this match."
            )
            raise errors.RespondWithError(msg) from None

    # Otherwise - we have to use the fuzzy search
    result: tuple[Hero | None, int] = (None, 0)

    # Step 1. Color aliases;
    for player_slot, color_aliases in COLOR_ALIASES.items():
        find = fuzzy.extract_one(argument, color_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
        if find and find[1] > result[1]:
            try:
                result = (heroes[player_slot], find[1])
            except ValueError:
                continue

    # Step 2. Hero aliases
    # Sort the hero list so heroes in the match come first (i.e. so "es" alias triggers on a hero in the match first)
    for hero, hero_aliases in sorted(HERO_ALIASES.items(), key=lambda x: x[0] in heroes, reverse=True):
        find = fuzzy.extract_one(argument, hero_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
        if find and find[1] > result[1]:
            result = (hero, find[1])

    if result[0] is None:
        msg = 'Sorry, didn\'t understand your query. Try something like "PA / 7 / Phantom Assassin / Blue".'
        raise errors.RespondWithError(msg)
    if result[0] not in heroes:
        msg = f"Hero {result[0]} is not present in the match."
        raise errors.RespondWithError(msg)

    return result


if __name__ == "__main__":
    # A little test.
    argument = "PA"
    self_heroes = [Hero.PhantomAssassin, Hero.Kez, Hero.KeeperOfTheLight, Hero.Io]

    res = extract_hero_index(argument, self_heroes)
    print(res)  # noqa: T201
