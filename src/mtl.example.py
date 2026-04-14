"""Modules to load (mtl).

Yeah, I use `mtl.py` as a short name because I like to keep this file pinned,
so it takes less space this way in VSCode.
"""

categories: dict[str, list[str]] = {
    "dev": [
        "required",  # Remember, this is needed for other modules (Dota 2)
        # ---
        # "control",
        # "other",
        # "webhook_logs",
    ],
    "personal": [
        # "alerts",
        # "counters",
        # "edit_information",
        # "emotes_check",
        # "keywords",
        # "stable",
        "tags",
        # "temporary",
        # "timers",
    ],
    "public": [
        # "dota_rp_flow",
        # "meta"
    ],
}


MODULES_TO_LOAD: tuple[str, ...] = (
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

LOAD_ALL_MODULES: bool = False
