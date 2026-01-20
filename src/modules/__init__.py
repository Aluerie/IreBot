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
    "modules.beta",
    # currently disabled
    # "modules.public.dota",
)


def get_modules(*, test: bool) -> tuple[str, ...]:
    """Get list of bot modules to load.

    Returns
    -------
    tuple[str, ...]
        Tuple of modules for the bot to load.
        The modules are given in a full dot form.
        Example: `('modules.personal.alerts', 'modules.dev.control', 'modules.public.dota_rp_flow', )`
    """
    if test and not USE_ALL_MODULES:
        # assume testing specific modules from `_test.py`
        return TEST_MODULES

    # assume running full bot functionality (besides `DISABLED_MODULES`)
    current_folder = "src/" + str(__package__)
    modules: tuple[str, ...] = ()
    module_categories = [path for path in Path(current_folder).iterdir() if path.is_dir() and not path.name.startswith("_")]
    for module_category in module_categories:
        # Personal and Public modules
        modules += tuple(
            module.name
            for module in iter_modules([module_category.absolute()], prefix=f"{__package__}.{module_category.name}.")
            if module.name not in DISABLED_MODULES
        )

    log.debug("The list of modules (%s total) to load: %s", len(modules), modules)
    return modules
