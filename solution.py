## Student Name: Rajendra Brahmbhatt
## Student ID: 217925157

"""
Appointment Schedule Recommender

Recommends appointment time slots within a user-defined working-hours window,
ensuring they do not clash with user-given busy intervals.

Features:
  - Accepts working hours (start/end) in 24-hour format
  - Accepts a list of busy intervals in 24-hour format
  - Accepts a meeting duration (minutes)
  - Accepts an optional buffer time applied after every meeting and busy interval
  - Accepts an optional candidate time window to further restrict recommendations
  - Returns up to N chronologically sorted, non-overlapping available slots
  - Each returned slot duration = meeting_duration + buffer_time

Assumptions:
  - All times are for a single day (no overnight wrapping)
  - Times are in 24-hour format (hours and minutes only)
  - Buffer time is uniform across all meetings
  - Meeting duration is the same for all meetings
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, order=True)
class TimeSlot:
    """
    A time-of-day represented as (hour, minute) in 24-hour format.
    Natural ordering is chronological due to field declaration order.
    """
    hour: int
    minute: int

    def to_minutes(self) -> int:
        """Convert to total minutes since midnight."""
        return self.hour * 60 + self.minute

    @classmethod
    def from_minutes(cls, total: int) -> "TimeSlot":
        """Create a TimeSlot from total minutes since midnight."""
        return cls(hour=total // 60, minute=total % 60)

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def __repr__(self) -> str:
        return f"TimeSlot({self.hour}, {self.minute})"


@dataclass(frozen=True)
class Interval:
    """
    A half-open time interval [start, end) on a single day.
    Used for busy blocks, candidate windows, and returned meeting slots.
    """
    start: TimeSlot
    end: TimeSlot

    def to_minutes(self) -> Tuple[int, int]:
        """Return (start_minutes, end_minutes) since midnight."""
        return self.start.to_minutes(), self.end.to_minutes()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __repr__(self) -> str:
        return f"({self.start}, {self.end})"


# ── Validation ────────────────────────────────────────────────────────────────

def _validate_inputs(
    work_start: TimeSlot,
    work_end: TimeSlot,
    meeting_duration: int,
    buffer_time: int,
    n: int,
    busy_intervals: List[Interval],
    candidate_windows: Optional[List[Interval]],
) -> None:
    """
    Validate all scheduler inputs and raise ValueError for any violation.

    Raises:
        ValueError: if any of the following hold:
            - work_start >= work_end
            - meeting_duration <= 0
            - buffer_time < 0
            - n <= 0
            - any busy interval has start >= end
            - any candidate window has start >= end
    """
    if work_start.to_minutes() >= work_end.to_minutes():
        raise ValueError(
            "Working-hours start time must be strictly before end time."
        )
    if meeting_duration <= 0:
        raise ValueError(
            "Meeting duration must be greater than 0 minutes."
        )
    if buffer_time < 0:
        raise ValueError(
            "Buffer time must be non-negative."
        )
    if n <= 0:
        raise ValueError(
            "Number of requested slots (N) must be greater than 0."
        )
    for iv in busy_intervals:
        s, e = iv.to_minutes()
        if s >= e:
            raise ValueError(
                f"Busy interval start must be before end: {iv}"
            )
    if candidate_windows:
        for cw in candidate_windows:
            s, e = cw.to_minutes()
            if s >= e:
                raise ValueError(
                    f"Candidate window start must be before end: {cw}"
                )


# ── Helper Functions ──────────────────────────────────────────────────────────

def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Sort and merge overlapping or adjacent (start, end) minute intervals.

    Args:
        intervals: list of (start_min, end_min) tuples.

    Returns:
        Sorted list of non-overlapping merged intervals.
    """
    if not intervals:
        return []
    sorted_ivs = sorted(intervals)
    merged: List[Tuple[int, int]] = [sorted_ivs[0]]
    for s, e in sorted_ivs[1:]:
        prev_s, prev_e = merged[-1]
        if s <= prev_e:                       # overlapping or adjacent
            merged[-1] = (prev_s, max(prev_e, e))
        else:
            merged.append((s, e))
    return merged


def _clip_busy_to_working_hours(
    busy_mins: List[Tuple[int, int]],
    work_start_min: int,
    work_end_min: int,
) -> List[Tuple[int, int]]:
    """
    Clip busy intervals to working hours, discarding any portions that
    fall fully or partially outside the working window.

    Intervals that partially overlap are trimmed to the overlapping
    portion.  Intervals entirely outside are dropped.

    Args:
        busy_mins:      list of (start, end) busy intervals in minutes.
        work_start_min: working-day start in minutes since midnight.
        work_end_min:   working-day end in minutes since midnight.

    Returns:
        Clipped and merged busy intervals within working hours.
    """
    clipped: List[Tuple[int, int]] = []
    for s, e in busy_mins:
        cs = max(s, work_start_min)
        ce = min(e, work_end_min)
        if cs < ce:
            clipped.append((cs, ce))
    return _merge_intervals(clipped)


