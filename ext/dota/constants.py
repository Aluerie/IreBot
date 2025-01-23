"""DOTA 2 CONSTANTS.

Just a separate file for Dota only constants.
"""

# /* cSpell:disable */
"""HERO ALIASES.

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
HERO_ALIASES = {
    1: ["am", "wei", "magina"],  # AntiMage
    2: ["mogul"],  # Axe
    3: [],  # Bane
    4: ["bs", "strygwyr", "seeker", "blood"],  # Bloodseeker
    5: ["cm", "rylai", "wolf"],  # CrystalMaiden
    6: ["traxex"],  # DrowRanger
    7: ["es", "raigor"],  # Earthshaker
    8: ["yurnero"],  # Juggernaut
    9: ["princess", "moon", "potm"],  # Mirana
    10: ["morph"],  # Morphling
    11: ["sf", "nevermore"],  # ShadowFiend
    12: ["pl", "azwraith"],  # PhantomLancer
    13: ["faerie dragon", "fd"],  # Puck
    14: ["butcher"],  # Pudge
    15: ["lightning revenant"],  # Razor
    16: ["sk", "crixalis"],  # SandKing
    17: ["ss", "raijin", "thunderkeg", "storm"],  # StormSpirit
    18: ["rogue knight"],  # Sven
    19: ["tony"],  # Tiny
    20: ["vs", "shendelzare", "venge"],  # VengefulSpirit
    21: ["wr", "lyralei"],  # Windranger
    22: ["lord of heaven", "zuus"],  # Zeus
    23: ["admiral"],  # Kunkka
    25: ["slayer"],  # Lina
    26: ["demon witch"],  # Lion
    27: ["ss", "rhasta", "shaman"],  # ShadowShaman
    28: [],  # Slardar
    29: ["th", "leviathan"],  # Tidehunter
    30: ["wd", "zharvakko"],  # WitchDoctor
    31: ["ethreain"],  # Lich
    32: ["stealth assassin", "sa"],  # Riki
    33: ["nigma"],  # Enigma
    34: ["boush"],  # Tinker
    35: ["kardel"],  # Sniper
    36: ["rotundjere", "necrolyte"],  # Necrophos
    37: ["wl", "demnok lannik"],  # Warlock
    38: ["bm"],  # Beastmaster
    39: ["qop", "akasha"],  # QueenOfPain
    40: ["lesale"],  # Venomancer
    41: ["fv"],  # FacelessVoid
    42: ["sk", "snk", "wk", "skeleton", "one true king", "ostarion"],  # WraithKing
    43: ["dp", "krobelus"],  # DeathProphet
    44: ["pa", "mortred"],  # PhantomAssassin
    45: [],  # Pugna
    46: ["ta", "lanaya"],  # TemplarAssassin
    47: ["netherdrake"],  # Viper
    48: ["moon rider"],  # Luna
    49: ["dk", "davion", "dragon's blood"],  # DragonKnight
    50: [],  # Dazzle
    51: ["rattletrap", "cw", "clock"],  # Clockwerk
    52: ["ts"],  # Leshrac
    53: ["np", "furion"],  # NaturesProphet
    54: ["ls", "naix"],  # Lifestealer
    55: ["ds", "ishkafel"],  # DarkSeer
    56: [],  # Clinkz
    57: ["purist thunderwrath"],  # Omniknight
    58: ["aiushtha", "ench", "bambi"],  # Enchantress
    59: [],  # Huskar
    60: ["ns", "balanar"],  # NightStalker
    61: ["arachnia", "brood", "spider"],  # Broodmother
    62: ["bh", "gondar"],  # BountyHunter
    63: ["nw", "skitskurr"],  # Weaver
    64: ["thd", "twin headed dragon"],  # Jakiro
    65: ["bat"],  # Batrider
    66: ["holy knight"],  # Chen
    67: ["mercurial"],  # Spectre
    68: ["aa", "kaldr", "apparition"],  # AncientApparition
    69: [],  # Doom
    70: ["ulfsaar"],  # Ursa
    71: ["sb", "barathrum", "bara"],  # SpiritBreaker
    72: ["aurel", "gyro"],  # Gyrocopter
    73: ["razzil", "alch"],  # Alchemist
    74: ["kid", "invo"],  # Invoker
    75: ["nortrom"],  # Silencer
    76: ["od"],  # OutworldDevourer
    77: ["banehallow", "wolf"],  # Lycan
    78: ["brew", "mangix"],  # Brewmaster
    79: ["sd"],  # ShadowDemon
    80: ["ld", "bear", "sylla"],  # LoneDruid
    81: ["ck", "chaos"],  # ChaosKnight
    82: ["geomancer", "meepwn"],  # Meepo
    83: ["tree"],  # TreantProtector
    84: ["om", "ogre"],  # OgreMagi
    85: ["dirge"],  # Undying
    86: [],  # Rubick
    87: ["dis"],  # Disruptor
    88: ["na", "nyx"],  # NyxAssassin
    89: ["naga", "slithice"],  # NagaSiren
    90: ["keeper", "ezalor", "kotl"],  # KeeperOfTheLight
    91: ["wisp"],  # Io
    92: ["visage", "necrolic"],  # Visage
    93: ["slark"],  # Slark
    94: ["medusa", "gorgon"],  # Medusa
    95: ["troll", "jahrakal"],  # TrollWarlord
    96: ["centaur", "cent"],  # CentaurWarrunner
    97: ["magnataur", "magnus", "mag"],  # Magnus
    98: ["rizzrack", "shredder", "timber"],  # Timbersaw
    99: ["rigwarl", "bb", "bristle"],  # Bristleback
    100: ["ymir"],  # Tusk
    101: ["sm", "dragonus", "sky"],  # SkywrathMage
    102: ["abaddon", "aba"],  # Abaddon
    103: ["et"],  # ElderTitan
    104: ["tresdin", "legion", "lc"],  # LegionCommander
    105: ["squee", "spleen", "spoon"],  # Techies
    106: ["xin", "ember", "es"],  # EmberSpirit
    107: ["es", "kaolin", "earth"],  # EarthSpirit
    108: ["pitlord", "azgalor", "ul"],  # Underlord
    109: ["tb"],  # Terrorblade
    110: ["ph"],  # Phoenix
    111: ["ora", "nerif"],  # Oracle
    112: ["ww", "auroth"],  # WinterWyvern
    113: ["zet", "aw", "arc", "zett"],  # ArcWarden
    114: ["mk", "sun wukong", "wukong"],  # MonkeyKing
    119: ["dw", "mireska", "oversight", "biggest oversight", "waifu"],  # Dark Willow
    120: ["ar", "pango"],  # Pangolier
    121: ["gs", "grim"],  # Grimstroke
    123: ["squirrel", "hw", "furry"],  # Hoodwink
    126: ["void", "vs", "inai"],  # Void Spirit
    128: ["snap", "mortimer", "beatrix"],  # Snapfire
    129: ["mars"],  # Mars
    131: ["rm", "marionetto", "cogliostro"],  # Ringmaster
    135: ["dawnbreaker", "valora", "mommy", "dawn"],  # Dawnbreaker
    136: ["AYAYA"],  # Marci
    137: ["pb"],  # Primal Beast
    138: [],  # Muerta
}
# /* cSpell:enable */

PLAYER_COLOURS = [
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
