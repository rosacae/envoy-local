"""Group env keys by prefix or custom mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class GroupResult:
    groups: Dict[str, List[EnvEntry]] = field(default_factory=dict)
    ungrouped: List[EnvEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "groups": {
                k: [{"key": e.key, "value": e.value} for e in v]
                for k, v in self.groups.items()
            },
            "ungrouped": [{"key": e.key, "value": e.value} for e in self.ungrouped],
        }


def group_by_prefix(
    result: ParseResult,
    separator: str = "_",
    prefixes: Optional[List[str]] = None,
) -> GroupResult:
    """Group entries by key prefix (e.g. DB_, AWS_, APP_).

    If *prefixes* is given only those prefixes are used as group names;
    otherwise every distinct first token before *separator* becomes a group.
    Keys without a separator land in *ungrouped*.
    """
    groups: Dict[str, List[EnvEntry]] = {}
    ungrouped: List[EnvEntry] = []

    for entry in result.entries:
        if entry.key is None:
            ungrouped.append(entry)
            continue

        if separator in entry.key:
            prefix = entry.key.split(separator, 1)[0]
            if prefixes is None or prefix in prefixes:
                groups.setdefault(prefix, []).append(entry)
                continue

        ungrouped.append(entry)

    return GroupResult(groups=groups, ungrouped=ungrouped)


def group_by_mapping(
    result: ParseResult,
    mapping: Dict[str, List[str]],
) -> GroupResult:
    """Group entries by explicit key-to-group mapping.

    *mapping* is ``{group_name: [key1, key2, ...]}``.  Keys not listed in any
    group end up in *ungrouped*.
    """
    key_to_group: Dict[str, str] = {}
    for group_name, keys in mapping.items():
        for k in keys:
            key_to_group[k] = group_name

    groups: Dict[str, List[EnvEntry]] = {}
    ungrouped: List[EnvEntry] = []

    for entry in result.entries:
        if entry.key and entry.key in key_to_group:
            g = key_to_group[entry.key]
            groups.setdefault(g, []).append(entry)
        else:
            ungrouped.append(entry)

    return GroupResult(groups=groups, ungrouped=ungrouped)
