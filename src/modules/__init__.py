from __future__ import annotations

import logging
from pathlib import Path
from pkgutil import iter_modules

__all__ = ("get_modules",)

try:
    import subset as select_modules_to_load

    TEST_CATEGORY_MODULES_MAPPING: dict[str, list[str]] = select_modules_to_load.CATEGORY_MODULES_MAPPING
    LOAD_ALL_MODULES = select_modules_to_load.LOAD_ALL_MODULES
except ModuleNotFoundError:
    TEST_CATEGORY_MODULES_MAPPING: dict[str, list[str]] = {}  # type: ignore[ConstantRedefinition]
    LOAD_ALL_MODULES: bool = True  # type: ignore[reportConstantRedefinition]

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DISABLED_MODULES: tuple[str, ...] = (
    # modules that should not be loaded
    "modules.beta",
    # currently disabled
    # "modules.public.dota",
)


def get_test_subset_modules(categories: dict[str, list[str]]) -> tuple[str, ...]:
    """Get a tuple of modules to load from a friendly formatted categories dictionary.

    Returns
    -------
    tuple[str, ...]
        Tuple of modules to load. Modules are listed in dot-format, i.e. "modules.public.dota_rp_flow"
    """
    modules_to_load: tuple[str, ...] = (
        # Categorized modules
        *tuple(
            f"modules.{category}.{extension}"
            for category, extensions in categories.items()
            for extension in extensions
            if extensions
        ),
        # Extras
        "modules.beta",
    )
    # Component-based dependencies
    if "modules.public.dota_rp_flow" in modules_to_load:
        modules_to_load += ("modules.dev.required",)
    return modules_to_load


def get_modules(*, test: bool) -> tuple[str, ...]:
    """Get list of bot modules to load.

    Returns
    -------
    tuple[str, ...]
        Tuple of modules for the bot to load.
        The modules are given in a full dot form.
        Example: `('modules.personal.alerts', 'modules.dev.control', 'modules.public.dota_rp_flow', )`
    """
    if test and not LOAD_ALL_MODULES:
        # assume testing specific modules from `m.py`
        return get_test_subset_modules(TEST_CATEGORY_MODULES_MAPPING)

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
