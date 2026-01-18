from __future__ import annotations

import logging
from pathlib import Path
from pkgutil import iter_modules

__all__ = ("get_modules",)

try:
    import _test

    TEST_MODULES = _test.TEST_MODULES
    USE_ALL_MODULES = _test.USE_ALL_MODULES
except ModuleNotFoundError:
    TEST_MODULES: tuple[str, ...] = ()  # type: ignore[ConstantRedefinition]
    USE_ALL_MODULES: bool = True  # type: ignore[reportConstantRedefinition]

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DISABLED_MODULES: tuple[str, ...] = (
    # modules that should not be loaded
    "ext.beta",
    # currently disabled
    # "ext.public.dota",
)


def get_modules(*, test: bool) -> tuple[str, ...]:
    """Get list of bot modules to load.

    Returns
    -------
    tuple[str, ...]
        Tuple of extensions for the bot to load.
        The extensions are given in a full dot form.
        Example: `('ext.personal.chatter', 'ext.personal.dev', 'ext.personal.other_commands', 'ext.personal.stream', )`
    """
    if test and not USE_ALL_MODULES:
        # assume testing specific extensions from `_test.py`
        return TEST_MODULES

    # assume running full bot functionality (besides `DISABLED_EXTENSIONS`)
    current_folder = str(__package__)
    modules: tuple[str, ...] = ()
    ext_categories = [path for path in Path(current_folder).iterdir() if path.is_dir() and not path.name.startswith("_")]
    for ext_category in ext_categories:
        # Personal and Public extensions
        modules += tuple(
            module.name
            for module in iter_modules([ext_category.absolute()], prefix=f"{__package__}.{ext_category.name}.")
            if module.name not in DISABLED_MODULES
        )

    log.debug("The list of extensions (%s total) to load: %s", len(modules), modules)
    return modules
