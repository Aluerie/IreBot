"""DOTA 2 CONSTANTS.

Just a separate file for Dota only constants.

HERO ALIASES.

The list mainly for !profile/!items command where for example people can just write "!items CM"
and the bot will send Crystal Maiden items.

The list includes mostly
* abreviations ("cm")
* persona names ("wei")
* dota 1 names ("traxex")
* short forms of any from above ("cent")

This list doesn't include
* official names because the bot gets them from Hero enum at `steam.ext.dota2`

The list was created using:
* Stratz aliases data:
    query HeroAliases {
        constants {
            heroes {
            id
                aliases
            }
        }
    }
* tsunami's https://chatwheel.howdoiplay.com/ list
* my personal ideas
* my chatters help
* dotabod alias list https://github.com/dotabod/backend/blob/master/packages/dota/src/dota/lib/heroes.ts
"""

from steam.ext.dota2 import Hero

# /* cSpell:disable */
HERO_ALIASES = {
    Hero.Abaddon: ["abaddon", "aba"],
    Hero.Alchemist: ["alch", "alchemist"],
    Hero.AncientApparition: ["aa", "apparition", "ancient apparition"],
    Hero.AntiMage: ["am", "wei", "magina", "anti-mage"],
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
    Hero.Earthshaker: ["es", "raigor", "earthshaker"],
    Hero.ElderTitan: ["et", "elder titan"],
    Hero.EmberSpirit: ["xin", "ember", "es", "ember spirit"],
    Hero.Enchantress: ["ench", "enchantress"],
    Hero.Enigma: ["nigma", "enigma"],
    Hero.FacelessVoid: ["fv", "faceless void"],
    Hero.Grimstroke: ["grim", "grimstroke"],
    Hero.Gyrocopter: ["gyro", "gyrocopter"],
    Hero.Hoodwink: ["hood", "hoodwink"],
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
    Hero.LoneDruid: ["ld", "bear", "lone druid"],
    Hero.Luna: ["moon rider", "luna"],
    Hero.Lycan: ["lycan"],
    Hero.Magnus: ["mag", "magnus"],
    Hero.Marci: ["marci"],
    Hero.Mars: ["mars"],
    Hero.Medusa: ["medusa", "gorgon"],
    Hero.Meepo: ["geomancer", "meepo"],
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

PLAYER_COLORS = [
    "Blue",
    "Teal",
    "Purple",
    "Yellow",
    "Orange",
    "Pink",
    "Olive",
    "LightBlue",
    "DarkGreen",
    "Brown",
]

COLOR_ALIASES = {
    0: ["blue"],
    1: ["teal"],
    2: ["purple"],
    3: ["yellow"],
    4: ["orange"],
    5: ["pink"],
    6: ["olive", "grey"],  # it was originally grey in WC3, but idk, it's easy to confuse with lightblue I feel like.
    7: ["lightblue"],
    8: ["darkgreen"],
    9: ["brown"],
}
