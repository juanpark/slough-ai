"""memory 모듈 import 시 psycopg3가 eager-load 되지 않음을 검증.

Note: psycopg2 (used by SQLAlchemy/connection.py) may be loaded transitively
— that is expected and separate from the psycopg3 lazy-import concern.
"""

import sys

# psycopg3-specific module prefixes (excludes psycopg2)
_PSYCOPG3_PREFIXES = (
    "psycopg.",       # psycopg3 sub-modules
    "psycopg_pool",   # psycopg3 pool
    "psycopg_binary", # psycopg3 binary C extension
)


def _is_psycopg3_module(name: str) -> bool:
    """Return True if the module name belongs to psycopg3 (not psycopg2)."""
    if name == "psycopg":
        return True
    return name.startswith(_PSYCOPG3_PREFIXES)


def test_memory_import_does_not_load_psycopg3():
    """Importing the memory module should NOT trigger psycopg3/pool imports.

    The actual psycopg3 imports happen lazily inside get_checkpointer(),
    so merely importing the module must leave sys.modules clean of psycopg3.
    """
    # Remove psycopg3-related modules if they were loaded by other tests
    psycopg3_keys = [k for k in sys.modules if _is_psycopg3_module(k)]
    saved = {k: sys.modules.pop(k) for k in psycopg3_keys}

    try:
        # Re-import the module (forces re-evaluation if not cached)
        if "src.services.ai.memory" in sys.modules:
            del sys.modules["src.services.ai.memory"]

        from src.services.ai.memory import get_checkpointer  # noqa: F401

        # Verify psycopg3 was NOT loaded as a side effect
        loaded_psycopg3 = [
            k for k in sys.modules if _is_psycopg3_module(k)
        ]
        assert loaded_psycopg3 == [], (
            f"psycopg3 modules loaded at import time (should be lazy): {loaded_psycopg3}"
        )
    finally:
        # Restore previously loaded modules
        sys.modules.update(saved)
