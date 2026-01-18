TEST_MODULES: tuple[str, ...] = (
    "ext.dev.required",
    # 1. BETA
    "ext.beta",
    # 2. Testing components
    #
    # 2.1. DEV
    "ext.dev.control",
    "ext.dev.other",
    # "ext.dev.required",
    "ext.dev.webhook_logs",
    # 2.2. PERSONAL
    "ext.personal.alerts",
    "ext.personal.counters",
    "ext.personal.edit_information",
    "ext.personal.emotes_check",
    "ext.personal.keywords",
    "ext.personal.stable",
    "ext.personal.temporary",
    "ext.personal.timers",
    # 2.3. PUBLIC
    "ext.public.dota_rp_flow",
    "ext.public.meta",
)
USE_ALL_MODULES = True