def _compute_free_gaps(
    work_start_min: int,
    work_end_min: int,
    busy_mins: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    """
    Compute free (available) gaps within [work_start_min, work_end_min)
    after removing all busy intervals.

    The busy intervals are first clipped to working hours and merged.

    Args:
        work_start_min: working-day start in minutes since midnight.
        work_end_min:   working-day end in minutes since midnight.
        busy_mins:      busy intervals in minutes (need not be sorted).

    Returns:
        List of (gap_start, gap_end) tuples representing available time,
        sorted chronologically.
    """
    clipped = _clip_busy_to_working_hours(busy_mins, work_start_min, work_end_min)

    gaps: List[Tuple[int, int]] = []
    cursor = work_start_min
    for s, e in clipped:
        if cursor < s:
            gaps.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < work_end_min:
        gaps.append((cursor, work_end_min))
    return gaps


def _intersect_with_candidates(
    gaps: List[Tuple[int, int]],
    candidate_windows: List[Interval],
) -> List[Tuple[int, int]]:
    """
    Narrow free gaps so that only portions falling inside at least one
    candidate window are kept.

    Args:
        gaps:              free-gap intervals in minutes.
        candidate_windows: user-supplied candidate Interval objects.

    Returns:
        Merged list of (start, end) minute intervals that lie in both a
        free gap and a candidate window.
    """
    cand_mins = sorted([c.to_minutes() for c in candidate_windows])
    cand_mins = _merge_intervals(cand_mins)

    intersected: List[Tuple[int, int]] = []
    for gs, ge in gaps:
        for cs, ce in cand_mins:
            lo = max(gs, cs)
            hi = min(ge, ce)
            if lo < hi:
                intersected.append((lo, hi))
    return _merge_intervals(intersected)


def _fill_slots(
    gaps: List[Tuple[int, int]],
    slot_block: int,
    n: int,
) -> List[Interval]:
    """
    Greedily place as many non-overlapping slots of size *slot_block*
    minutes as possible (up to *n*) inside the given gaps.

    Slots are placed chronologically from the earliest gap forward
    (tie-breaking rule #1 and #2).  No attempt is made to spread
    meetings across the day (tie-breaking rule #3).

    If no gap is large enough to hold a full slot, the system returns
    only gaps that can accommodate the meeting (per the invariant that
    returned slots must be at least as long as the required duration).

    Args:
        gaps:       sorted, non-overlapping free-gap intervals (minutes).
        slot_block: total minutes each slot occupies (duration + buffer).
        n:          maximum number of slots to place.

    Returns:
        Chronologically ordered list of Interval objects.
    """
    slots: List[Interval] = []
    for gap_start, gap_end in gaps:
        cursor = gap_start
        while cursor + slot_block <= gap_end and len(slots) < n:
            slots.append(
                Interval(
                    TimeSlot.from_minutes(cursor),
                    TimeSlot.from_minutes(cursor + slot_block),
                )
            )
            cursor += slot_block          # advance past this slot
        if len(slots) >= n:
            break
    return slots


# ── Main Public Function ──────────────────────────────────────────────────────

def recommend_slots(
    work_start: TimeSlot,
    work_end: TimeSlot,
    busy_intervals: List[Interval],
    meeting_duration: int,
    n: int,
    buffer_time: int = 0,
    candidate_windows: Optional[List[Interval]] = None,
) -> List[Interval]:
    """
    Recommend up to *n* non-overlapping meeting slots that satisfy all
    constraints.

    Algorithm overview:
        1. Validate all inputs (working hours, duration, buffer, N,
           busy-interval ordering, candidate-window ordering).
        2. Sort and merge busy intervals; expand each by buffer_time so
           that a slot placed right after a busy block automatically
           respects the required buffer gap.
        3. Compute free gaps within working hours.  Busy intervals that
           fall fully or partially outside working hours are clipped /
           ignored.
        4. If candidate windows are provided, intersect the free gaps
           with the candidate windows.
        5. Greedily fill the remaining gaps with slots of size
           (meeting_duration + buffer_time), filling chronologically
           from the earliest gap.

    Args:
        work_start:       beginning of the working day (inclusive).
        work_end:         end of the working day (exclusive).
        busy_intervals:   existing busy blocks (need not be sorted;
                          intervals outside working hours are ignored).
        meeting_duration: length of each meeting in minutes (> 0).
        n:                maximum number of slots to return (> 0).
        buffer_time:      minutes of buffer after every meeting **and**
                          after every busy interval (default 0, >= 0).
        candidate_windows: if provided, every slot must fall entirely
                           within at least one candidate window.

    Returns:
        List of up to *n* Interval objects in chronological order.
        Each slot spans (meeting_duration + buffer_time) minutes.
        Returns fewer than *n* (or []) when not enough room exists.

    Raises:
        ValueError: on invalid inputs (see _validate_inputs).
    """
    # 1. Validate
    _validate_inputs(
        work_start, work_end, meeting_duration, buffer_time, n,
        busy_intervals, candidate_windows,
    )

    work_s = work_start.to_minutes()
    work_e = work_end.to_minutes()
    slot_block = meeting_duration + buffer_time

    # 2. Merge busy intervals and expand by buffer
    busy_mins = _merge_intervals(
        [iv.to_minutes() for iv in busy_intervals]
    )
    expanded_busy: List[Tuple[int, int]] = [
        (s, e + buffer_time) for s, e in busy_mins
    ]

    # 3. Free gaps within working hours
    gaps = _compute_free_gaps(work_s, work_e, expanded_busy)

    # 4. Optionally restrict to candidate windows
    if candidate_windows:
        gaps = _intersect_with_candidates(gaps, candidate_windows)

    # 5. Greedily place slots
    return _fill_slots(gaps, slot_block, n)