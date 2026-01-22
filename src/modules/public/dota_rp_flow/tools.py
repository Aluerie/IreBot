from __future__ import annotations

from steam.ext.dota2 import Hero

from utils import errors, fuzzy

__all__ = ("extract_hero_index",)

# /* cSpell:disable */
HERO_ALIASES = {
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
    if argument.isdigit():
        # then the user typed only a number and our life is easy because it is a player slot
        # let's consider users normal: they start enumerating slots from 1 instead of 0.
        player_slot = int(argument) - 1
        if not 0 <= player_slot <= 9:
            msg = "Sorry, player_slot can only be of 1-10 values."
            raise errors.RespondWithError(msg)
        return heroes[player_slot], player_slot

    # Otherwise - we have to use the fuzzy search

    # Step 1. Colors;
    player_slot_choice = (None, 0)
    for player_slot, color_aliases in COLOR_ALIASES.items():
        find = fuzzy.extract_one(argument, color_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
        if find and find[1] > player_slot_choice[1]:
            player_slot_choice = (player_slot, find[1])

    # Step 2. let's see if hero aliases can beat official
    hero_slot_choice = (None, 0)
    # Sort the hero list so heroes in the match come first (i.e. so "es" alias triggers on a hero in the match)
    for hero, hero_aliases in sorted(HERO_ALIASES.items(), key=lambda x: x[0] in heroes, reverse=True):
        find = fuzzy.extract_one(argument, hero_aliases, scorer=fuzzy.quick_token_sort_ratio, score_cutoff=49)
        if find and find[1] > hero_slot_choice[1]:
            hero_slot_choice = (hero, find[1])

    error_message = 'Sorry, didn\'t understand your query. Try something like "PA / 7 / Phantom Assassin / Blue".'
    if player_slot_choice[1] > hero_slot_choice[1]:
        # then color matched better
        player_slot = player_slot_choice[0]
        if player_slot is None:
            raise errors.RespondWithError(error_message)
        return heroes[player_slot], player_slot

    # Else: hero aliases matched better;
    hero = hero_slot_choice[0]
    if hero is None:
        raise errors.RespondWithError(error_message)

    try:
        player_slot = heroes.index(hero)
    except ValueError:
        msg = f"Hero {hero} is not present in the match."
        raise errors.RespondWithError(msg) from None

    return hero, player_slot
