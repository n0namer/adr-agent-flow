"""Gate registry bootstrap."""
from .registry import register_gate, get_gate, all_gates  # noqa: F401

# Import builtin gates to ensure registration on module import.
from .builtin import gate_adr_trace  # noqa: F401
from .builtin import gate_log_vs_adr  # noqa: F401
from .builtin import gate_dod_gate  # noqa: F401
