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
    Hero.AntiMage: ["am", "wei", "magina", "anti-mage"],
    Hero.Axe: ["mogul", "axe"],
    Hero.Bane: ["bane"],
    Hero.Bloodseeker: ["bs", "strygwyr", "seeker", "blood", "bloodseeker"],
    Hero.CrystalMaiden: ["cm", "rylai", "wolf", "crystal maiden"],
    Hero.DrowRanger: ["traxex", "drow ranger"],
    Hero.Earthshaker: ["es", "raigor", "earthshaker"],
    Hero.Juggernaut: ["yurnero", "juggernaut"],
    Hero.Mirana: ["princess", "moon", "potm", "mirana"],
    Hero.Morphling: ["morph", "morphling"],
    Hero.ShadowFiend: ["sf", "nevermore", "shadow fiend"],
    Hero.PhantomLancer: ["pl", "azwraith", "phantom lancer"],
    Hero.Puck: ["faerie dragon", "fd", "puck"],
    Hero.Pudge: ["butcher", "pudge"],
    Hero.Razor: ["lightning revenant", "razor"],
    Hero.SandKing: ["sk", "crixalis", "sand king"],
    Hero.StormSpirit: ["ss", "raijin", "thunderkeg", "storm", "storm spirit"],
    Hero.Sven: ["rogue knight", "sven"],
    Hero.Tiny: ["tony", "tiny"],
    Hero.VengefulSpirit: ["vs", "shendelzare", "venge", "vengeful spirit"],
    Hero.Windranger: ["wr", "lyralei", "windranger"],
    Hero.Zeus: ["lord of heaven", "zuus", "zeus"],
    Hero.Kunkka: ["admiral", "kunkka"],
    Hero.Lina: ["slayer", "lina"],
    Hero.Lion: ["demon witch", "lion"],
    Hero.ShadowShaman: ["ss", "rhasta", "shaman", "shadow shaman"],
    Hero.Slardar: ["slardar"],
    Hero.Tidehunter: ["th", "leviathan", "tidehunter"],
    Hero.WitchDoctor: ["wd", "zharvakko", "witch doctor"],
    Hero.Lich: ["ethreain", "lich"],
    Hero.Riki: ["stealth assassin", "sa", "riki"],
    Hero.Enigma: ["nigma", "enigma"],
    Hero.Tinker: ["boush", "tinker"],
    Hero.Sniper: ["kardel", "sniper"],
    Hero.Necrophos: ["rotundjere", "necrolyte", "necrophos"],
    Hero.Warlock: ["wl", "demnok lannik", "warlock"],
    Hero.Beastmaster: ["bm", "beastmaster"],
    Hero.QueenOfPain: ["qop", "akasha", "queen of pain"],
    Hero.Venomancer: ["lesale", "venomancer"],
    Hero.FacelessVoid: ["fv", "faceless void"],
    Hero.WraithKing: ["sk", "snk", "wk", "skeleton", "one true king", "ostarion", "wraith king"],
    Hero.DeathProphet: ["dp", "krobelus", "death prophet"],
    Hero.PhantomAssassin: ["pa", "mortred", "phantom assassin"],
    Hero.Pugna: ["pugna"],
    Hero.TemplarAssassin: ["ta", "lanaya", "templar assassin"],
    Hero.Viper: ["netherdrake", "viper"],
    Hero.Luna: ["moon rider", "luna"],
    Hero.DragonKnight: ["dk", "davion", "dragon's blood", "dragon knight"],
    Hero.Dazzle: ["dazzle"],
    Hero.Clockwerk: ["rattletrap", "cw", "clock", "clockwerk"],
    Hero.Leshrac: ["ts", "leshrac"],
    Hero.NaturesProphet: ["np", "furion", "nature's prophet"],
    Hero.Lifestealer: ["ls", "naix", "lifestealer"],
    Hero.DarkSeer: ["ds", "ishkafel", "dark seer"],
    Hero.Clinkz: ["clinkz"],
    Hero.Omniknight: ["purist thunderwrath", "omniknight"],
    Hero.Enchantress: ["aiushtha", "ench", "bambi", "enchantress"],
    Hero.Huskar: ["huskar"],
    Hero.NightStalker: ["ns", "balanar", "night stalker"],
    Hero.Broodmother: ["arachnia", "brood", "spider", "broodmother"],
    Hero.BountyHunter: ["bh", "gondar", "bounty hunter"],
    Hero.Weaver: ["nw", "skitskurr", "weaver"],
    Hero.Jakiro: ["thd", "twin headed dragon", "jakiro"],
    Hero.Batrider: ["bat", "batrider"],
    Hero.Chen: ["holy knight", "chen"],
    Hero.Spectre: ["mercurial", "spectre"],
    Hero.AncientApparition: ["aa", "kaldr", "apparition", "ancient apparition"],
    Hero.Doom: ["doom"],
    Hero.Ursa: ["ulfsaar", "ursa"],
    Hero.SpiritBreaker: ["sb", "barathrum", "bara", "spirit breaker"],
    Hero.Gyrocopter: ["aurel", "gyro", "gyrocopter"],
    Hero.Alchemist: ["razzil", "alch", "alchemist"],
    Hero.Invoker: ["kid", "invo", "invoker"],
    Hero.Silencer: ["nortrom", "silencer"],
    Hero.OutworldDestroyer: ["od", "outworld destroyer"],
    Hero.Lycan: ["banehallow", "wolf", "lycan"],
    Hero.Brewmaster: ["brew", "mangix", "brewmaster"],
    Hero.ShadowDemon: ["sd", "shadow demon"],
    Hero.LoneDruid: ["ld", "bear", "sylla", "lone druid"],
    Hero.ChaosKnight: ["ck", "chaos", "chaos knight"],
    Hero.Meepo: ["geomancer", "meepwn", "meepo"],
    Hero.TreantProtector: ["tree", "treant protector"],
    Hero.OgreMagi: ["om", "ogre", "ogre magi"],
    Hero.Undying: ["dirge", "undying"],
    Hero.Rubick: ["rubick"],
    Hero.Disruptor: ["dis", "disruptor"],
    Hero.NyxAssassin: ["na", "nyx", "nyx assassin"],
    Hero.NagaSiren: ["naga", "slithice", "naga siren"],
    Hero.KeeperOfTheLight: ["keeper", "ezalor", "kotl", "keeper of the light"],
    Hero.Io: ["wisp", "io"],
    Hero.Visage: ["visage", "necrolic", "visage"],
    Hero.Slark: ["slark", "slark"],
    Hero.Medusa: ["medusa", "gorgon", "medusa"],
    Hero.TrollWarlord: ["troll", "jahrakal", "troll warlord"],
    Hero.CentaurWarrunner: ["centaur", "cent", "centaur warrunner"],
    Hero.Magnus: ["magnataur", "magnus", "mag", "magnus"],
    Hero.Timbersaw: ["rizzrack", "shredder", "timber", "timbersaw"],
    Hero.Bristleback: ["rigwarl", "bb", "bristle", "bristleback"],
    Hero.Tusk: ["ymir", "tusk"],
    Hero.SkywrathMage: ["sm", "dragonus", "sky", "skywrath mage"],
    Hero.Abaddon: ["abaddon", "aba", "abaddon"],
    Hero.ElderTitan: ["et", "elder titan"],
    Hero.LegionCommander: ["tresdin", "legion", "lc", "legion commander"],
    Hero.Techies: ["squee", "spleen", "spoon", "techies"],
    Hero.EmberSpirit: ["xin", "ember", "es", "ember spirit"],
    Hero.EarthSpirit: ["es", "kaolin", "earth", "earth spirit"],
    Hero.Underlord: ["pitlord", "azgalor", "ul", "underlord"],
    Hero.Terrorblade: ["tb", "terrorblade"],
    Hero.Phoenix: ["ph", "phoenix"],
    Hero.Oracle: ["ora", "nerif", "oracle"],
    Hero.WinterWyvern: ["ww", "auroth", "winter wyvern"],
    Hero.ArcWarden: ["zet", "aw", "arc", "zett", "arc warden"],
    Hero.MonkeyKing: ["mk", "sun wukong", "wukong", "monkey king"],
    Hero.DarkWillow: ["dw", "mireska", "oversight", "biggest oversight", "waifu", "dark willow"],
    Hero.Pangolier: ["ar", "pango", "pangolier"],
    Hero.Grimstroke: ["gs", "grim", "grimstroke"],
    Hero.Hoodwink: ["squirrel", "hw", "furry", "hoodwink"],
    Hero.VoidSpirit: ["void", "vs", "inai", "void spirit"],
    Hero.Snapfire: ["snap", "mortimer", "beatrix", "snapfire"],
    Hero.Mars: ["mars", "mars"],
    Hero.Ringmaster: ["rm", "marionetto", "cogliostro", "ringmaster"],
    Hero.Dawnbreaker: ["dawnbreaker", "valora", "mommy", "dawn", "dawnbreaker"],
    Hero.Marci: ["AYAYA", "marci"],
    Hero.PrimalBeast: ["pb", "primal beast"],
    Hero.Muerta: ["muerta"],
    Hero.Kez: ["kez"],
    Hero.Largo: ["largo"],
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
    6: ["olive", "grey"], # it was originally grey in WC3, but idk, it's easy to confuse with lightblue I feel like.
    7: ["lightblue"],
    8: ["darkgreen"],
    9: ["brown"],
}
