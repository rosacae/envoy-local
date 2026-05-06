"""Helpers for integrating mask into other envoy-local workflows."""
from __future__ import annotations

from typing import Dict, List, Optional

from envoy_local.mask import MaskOptions, MaskResult, mask_entries
from envoy_local.parser import ParseResult
from envoy_local.redactor import RedactionConfig, Redactor


def auto_mask(
    result: ParseResult,
    extra_keys: Optional[List[str]] = None,
    config: Optional[RedactionConfig] = None,
    visible_chars: int = 4,
) -> MaskResult:
    """Mask all keys that the redactor considers secrets plus any *extra_keys*.

    This is the preferred high-level helper used by other CLI commands that
    want to display .env contents without leaking secrets.
    """
    cfg = config or RedactionConfig()
    redactor = Redactor(cfg)
    heuristic = [
        e.key for e in result.entries if e.key and redactor.is_secret(e.key)
    ]
    combined = list(set(heuristic + list(extra_keys or [])))
    opts = MaskOptions(visible_chars=visible_chars, only_secrets=True)
    return mask_entries(result, opts=opts, secret_keys=combined)


def masked_dict(
    result: ParseResult,
    extra_keys: Optional[List[str]] = None,
    config: Optional[RedactionConfig] = None,
) -> Dict[str, str]:
    """Return a plain dict with secrets masked — convenient for logging."""
    mr = auto_mask(result, extra_keys=extra_keys, config=config)
    return {
        e.key: (e.value or "")
        for e in mr.entries
        if e.key is not None
    }
