from __future__ import annotations

import platform
from pkgutil import iter_modules

__all__ = ("EXTENSIONS",)

try:
    import _test  # noqa: PLC2701

    TEST_EXTENSIONS = _test.TEST_EXTENSIONS
    USE_ALL_EXTENSIONS = _test.TEST_USE_ALL_EXTENSIONS
except ModuleNotFoundError:
    TEST_EXTENSIONS: tuple[str, ...] = ()  # type: ignore[ConstantRedefinition]
    USE_ALL_EXTENSIONS: bool = True  # type: ignore[reportConstantRedefinition]

# EXTENSIONS

# write extensions (!) with "ext." prefix in the following tuples:
DISABLED_EXTENSIONS: tuple[str, ...] = (
    # extensions that should not be loaded
    "ext.beta",
    # currently disabled
    "ext.dota",
)


def get_extensions() -> tuple[str, ...]:
    if platform.system() == "Windows" and not USE_ALL_EXTENSIONS:
        # assume testing specific extensions from `_test.py`
        return tuple(f"{__package__}.{ext}" for ext in TEST_EXTENSIONS)

    # assume running full bot functionality (besides `DISABLED_EXTENSIONS`)
    return tuple(
        module.name for module in iter_modules(__path__, f"{__package__}.") if module.name not in DISABLED_EXTENSIONS
    )


EXTENSIONS = get_extensions()
