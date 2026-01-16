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
    Hero.Abaddon: ["abaddon", "aba", "abaddon"],
    Hero.Alchemist: ["razzil", "alch", "alchemist"],
    Hero.AncientApparition: ["aa", "kaldr", "apparition", "ancient apparition"],
    Hero.AntiMage: ["am", "wei", "magina", "anti-mage"],
    Hero.ArcWarden: ["zet", "aw", "arc", "zett", "arc warden"],
    Hero.Axe: ["mogul", "axe"],
    Hero.Bane: ["bane"],
    Hero.Batrider: ["bat", "batrider"],
    Hero.Beastmaster: ["bm", "beastmaster"],
    Hero.Bloodseeker: ["bs", "strygwyr", "seeker", "blood", "bloodseeker"],
    Hero.BountyHunter: ["bh", "gondar", "bounty hunter"],
    Hero.Brewmaster: ["brew", "mangix", "brewmaster"],
    Hero.Bristleback: ["rigwarl", "bb", "bristle", "bristleback"],
    Hero.Broodmother: ["arachnia", "brood", "spider", "broodmother"],
    Hero.CentaurWarrunner: ["centaur", "cent", "centaur warrunner"],
    Hero.ChaosKnight: ["ck", "chaos", "chaos knight"],
    Hero.Chen: ["holy knight", "chen"],
    Hero.Clinkz: ["clinkz"],
    Hero.Clockwerk: ["rattletrap", "cw", "clock", "clockwerk"],
    Hero.CrystalMaiden: ["cm", "rylai", "wolf", "crystal maiden"],
    Hero.DarkSeer: ["ds", "ishkafel", "dark seer"],
    Hero.DarkWillow: ["dw", "mireska", "oversight", "biggest oversight", "waifu", "dark willow"],
    Hero.Dawnbreaker: ["dawnbreaker", "valora", "mommy", "dawn", "dawnbreaker"],
    Hero.Dazzle: ["dazzle"],
    Hero.DeathProphet: ["dp", "krobelus", "death prophet"],
    Hero.Disruptor: ["dis", "disruptor"],
    Hero.Doom: ["doom"],
    Hero.DragonKnight: ["dk", "davion", "dragon's blood", "dragon knight"],
    Hero.DrowRanger: ["traxex", "drow ranger"],
    Hero.EarthSpirit: ["es", "kaolin", "earth", "earth spirit"],
    Hero.Earthshaker: ["es", "raigor", "earthshaker"],
    Hero.ElderTitan: ["et", "elder titan"],
    Hero.EmberSpirit: ["xin", "ember", "es", "ember spirit"],
    Hero.Enchantress: ["aiushtha", "ench", "bambi", "enchantress"],
    Hero.Enigma: ["nigma", "enigma"],
    Hero.FacelessVoid: ["fv", "faceless void"],
    Hero.Grimstroke: ["gs", "grim", "grimstroke"],
    Hero.Gyrocopter: ["aurel", "gyro", "gyrocopter"],
    Hero.Hoodwink: ["squirrel", "hw", "furry", "hoodwink"],
    Hero.Huskar: ["huskar"],
    Hero.Invoker: ["kid", "invo", "invoker"],
    Hero.Io: ["wisp", "io"],
    Hero.Jakiro: ["thd", "twin headed dragon", "jakiro"],
    Hero.Juggernaut: ["yurnero", "juggernaut"],
    Hero.KeeperOfTheLight: ["keeper", "ezalor", "kotl", "keeper of the light"],
    Hero.Kez: ["kez"],
    Hero.Kunkka: ["admiral", "kunkka"],
    Hero.Largo: ["largo"],
    Hero.LegionCommander: ["tresdin", "legion", "lc", "legion commander"],
    Hero.Leshrac: ["ts", "leshrac"],
    Hero.Lich: ["ethreain", "lich"],
    Hero.Lifestealer: ["ls", "naix", "lifestealer"],
    Hero.Lina: ["slayer", "lina"],
    Hero.Lion: ["demon witch", "lion"],
    Hero.LoneDruid: ["ld", "bear", "sylla", "lone druid"],
    Hero.Luna: ["moon rider", "luna"],
    Hero.Lycan: ["banehallow", "wolf", "lycan"],
    Hero.Magnus: ["magnataur", "magnus", "mag", "magnus"],
    Hero.Marci: ["AYAYA", "marci"],
    Hero.Mars: ["mars", "mars"],
    Hero.Medusa: ["medusa", "gorgon", "medusa"],
    Hero.Meepo: ["geomancer", "meepwn", "meepo"],
    Hero.Mirana: ["princess", "moon", "potm", "mirana"],
    Hero.MonkeyKing: ["mk", "sun wukong", "wukong", "monkey king"],
    Hero.Morphling: ["morph", "morphling"],
    Hero.Muerta: ["muerta"],
    Hero.NagaSiren: ["naga", "slithice", "naga siren"],
    Hero.NaturesProphet: ["np", "furion", "nature's prophet"],
    Hero.Necrophos: ["rotundjere", "necrolyte", "necrophos"],
    Hero.NightStalker: ["ns", "balanar", "night stalker"],
    Hero.NyxAssassin: ["na", "nyx", "nyx assassin"],
    Hero.OgreMagi: ["om", "ogre", "ogre magi"],
    Hero.Omniknight: ["purist thunderwrath", "omniknight"],
    Hero.Oracle: ["ora", "nerif", "oracle"],
    Hero.OutworldDestroyer: ["od", "outworld destroyer"],
    Hero.Pangolier: ["ar", "pango", "pangolier"],
    Hero.PhantomAssassin: ["pa", "mortred", "phantom assassin"],
    Hero.PhantomLancer: ["pl", "azwraith", "phantom lancer"],
    Hero.Phoenix: ["ph", "phoenix"],
    Hero.PrimalBeast: ["pb", "primal beast"],
    Hero.Puck: ["faerie dragon", "fd", "puck"],
    Hero.Pudge: ["butcher", "pudge"],
    Hero.Pugna: ["pugna"],
    Hero.QueenOfPain: ["qop", "akasha", "queen of pain", "queen"],
    Hero.Razor: ["lightning revenant", "razor"],
    Hero.Riki: ["stealth assassin", "sa", "riki"],
    Hero.Ringmaster: ["rm", "marionetto", "cogliostro", "ringmaster"],
    Hero.Rubick: ["rubick"],
    Hero.SandKing: ["sk", "crixalis", "sand king"],
    Hero.ShadowDemon: ["sd", "shadow demon"],
    Hero.ShadowFiend: ["sf", "nevermore", "shadow fiend"],
    Hero.ShadowShaman: ["ss", "rhasta", "shaman", "shadow shaman"],
    Hero.Silencer: ["nortrom", "silencer"],
    Hero.SkywrathMage: ["sm", "dragonus", "sky", "skywrath mage"],
    Hero.Slardar: ["slardar"],
    Hero.Slark: ["slark", "slark"],
    Hero.Snapfire: ["snap", "mortimer", "beatrix", "snapfire"],
    Hero.Sniper: ["kardel", "sniper"],
    Hero.Spectre: ["mercurial", "spectre"],
    Hero.SpiritBreaker: ["sb", "barathrum", "bara", "spirit breaker"],
    Hero.StormSpirit: ["ss", "raijin", "thunderkeg", "storm", "storm spirit"],
    Hero.Sven: ["rogue knight", "sven"],
    Hero.Techies: ["techies"],
    Hero.TemplarAssassin: ["ta", "lanaya", "templar assassin"],
    Hero.Terrorblade: ["tb", "terrorblade"],
    Hero.Tidehunter: ["th", "leviathan", "tidehunter"],
    Hero.Timbersaw: ["rizzrack", "shredder", "timber", "timbersaw"],
    Hero.Tinker: ["boush", "tinker"],
    Hero.Tiny: ["tony", "tiny"],
    Hero.TreantProtector: ["tree", "treant protector"],
    Hero.TrollWarlord: ["troll", "jahrakal", "troll warlord"],
    Hero.Tusk: ["ymir", "tusk"],
    Hero.Underlord: ["pitlord", "azgalor", "ul", "underlord"],
    Hero.Undying: ["dirge", "undying"],
    Hero.Ursa: ["ulfsaar", "ursa"],
    Hero.VengefulSpirit: ["vs", "shendelzare", "venge", "vengeful spirit"],
    Hero.Venomancer: ["lesale", "venomancer"],
    Hero.Viper: ["netherdrake", "viper"],
    Hero.Visage: ["visage"],
    Hero.VoidSpirit: ["void", "vs", "inai", "void spirit"],
    Hero.Warlock: ["wl", "demnok lannik", "warlock"],
    Hero.Weaver: ["nw", "skitskurr", "weaver"],
    Hero.Windranger: ["wr", "lyralei", "windranger"],
    Hero.WinterWyvern: ["ww", "auroth", "winter wyvern"],
    Hero.WitchDoctor: ["wd", "zharvakko", "witch doctor"],
    Hero.WraithKing: ["sk", "snk", "wk", "skeleton", "one true king", "ostarion", "wraith king"],
    Hero.Zeus: ["lord of heaven", "zuus", "zeus"],
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
