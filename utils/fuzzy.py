"""Fuzzy wuzzy string matching utilities.

Sources
-------
*  `fuzzy.py` file from RoboDanny (license MPL v2 from Rapptz/RoboDanny)
    https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/fuzzy.py
* Helpful article:
    http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

Notes
-----
* Unfortunately, Danny didn't make doc-strings for the functions in here so I mostly cross-checked with
    https://github.com/seatgeek/thefuzz concepts and ideas, which are kinda the same
    (but in my testing that library is slower than the code here, not sure why).
"""

from __future__ import annotations

import heapq
import operator
import re
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Literal, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Sequence

T = TypeVar("T")

__all__ = (
    "extract",  # exact matches
    "extract_one",  # exact best match
    "extract_or_exact",  # exact match if present or matches
    "extract_top_matches",  # matches with only top score
    "find_one",  # regex, only one match
    "finder",  # regex
)


def ratio(a: str, b: str) -> int:
    """Return a measure of the sequences' similarity as an integer in the range [0, 100]."""
    m = SequenceMatcher(None, a, b)
    return round(100 * m.ratio())


def quick_ratio(a: str, b: str) -> int:
    """Return an upper bound on `ratio()` relatively quickly."""
    m = SequenceMatcher(None, a, b)
    return round(100 * m.quick_ratio())


def partial_ratio(a: str, b: str) -> int:
    """Return the ratio of the most similar substring as a number between 0 and 100."""
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    m = SequenceMatcher(None, short, long)

    blocks = m.get_matching_blocks()

    scores: list[float] = []
    for i, j, _ in blocks:
        start = max(j - i, 0)
        end = start + len(short)
        o = SequenceMatcher(None, short, long[start:end])
        r = o.ratio()

        if 100 * r > 99:
            return 100
        scores.append(r)

    return round(100 * max(scores))


_word_regex = re.compile(r"\W", re.IGNORECASE)


def _sort_tokens(a: str) -> str:
    a = _word_regex.sub(" ", a).lower().strip()
    return " ".join(sorted(a.split()))


def token_sort_ratio(a: str, b: str) -> int:
    """Return a measure of the sequences' similarity between 0 and 100 but sorting the token before comparing."""
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return ratio(a, b)


def quick_token_sort_ratio(a: str, b: str) -> int:
    """Return a measure of the sequences' similarity between 0 and 100 but sorting the token before comparing.

    And using `quick_ratio` instead.
    """
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return quick_ratio(a, b)


def partial_token_sort_ratio(a: str, b: str) -> int:
    """Return the ratio of the most similar substring as a number between 0 and 100.

    But sorting the token before comparing.
    """
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return partial_ratio(a, b)


