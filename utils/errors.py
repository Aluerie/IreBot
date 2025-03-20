"""CUSTOM ERRORS.

All exceptions raised by me should be defined in this file.
It's just my small code practice.
"""

from __future__ import annotations


class IreBotError(Exception):
    """The base exception for IreBot. All other exceptions should inherit from this."""

    __slots__: tuple[str, ...] = ()


class TranslateError(IreBotError):
    """Raised when there is an error in translate functionality."""

    def __init__(self, status_code: int, text: str) -> None:
        self.status_code: int = status_code
        self.text: str = text
        super().__init__(f"Google Translate responded with HTTP Status Code {status_code}")


class GuardError(IreBotError):
    """My own `commands.CheckFailure` Error.

    Used in my own command checks.
    """

    __slots__: tuple[str, ...] = ()


class BadArgumentError(IreBotError):
    """Bad Argument was provided for the command."""

    __slots__: tuple[str, ...] = ()


class UsageError(IreBotError):
    """Something wasn't properly used."""

    __slots__: tuple[str, ...] = ()


class SomethingWentWrong(IreBotError):  # noqa: N818
    """Something went wrong."""

    __slots__: tuple[str, ...] = ()


class PlaceholderRaiseError(IreBotError):
    """Placeholder Error.

    Maybe silly thing, but instead of doing empty `raise` that is not clear later in logs what exactly it is
    I prefer raising my own placeholder error with a message.
    This is usually used in a code where I'm unsure what to do and how else to handle the situation.
    """

    __slots__: tuple[str, ...] = ()


class GameNotFoundError(IreBotError):
    """Dota 2 Game Not Found."""

    __slots__: tuple[str, ...] = ()


class APIResponseError(IreBotError):
    """API Response Error."""

    __slots__: tuple[str, ...] = ()


class ResponseNotOK(IreBotError):  # noqa: N818
    """Raised when `aiohttp`'s session response is not OK.

    Sometimes we just specifically need to raise an error in those cases
    when response from `self.bot.session.get(url)` is not OK.
    I.e. Cache Updates.
    """

    __slots__: tuple[str, ...] = ()
