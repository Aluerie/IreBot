"""Modules to load (MTL)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:

    class CategoriesDict(TypedDict):
        dev: list[str]
        personal: list[str]
        public: list[str]

    DictStrStr = dict[str, str]


__all__ = ("LOAD_ALL_MODULES", "MODULES_TO_LOAD")

CATEGORIES: CategoriesDict = {
    "dev": [
        # "required",
        # ---
        # "control",
        # "other",
        # "webhook_logs",
    ],
    "personal": [
        # "alerts",
        # "counters",
        # "edit_information",
        "emotes"
        # "keywords",
        # "stable",
        # "tags",
        # "temporary",
        # "timers",
    ],
    "public": [
        # "dota_rp_flow",
        # "meta"
    ],
}


def get_modules_to_load(categories: CategoriesDict) -> tuple[str, ...]:
    """Get modules to load from a friendly formatted categories dictionary.

    Returns
    -------
    tuple[str, ...]
        Tuple of modules to load. Modules are listed in dot-format, i.e. "modules.public.dota_rp_flow"
    """
    modules_to_load: tuple[str, ...] = (
        # Categorized modules
        *tuple(
            f"modules.{category}.{extension}"
            for category, extensions in cast("DictStrStr", categories).items()
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


MODULES_TO_LOAD = get_modules_to_load(CATEGORIES)
LOAD_ALL_MODULES: bool = False
