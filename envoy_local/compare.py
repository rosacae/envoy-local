"""Compare two .env files or profiles and report key-level differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.redactor import Redactor


@dataclass
class CompareEntry:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]

    @property
    def only_in_left(self) -> bool:
        return self.left_value is not None and self.right_value is None

    @property
    def only_in_right(self) -> bool:
        return self.left_value is None and self.right_value is not None

    @property
    def differs(self) -> bool:
        return (
            self.left_value is not None
            and self.right_value is not None
            and self.left_value != self.right_value
        )

    def to_dict(self, redactor: Optional[Redactor] = None) -> dict:
        def _v(val: Optional[str]) -> Optional[str]:
            if val is None:
                return None
            if redactor and redactor.is_secret(self.key):
                return redactor.redact(val)
            return val

        return {
            "key": self.key,
            "left": _v(self.left_value),
            "right": _v(self.right_value),
            "status": (
                "left_only" if self.only_in_left
                else "right_only" if self.only_in_right
                else "changed" if self.differs
                else "equal"
            ),
        }


@dataclass
class CompareResult:
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return any(e.only_in_left or e.only_in_right or e.differs for e in self.entries)

    def left_only(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.only_in_left]

    def right_only(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.only_in_right]

    def changed(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.differs]

    def equal(self) -> List[CompareEntry]:
        return [e for e in self.entries if not (e.only_in_left or e.only_in_right or e.differs)]

    def summary(self) -> Dict[str, int]:
        """Return a count summary of each difference category."""
        return {
            "left_only": len(self.left_only()),
            "right_only": len(self.right_only()),
            "changed": len(self.changed()),
            "equal": len(self.equal()),
            "total": len(self.entries),
        }


def compare_parse_results(left: ParseResult, right: ParseResult) -> CompareResult:
    from envoy_local.parser import as_dict

    left_dict: Dict[str, str] = as_dict(left)
    right_dict: Dict[str, str] = as_dict(right)
    all_keys = sorted(set(left_dict) | set(right_dict))
    entries = [
        CompareEntry(
            key=k,
            left_value=left_dict.get(k),
            right_value=right_dict.get(k),
        )
        for k in all_keys
    ]
    return CompareResult(entries=entries)


def compare_env_files(left_path: Path, right_path: Path) -> CompareResult:
    """Parse two .env files from disk and return their comparison result.

    Raises:
        FileNotFoundError: If either path does not exist.
    """
    if not left_path.exists():
        raise FileNotFoundError(f"Left file not found: {left_path}")
    if not right_path.exists():
        raise FileNotFoundError(f"Right file not found: {right_path}")
    left = parse_env_file(left_path)
    right = parse_env_file(right_path)
    return compare_parse_results(left, right)
