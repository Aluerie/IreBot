"""CUSTOM ERRORS.

All exceptions raised by me should be defined in this file.
It's just my small code practice.
"""

from __future__ import annotations

from typing import Any


class IreBotError(Exception):
    """The base exception for IreBot. All other exceptions should inherit from this."""

    __slots__: tuple[str, ...] = ()


class SilentError(IreBotError):
    """Errors to be ignored by the error handler."""

    __slots__: tuple[str, ...] = ()


class RespondWithError(IreBotError):
    """Error class for which Error Handler should just send the message into the context.

    Not an error per se (at least not always), but useful when we have a known exceptional situation
    that requires an early exit but still with a command response.
    """

    __slots__: tuple[str, ...] = ()


class PlaceholderError(IreBotError):
    """Placeholder Error.

    An error type I mostly use for the debugging purposes in places I'm not sure what to do about.
    Can attach some debug data into `.data` attribute for more debugging information.
    """

    __slots__: tuple[str, ...] = ()

    def __init__(self, message: str, **kwargs: Any) -> None:
        self.data: dict[str, Any] = kwargs
        super().__init__(message)


# UN-REVIEWED


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
