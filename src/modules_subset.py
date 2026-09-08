"""Modules to load when `bot.test_subset_mode` is `True`."""

MODULES_SUBSET: dict[str, list[str]] = {
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
        # "discord_notifications",
        # "emotes_common"
        # "emotes_7tv",
        # "information",
        # "keywords",
        # "stable",
        "tags",
        # "temporary",
        # "timers",
    ],
    "public": [
        # "d9kmmrbot",
        # "meta"
    ],
}


LOAD_ALL_MODULES: bool = False
