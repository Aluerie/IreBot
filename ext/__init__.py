from __future__ import annotations

import logging
from pathlib import Path
from pkgutil import iter_modules

__all__ = ("get_extensions",)

try:
    import _test

    TEST_EXTENSIONS = _test.TEST_EXTENSIONS
    USE_ALL_EXTENSIONS = _test.USE_ALL_EXTENSIONS
except ModuleNotFoundError:
    TEST_EXTENSIONS: tuple[str, ...] = ()  # type: ignore[ConstantRedefinition]
    USE_ALL_EXTENSIONS: bool = True  # type: ignore[reportConstantRedefinition]

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

DISABLED_EXTENSIONS: tuple[str, ...] = (
    # extensions that should not be loaded
    "ext.beta",
    # currently disabled
    # "ext.public.dota",
)


def get_extensions(*, test: bool) -> tuple[str, ...]:
    """Get list of bot extensions to load.

    Returns
    -------
    tuple[str, ...]
        Tuple of extensions for the bot to load.
        The extensions are given in a full dot form.
        Example: `('ext.personal.chatter', 'ext.personal.dev', 'ext.personal.other_commands', 'ext.personal.stream', )`
    """
    if test and not USE_ALL_EXTENSIONS:
        # assume testing specific extensions from `_test.py`
        return TEST_EXTENSIONS

    # assume running full bot functionality (besides `DISABLED_EXTENSIONS`)
    current_folder = str(__package__)
    extensions: tuple[str, ...] = ()
    ext_categories = [path for path in Path(current_folder).iterdir() if path.is_dir() and not path.name.startswith("_")]
    for ext_category in ext_categories:
        # Personal and Public extensions
        extensions += tuple(
            module.name
            for module in iter_modules([ext_category.absolute()], prefix=f"{__package__}.{ext_category.name}.")
            if module.name not in DISABLED_EXTENSIONS
        )

    log.debug("The list of extensions to load: %s", extensions)
    return extensions
