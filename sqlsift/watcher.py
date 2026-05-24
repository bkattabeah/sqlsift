"""Schema watcher: periodically poll a loader callable and emit drift events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlsift.schema import Schema
from sqlsift.diff import compute_diff, SchemaDiff
from sqlsift.summary import summarize_diff


@dataclass
class WatchOptions:
    """Configuration for the schema watcher."""
    interval: float = 60.0          # seconds between polls
    max_iterations: Optional[int] = None  # None => run forever
    on_drift: Optional[Callable[[SchemaDiff], None]] = None
    on_no_change: Optional[Callable[[], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None


@dataclass
class WatchEvent:
    """Record of a single watcher iteration."""
    iteration: int
    had_drift: bool
    diff: SchemaDiff
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:  # pragma: no cover
        status = "DRIFT" if self.had_drift else "OK"
        return f"<WatchEvent iteration={self.iteration} status={status}>"


def _default_on_drift(diff: SchemaDiff) -> None:  # pragma: no cover
    summary = summarize_diff(diff)
    print(f"[sqlsift watcher] Drift detected: {summary}")


def _default_on_error(exc: Exception) -> None:  # pragma: no cover
    print(f"[sqlsift watcher] Error loading schema: {exc}")


def watch(
    loader: Callable[[], Schema],
    options: Optional[WatchOptions] = None,
) -> List[WatchEvent]:
    """Poll *loader* repeatedly and detect schema drift between successive snapshots.

    Returns the list of :class:`WatchEvent` objects collected during the run.
    Intended for use in long-running processes; set ``options.max_iterations``
    to limit execution in tests or one-shot scripts.

    If *loader* raises an exception during a poll, ``options.on_error`` is
    called (defaulting to a stderr print) and the iteration is skipped without
    updating the previous snapshot.
    """
    if options is None:
        options = WatchOptions()

    on_drift = options.on_drift or _default_on_drift
    on_no_change = options.on_no_change
    on_error = options.on_error or _default_on_error

    previous: Optional[Schema] = None
    events: List[WatchEvent] = []
    iteration = 0

    while True:
        try:
            current = loader()
        except Exception as exc:  # noqa: BLE001
            on_error(exc)
            iteration += 1
            if options.max_iterations is not None and iteration >= options.max_iterations:
                break
            time.sleep(options.interval)
            continue

        if previous is not None:
            diff = compute_diff(previous, current)
            had_drift = diff.has_changes()
            if had_drift:
                on_drift(diff)
            elif on_no_change is not None:
                on_no_change()
            events.append(WatchEvent(iteration=iteration, had_drift=had_drift, diff=diff))
        previous = current
        iteration += 1

        if options.max_iterations is not None and iteration >= options.max_iterations:
            break

        time.sleep(options.interval)

    return events
