"""Registry helpers for adapters, gates and LLM judges with plugin discovery."""
from __future__ import annotations
import importlib
import pkgutil
import os
import sys
from typing import Any, Dict, Iterable


class Registry:
    """Simple case-insensitive registry with last-wins semantics."""

    def __init__(self, name: str):
        self.name = name
        self._items: Dict[str, Any] = {}

    def register(self, key: str, obj: Any) -> None:
        k = key.lower()
        self._items[k] = obj

    def get(self, key: str) -> Any:
        return self._items[key.lower()]

    def has(self, key: str) -> bool:
        return key.lower() in self._items

    def keys(self) -> list[str]:
        return list(self._items.keys())


adapters = Registry("adapters")
gates = Registry("gates")
judges = Registry("judges")


def _iter_modules(folder: str) -> Iterable[str]:
    prefix = folder.rstrip("/").replace("/", ".") + "."
    for module in pkgutil.walk_packages([folder], prefix=prefix):
        yield module.name


def load_local_plugins(sources: Iterable[str]) -> None:
    cwd = os.getcwd()
    for source in sources:
        if not source.startswith("local:"):
            continue
        folder = source.split(":", 1)[1]
        if not os.path.isdir(folder):
            continue
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        for module_name in _iter_modules(folder):
            importlib.import_module(module_name)


def load_entrypoint_plugins(group: str) -> None:
    try:
        from importlib import metadata as importlib_metadata
    except ImportError:  # pragma: no cover
        import importlib_metadata  # type: ignore
    entries = importlib_metadata.entry_points()
    selected = entries.get(group, []) if hasattr(entries, "get") else [ep for ep in entries if ep.group == group]
    for entry_point in selected:
        entry_point.load()


def discover_plugins(cfg: Dict[str, Any]) -> None:
    plugins_cfg = cfg.get("plugins", {}) or {}
    sources = plugins_cfg.get("discovery", [])
    if not sources:
        return
    local_sources = [s for s in sources if s.startswith("local:")]
    if local_sources:
        load_local_plugins(local_sources)
    for source in sources:
        if source.startswith("entrypoint:"):
            load_entrypoint_plugins(source.split(":", 1)[1])
