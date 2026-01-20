TEST_MODULES: tuple[str, ...] = (
    "modules.dev.required",
    # 1. BETA
    "modules.beta",
    # 2. Testing components
    #
    # 2.1. DEV
    "modules.dev.control",
    "modules.dev.other",
    # "modules.dev.required",
    "modules.dev.webhook_logs",
    # 2.2. PERSONAL
    "modules.personal.alerts",
    "modules.personal.counters",
    "modules.personal.edit_information",
    "modules.personal.emotes_check",
    "modules.personal.keywords",
    "modules.personal.stable",
    "modules.personal.temporary",
    "modules.personal.timers",
    # 2.3. PUBLIC
    "modules.public.dota_rp_flow",
    "modules.public.meta",
)
USE_ALL_MODULES = True
