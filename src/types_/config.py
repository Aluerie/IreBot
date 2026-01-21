from typing import TypedDict

__all__ = ("Config",)


class Twitch(TypedDict):
    CLIENT_ID: str
    CLIENT_SECRET: str


class Postgres(TypedDict):
    VPS: str
    HOME: str


class SteamAccount(TypedDict):
    USERNAME: str
    PASSWORD: str


class Steam(TypedDict):
    IRENE_ID32: int
    IRENE_ID64: int
    IRENESTEST: SteamAccount
    IRENESBOT: SteamAccount


class Tokens(TypedDict):
    STRATZ_BEARER: str
    STEAM: str
    SPOTIFY_AIDENWALLIS: str
    EVENTSUB: str


class Webhooks(TypedDict):
    ERROR: str
    LOGGER: str


class Config(TypedDict):
    """Type-hints for dictionary created from loading `config.toml` file."""

    POSTGRES: Postgres
    STEAM: Steam
    TWITCH: Twitch
    WEBHOOKS: Webhooks
    TOKENS: Tokens
