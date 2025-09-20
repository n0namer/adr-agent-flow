"""Adapter registry facade."""
from ext_registry import adapters


def register_adapter(kind: str, key: str, obj) -> None:
    adapters.register(f"{kind}:{key}", obj)


def get_adapter(kind: str, key: str):
    return adapters.get(f"{kind}:{key}")


def has_adapter(kind: str, key: str) -> bool:
    return adapters.has(f"{kind}:{key}")


# Import builtin adapters for registration side-effects.
from . import coverage  # noqa: F401  pylint: disable=unused-import
from . import e2e  # noqa: F401  pylint: disable=unused-import
from . import security  # noqa: F401  pylint: disable=unused-import
from . import logger  # noqa: F401  pylint: disable=unused-import
