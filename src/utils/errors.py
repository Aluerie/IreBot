"""CUSTOM ERRORS.

All exceptions raised by me should be defined in this file.
It's just my small code practice.
"""

from __future__ import annotations

from typing import Any


class IreBotError(Exception):
    """The base exception for IreBot. All other exceptions should inherit from this."""


class SilentError(IreBotError):
    """Errors to be ignored by the error handler."""


class RespondWithError(IreBotError):
    """Error class for which Error Handler should just send the message into the context.

    Not an error per se (at least not always), but useful when we have a known exceptional situation
    that requires an early exit but still with a command response.
    """


class BadUserInputError(RespondWithError):
    """Error indicating there was a problem with user input."""


class PlaceholderError(IreBotError):
    """Placeholder Error for "Something went wrong" moments.

    An error type I mostly use for the debugging purposes in places I'm not sure what to do about.
    Can attach some debug data into `.data` attribute for more debugging information.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        self.data: dict[str, Any] = kwargs
        super().__init__(message)


class APIDataError(IreBotError):
    """API Data Error.

    This error is raised when 3rd party API returns a response indicating
    that there was some error.

    Useful for API like GraphQL which like to put an error message into its data responses, i.e.
    `{data: {"error": "There was an error"}}`.

    Attributes
    ----------
    data: Any
        Any data that API attached to the response.
    """

    def __init__(self, message: str, data: Any) -> None:
        self.data: Any = data
        super().__init__(message)


class ResponseNotOK(IreBotError):  # noqa: N818
    """Raised when `aiohttp`'s session response is not OK.

    Sometimes we just specifically need to raise an error in those cases
    when response from `self.bot.session.get(url)` is not OK.
    I.e. Cache Updates.
    """
