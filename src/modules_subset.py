"""Modules to load when `bot.test_subset_mode` is `True`."""

CATEGORY_MODULES_MAPPING: dict[str, list[str]] = {
    "dev": [
        # "required",
        # ---
        # "control",
        "other",
        # "webhook_logs",
    ],
    "personal": [
        # "alerts",
        # "counters",
        # "discord_notifications",
        # "information",
        # "emotes"
        # "keywords",
        # "stable",
        # "tags",
        # "temporary",
        # "timers",
    ],
    "public": [
        # "d9kmmrbot",
        # "meta"
    ],
}


LOAD_ALL_MODULES: bool = False