@overload
def _extraction_generator(
    query: str,
    choices: Sequence[str],
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> Generator[tuple[str, int], None, None]: ...


@overload
def _extraction_generator[T](
    query: str,
    choices: dict[str, T],
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> Generator[tuple[str, int, T], None, None]: ...


def _extraction_generator[T](
    query: str,
    choices: Sequence[str] | dict[str, T],
    scorer: Callable[[str, str], int] = quick_ratio,
    score_cutoff: int = 0,
) -> Generator[tuple[str, int, T] | tuple[str, int], None, None]:
    if isinstance(choices, dict):
        for key, value in choices.items():
            score = scorer(query, key)
            if score >= score_cutoff:
                yield (key, score, value)
    else:
        for choice in choices:
            score = scorer(query, choice)
            if score >= score_cutoff:
                yield (choice, score)


@overload
def extract(
    query: str,
    choices: Sequence[str],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
    limit: int | None = ...,
) -> list[tuple[str, int]]: ...


@overload
def extract[T](
    query: str,
    choices: dict[str, T],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
    limit: int | None = ...,
) -> list[tuple[str, int, T]]: ...


def extract[T](
    query: str,
    choices: Sequence[str] | dict[str, T],
    *,
    scorer: Callable[[str, str], int] = quick_ratio,
    score_cutoff: int = 0,
    limit: int | None = 10,
) -> list[tuple[str, int]] | list[tuple[str, int, T]]:
    """Select the best match in a list or dictionary of choices.

    Find best matches in a list or dictionary of choices, return a
    list of tuples containing the match and its score. If a dictionary
    is used, also returns the key for each match.
    """
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    if limit is not None:
        return heapq.nlargest(limit, it, key=operator.itemgetter(1))  # type: ignore[reportReturnType]
    return sorted(it, key=operator.itemgetter(1), reverse=True)  # type: ignore[reportReturnType]


@overload
def extract_one(
    query: str,
    choices: Sequence[str],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> tuple[str, int] | None: ...


@overload
def extract_one[T](
    query: str,
    choices: dict[str, T],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> tuple[str, int, T] | None: ...


def extract_one[T](
    query: str,
    choices: dict[str, T] | Sequence[str],
    *,
    scorer: Callable[[str, str], int] = quick_ratio,
    score_cutoff: int = 0,
) -> tuple[str, int] | tuple[str, int, T] | None:
    """Find the single best match above a score in a list of choices.

    This is a convenience method which returns the single best choice.
    See extract() for the full arguments list.
    """
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    try:
        return max(it, key=operator.itemgetter(1))
    except:  # noqa: E722
        # iterator could return nothing
        return None


@overload
def extract_or_exact(
    query: str,
    choices: Sequence[str],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
    limit: int | None = ...,
) -> list[tuple[str, int]]: ...


@overload
def extract_or_exact[T](
    query: str,
    choices: dict[str, T],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
    limit: int | None = ...,
) -> list[tuple[str, int, T]]: ...


def extract_or_exact[T](
    query: str,
    choices: dict[str, T] | Sequence[str],
    *,
    scorer: Callable[[str, str], int] = quick_ratio,
    score_cutoff: int = 0,
    limit: int | None = None,
) -> list[tuple[str, int]] | list[tuple[str, int, T]]:
    """Extract: Select the best match in a list or dictionary of choices.

    Find best matches in a list or dictionary of choices, return a
    list of tuples containing the match and its score. If a dictionary
    is used, also returns the key for each match.

    However, if "exact" match is present (the top one is exact or more than 30% more correct than the top)
    then return that instead of "extract" results.
    """
    matches = extract(query, choices, scorer=scorer, score_cutoff=score_cutoff, limit=limit)
    if len(matches) == 0:
        return []

    if len(matches) == 1:
        return matches

    top = matches[0][1]
    second = matches[1][1]

    # check if the top one is exact or more than 30% more correct than the top
    if top == 100 or top > (second + 30):
        return [matches[0]]  # pyright: ignore[reportReturnType]

    return matches


@overload
def extract_top_matches(
    query: str,
    choices: Sequence[str],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> list[tuple[str, int]]: ...


@overload
def extract_top_matches[T](
    query: str,
    choices: dict[str, T],
    *,
    scorer: Callable[[str, str], int] = ...,
    score_cutoff: int = ...,
) -> list[tuple[str, int, T]]: ...


def extract_top_matches[T](
    query: str,
    choices: dict[str, T] | Sequence[str],
    *,
    scorer: Callable[[str, str], int] = quick_ratio,
    score_cutoff: int = 0,
) -> list[tuple[str, int]] | list[tuple[str, int, T]]:
    """Find matches with the highest score in a list of choices.

    This is a convenience method which only returns top matches.
    See extract() for the full arguments list.
    """
    matches = extract(query, choices, scorer=scorer, score_cutoff=score_cutoff, limit=None)
    if len(matches) == 0:
        return []

    top_score = matches[0][1]
    to_return = []
    index = 0
    while True:
        try:
            match = matches[index]
        except IndexError:
            break
        else:
            index += 1

        if match[1] != top_score:
            break

        to_return.append(match)
    return to_return


@overload
def finder(
    text: str,
    collection: Iterable[T],
    *,
    key: Callable[[T], str] | None = ...,
    raw: Literal[True],
) -> list[tuple[int, int, T]]: ...


@overload
def finder(
    text: str,
    collection: Iterable[T],
    *,
    key: Callable[[T], str] | None = ...,
    raw: Literal[False],
) -> list[T]: ...


@overload
def finder(
    text: str,
    collection: Iterable[T],
    *,
    key: Callable[[T], str] | None = ...,
    raw: bool = ...,
) -> list[T]: ...


def finder(
    text: str,
    collection: Iterable[T],
    *,
    key: Callable[[T], str] | None = None,
    raw: bool = False,
) -> list[tuple[int, int, T]] | list[T]:
    """Find best matches using regex."""
    suggestions: list[tuple[int, int, T]] = []
    text = str(text)
    pat = ".*?".join(map(re.escape, text))
    regex = re.compile(pat, flags=re.IGNORECASE)
    for item in collection:
        to_search = key(item) if key else str(item)
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup: tuple[int, int, T]) -> tuple[int, int, str | T]:
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    if raw:
        return sorted(suggestions, key=sort_key)
    return [z for _, _, z in sorted(suggestions, key=sort_key)]


def find_one(text: str, collection: Iterable[str], *, key: Callable[[str], str] | None = None) -> str | None:
    """Find one single best match using regex."""
    try:
        return finder(text, collection, key=key)[0]
    except IndexError:
        return None
