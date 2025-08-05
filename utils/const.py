from enum import StrEnum

# ruff: noqa: N815


class UserID(StrEnum):
    """Known/special user IDs."""

    Irene = "180499648"
    Bot = "1277023540"  # @IrenesBot
    # AuuBot = "1158666176"  # @AuuBot noqa: ERA001
    # AlueBot = "519438249"  # @AlueBot noqa: ERA001


class LowerName(StrEnum):
    """Known/special user names."""

    Irene = "irene_adler__"


class DisplayName(StrEnum):
    """Known/special user display names."""

    Irene = "Irene_Adler__"


class Global(StrEnum):
    """Global emotes that are usable everywhere."""

    # Twitch Native ones
    D4Head = "4Head"  # idk let's think better name?

    # BTTV
    monkaS = "monkaS"

    # FFZ
    # None - no good ones?..

    # STV
    EZ = "EZ"


class BTTV(StrEnum):
    """Some of BTTV emotes enabled on the channel."""

    DankG = "DankG"
    Offline = "Offline"
    peepoHey = "peepoHey"
    PogU = "PogU"
    Smoge = "Smoge"
    weirdChamp = "weirdChamp"


class FFZ(StrEnum):
    """Some of FFZ emotes enabled on the channel."""

    Weirdge = "Weirdge"
    monkaGIGA = "monkaGIGA"
    monkaGIGAGUN = "monkaGIGAGUN"
    monkaH = "monkaH"
    peepoPolice = "peepoPolice"
    peepoWTF = "peepoWTF"
    PepoG = "PepoG"
    sadKEK = "sadKEK"
    WTFF = "WTFF"


class STV(StrEnum):
    """Some of 7TV emotes enabled on the channel."""

    actually = "actually"
    Adge = "Adge"
    ALERT = "ALERT"
    ApuBritish = "ApuBritish"
    AYAYA = "AYAYA"
    buenoSuccess = "buenoSuccess"
    buenoFail = "buenoFail"
    Cinema = "Cinema"
    catFU = "catFU"
    classic = "classic"
    DankApprove = "DankApprove"
    dankFix = "dankFix"
    dankHey = "dankHey"
    DankL = "DankL"
    DankMods = "DankMods"
    DankDolmes = "DankDolmes"
    DANKHACKERMANS = "DANKHACKERMANS"
    DankLurk = "DankLurk"
    DankReading = "DankReading"
    DankThink = "DankThink"
    Deadge = "Deadge"
    Discord = "Discord"
    donkDetective = "donkDetective"
    donkHappy = "donkHappy"
    donkHey = "donkHey"
    donkJam = "donkJam"
    donkSad = "donkSad"
    Donki = "Donki"
    DonkPrime = "DonkPrime"
    ermtosis = "ermtosis"
    Erm = "Erm"
    EZdodge = "EZdodge"
    FeelsBingMan = "FeelsBingMan"
    FirstTimeChadder = "FirstTimeChadder"
    FirstTimeDentge = "FirstTimeDentge"
    FirstTimePlinker = "FirstTimePlinker"
    forsenCD = "forsenCD"
    gg = "gg"
    GroupScoots = "GroupScoots"
    hello = "hello"
    Hey = "Hey"
    heyinoticedyouhaveaprimegamingbadgenexttoyourname = "heyinoticedyouhaveaprimegamingbadgenexttoyourname"
    hi = "hi"
    How2Read = "How2Read"
    LastTimeChatter = "LastTimeChatter"
    peepoAds = "peepoAds"
    peepoDapper = "peepoDapper"
    please = "please"
    plink = "plink"
    PogChampPepe = "PogChampPepe"
    POGCRAZY = "POGCRAZY"
    POLICE = "POLICE"
    science = "science"
    Speedge = "Speedge"
    yo = "yo"
    uuh = "uuh"
    wickedchad = "wickedchad"
    widepeepoHappyRightHeart = "widepeepoHappyRightHeart"
    wow = "wow"
    UltraMad = "UltraMad"


class Bots(StrEnum):
    """List of known bot names.

    Used to identify other bots' messages.
    Variable name is supposed to be their display name while
    the value is lowercase name for easier comparing.

    I might enable these bots in the channel so let's keep them all here.
    """

    # the commented bots are currently not invited to irene's channel
    # commenting them for that extra nano-second performance gain when doing "chatter.name in const.Bots" check.

    # d9kmmrbot = "9kmmrbot"
    # dotabod = "dotabod"
    # Fossabot = "fossabot"
    IrenesBot = "irenesbot"
    # LolRankBot = "lolrankbot"
    # Moobot = "moobot"
    # Nightbot = "nightbot"
    # Sery_Bot = "sery_bot"
    # StreamLabs = "streamlabs"
    # Streamelements = "streamelements"
    Supibot = "supibot"
    WizeBot = "wizebot"


DIGITS = [
    "\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}",
]


class Logo(StrEnum):
    """Images for brands and logos."""

    Twitch = "https://cdn3.iconfinder.com/data/icons/social-messaging-ui-color-shapes-2-free/128/social-twitch-circle-512.png"
