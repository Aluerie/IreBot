from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, override

from . import MISSING

if TYPE_CHECKING:
    import datetime


class plural:  # noqa: N801
    """Helper class to format tricky number + singular/plural noun situations.

    Returns a human-readable string combining number and a proper noun.
    `format_spec` in this case is supposed to list both singular/plural forms with a separator "|".
    See examples.

    Examples
    --------
        >>> format(plural(1), 'child|children')  # '1 child'
        >>> format(plural(8), 'week|weeks')  # '8 weeks'
        >>> f'{plural(3):reminder}' # 3 reminders

    Sources
    -------
    * Rapptz/RoboDanny (licensed MPL v2)
        https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/formats.py
    """

    def __init__(self, number: int) -> None:
        self.number: int = number

    @override
    def __format__(self, format_spec: str) -> str:
        number = self.number
        singular, _, plural = format_spec.partition("|")  # _ is `separator`
        plural = plural or f"{singular}s"
        if abs(number) != 1:
            return f"{number} {plural}"
        return f"{number} {singular}"


class TimeDeltaFormat(IntEnum):
    """An enum representing options for `fmt` argument in `timedelta_to_words` function."""

    Full = 1
    """1 minute 6 seconds"""
    Short = 2
    """1 min 30 sec"""
    Letter = 3
    """1m30s"""


def timedelta_to_words(
    timedelta: datetime.timedelta = MISSING,
    seconds: int = MISSING,
    *,
    accuracy: int = 2,
    fmt: TimeDeltaFormat = TimeDeltaFormat.Full,
) -> str:
    """Convert `datetime.timedelta` to a string of humanly readable words.

    Parameters
    ----------
    timedelta: datetime.timedelta = MISSING
        Time delta to convert to words (as datetime.timedelta type)
    seconds: int = MISSING
        Time delta to convert to words (as integer amount of seconds).
        Note that you should pass only one argument: either `delta` or `seconds`.
    accuracy: int = 2
        Amount of words to allow in the result. This is called accuracy because effectively,
        we are cutting down on how accurately the wording represents the time delta.
    fmt: TimeDeltaFormat = TimeDeltaFormat.Full
        A formatting choice for the output.
        The examples of each are given in `TimeDeltaFormat` class' doc-strings for each enum.

    Returns
    -------
    str
        Human-readable description for the time delta.

    Example:
    -------
    ```
    x = datetime.timedelta(seconds=66)
    timedelta_to_words(x)  # "1 minute 6 seconds"
    ```
    """
    if timedelta is not MISSING and seconds is not MISSING:
        msg = "Cannot mix `delta` and `seconds` keyword arguments."
        raise TypeError(msg)

    if timedelta:
        total_seconds = int(timedelta.total_seconds())
    elif seconds:
        total_seconds = seconds
    else:
        msg = "You need to provide at least one of the following arguments: `delta` and `seconds`."
        raise TypeError(msg)

    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    match fmt:
        case TimeDeltaFormat.Full:  # 1 minute 6 seconds
            time_units = {"day": days, "hour": hours, "minute": minutes, "second": seconds}
            output = [format(plural(number), word) for word, number in time_units.items() if number]
            return " ".join(output[:accuracy])
        case TimeDeltaFormat.Short:  # 1 min 30 sec
            time_units = {"day(-s)": days, "hr": hours, "min": minutes, "sec": seconds}
            output = [f"{number} {short}" for short, number in time_units.items() if number]
            return " ".join(output[:accuracy])
        case TimeDeltaFormat.Letter:  # 1m30s
            time_units = {"d": days, "h": hours, "m": minutes, "s": seconds}
            output = [f"{number:02d}{letter}" for letter, number in time_units.items() if number]
            return "".join(output[:accuracy]).removeprefix("0")  # remove leading zero if it managed to sneak in


def ordinal(n: int | str) -> str:
    """Convert an integer into its ordinal representation, i.e. 0->'0th', '3'->'3rd'.

    Dev Note
    --------
    Remember that there is always a funny lambda possibility
    `ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])`
    """
    n = int(n)
    suffix = "th" if 11 <= n % 100 <= 13 else ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


def magnitude(number: float) -> str:
    """_summary_.

    Parameters
    ----------
    number
        _description_

    Examples
    --------
    * 10_000 -> '10k'
    * 999999 -> '1m'
    * 1234 -> 1.1k
    """
    number = float(f"{number:.2g}")
    magnitude = 0
    while abs(number) >= 1000:
        magnitude += 1
        number /= 1000.0
    return f"{number:f}".rstrip("0").rstrip(".") + ["", "k", "m", "b", "t"][magnitude]
