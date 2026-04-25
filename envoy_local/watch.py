"""File watcher that detects changes to .env files and triggers callbacks."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional


@dataclass
class WatchState:
    path: Path
    last_hash: Optional[str] = None
    last_mtime: float = 0.0


def _file_hash(path: Path) -> Optional[str]:
    """Return MD5 hex digest of file contents, or None if unreadable."""
    try:
        data = path.read_bytes()
        return hashlib.md5(data).hexdigest()
    except OSError:
        return None


def _file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


@dataclass
class WatchResult:
    path: Path
    changed: bool
    previous_hash: Optional[str]
    current_hash: Optional[str]

    @property
    def appeared(self) -> bool:
        return self.previous_hash is None and self.current_hash is not None

    @property
    def disappeared(self) -> bool:
        return self.previous_hash is not None and self.current_hash is None


class EnvWatcher:
    """Poll one or more .env files for changes."""

    def __init__(self, paths: list[Path], poll_interval: float = 1.0) -> None:
        self.poll_interval = poll_interval
        self._states: Dict[Path, WatchState] = {}
        for p in paths:
            self._states[p] = WatchState(path=p, last_hash=_file_hash(p), last_mtime=_file_mtime(p))

    def check(self) -> list[WatchResult]:
        """Check all watched paths and return results for those that changed."""
        results: list[WatchResult] = []
        for path, state in self._states.items():
            current_mtime = _file_mtime(path)
            if current_mtime == state.last_mtime and state.last_hash is not None:
                continue
            current_hash = _file_hash(path)
            if current_hash != state.last_hash:
                results.append(
                    WatchResult(
                        path=path,
                        changed=True,
                        previous_hash=state.last_hash,
                        current_hash=current_hash,
                    )
                )
                state.last_hash = current_hash
                state.last_mtime = current_mtime
        return results

    def watch(self, callback: Callable[[WatchResult], None], max_iterations: Optional[int] = None) -> None:
        """Block and call *callback* whenever a watched file changes."""
        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            for result in self.check():
                callback(result)
            time.sleep(self.poll_interval)
            iterations += 1
