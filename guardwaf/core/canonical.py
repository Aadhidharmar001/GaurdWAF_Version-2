"""
Canonical Parameter Serialization and SHA-256 Digest Module.
Guarantees deterministic, reproducible parameter hashing across platforms and runtime instances.
"""

import hashlib
import json
from typing import Any, Dict


def canonicalize_parameters(params: Dict[str, Any]) -> str:
    """
    Converts a Python dictionary of parameters into a deterministic, canonical JSON string representation.
    Keys are sorted recursively, and formatting is kept compact (no extra whitespace).
    """

    def _normalize(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: _normalize(v) for k, v in sorted(val.items())}
        elif isinstance(val, (list, tuple)):
            return [_normalize(v) for v in val]
        return val

    normalized = _normalize(params or {})
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def compute_parameter_digest(params: Dict[str, Any]) -> str:
    """
    Computes the SHA-256 hex digest of the canonical parameter string representation.
    """
    canonical_str = canonicalize_parameters(params)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
