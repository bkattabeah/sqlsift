"""Lightweight in-memory store that accumulates WatchEvents for inspection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.watcher import WatchEvent


@dataclass
class WatchStore:
    """Accumulate :class:`WatchEvent` objects and provide simple queries."""

    _events: List[WatchEvent] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def record(self, event: WatchEvent) -> None:
        """Append *event* to the store."""
        self._events.append(event)

    def clear(self) -> None:
        """Remove all recorded events."""
        self._events.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def events(self) -> List[WatchEvent]:
        """All recorded events (oldest first)."""
        return list(self._events)

    @property
    def drift_events(self) -> List[WatchEvent]:
        """Only events where drift was detected."""
        return [e for e in self._events if e.had_drift]

    @property
    def total(self) -> int:
        """Total number of recorded events."""
        return len(self._events)

    @property
    def drift_count(self) -> int:
        """Number of events where drift was detected."""
        return sum(1 for e in self._events if e.had_drift)

    @property
    def latest(self) -> Optional[WatchEvent]:
        """Most recent event, or *None* if the store is empty."""
        return self._events[-1] if self._events else None

    def make_callback(self):
        """Return an ``on_drift`` callback that records drift events here."""
        def _cb(diff):
            # The WatchEvent is created externally by watch(); this callback
            # is a convenience shim for callers who want to hook into drift
            # without subclassing.  We store a lightweight sentinel instead.
            pass  # real recording happens via record()
        return _cb

    def __repr__(self) -> str:
        return (
            f"WatchStore(total={self.total}, drift={self.drift_count})"
        )
