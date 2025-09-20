"""Gate registry helpers."""
from __future__ import annotations
from .base import Gate
from ext_registry import gates as _gates


def register_gate(cls: type[Gate]):
    _gates.register(cls.key, cls())
    return cls


def get_gate(key: str) -> Gate:
    return _gates.get(key)


def all_gates() -> list[str]:
    return _gates.keys()
