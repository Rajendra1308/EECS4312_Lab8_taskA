## Student Name: Rajendra Brahmbhatt 
## Student ID: 217925157

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption (unless stated otherwise in handout): non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""
    pass


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.

    Args:
        day: the calendar day for which to suggest slots.
        working_hours: the allowed working window for meetings (start < end).
        busy_intervals: list of busy time intervals (may be overlapping / unsorted).
        duration: required meeting length (must be > 0).
        n: maximum number of slot suggestions to return (n >= 0).
        buffer: optional buffer time required between meetings (buffer >= 0).
        candidate_window: optional extra restriction on suggestions (must lie within this window too).

    Returns:
        A list of Slot objects, sorted by start_time ascending, deterministic under identical inputs.
        If no suitable time slots are available, return an empty list.

    Notes:
        - Suggested slots must fall within working_hours (and candidate_window if provided).
        - Suggested slots must not overlap busy_intervals, considering buffer time.
        - You are free to choose internal representation; inputs use time-of-day.
        - See lab handout for required slot granularity (e.g., 5-min/15-min steps), if any.
    """

    ##################################################################
    # TODO: Implement as per lab handout requirements and constraints.
    ##################################################################




    # ==================== VALIDATION ====================

    if working_hours.start >= working_hours.end:
        raise ValueError("Working hours start must be before end")

    if duration <= timedelta(0):
        raise ValueError("Meeting duration must be greater than zero")

    if buffer < timedelta(0):
        raise ValueError("Buffer cannot be negative")

    if n <= 0:
        raise ValueError("N must be greater than zero")

    if candidate_window:
        if candidate_window.start >= candidate_window.end:
            raise ValueError("Candidate window start must be before end")

    for b in busy_intervals:
        if b.start >= b.end:
            raise ValueError("Busy interval start must be before end")

    # ==================== EFFECTIVE WINDOW ====================

    effective_start = working_hours.start
    effective_end = working_hours.end

    if candidate_window:
        effective_start = max(effective_start, candidate_window.start)
        effective_end = min(effective_end, candidate_window.end)

        if effective_start >= effective_end:
            return []

    effective_start_dt = datetime.combine(day, effective_start)
    effective_end_dt = datetime.combine(day, effective_end)

    # ==================== NORMALIZE BUSY ====================

    busy_sorted = sorted(busy_intervals, key=lambda b: b.start)

    merged = []

    for b in busy_sorted:
        b_start = datetime.combine(day, b.start) - buffer
        b_end = datetime.combine(day, b.end) + buffer

        # Ignore busy intervals fully outside working window
        if b_end <= effective_start_dt or b_start >= effective_end_dt:
            continue

        b_start = max(b_start, effective_start_dt)
        b_end = min(b_end, effective_end_dt)

        if not merged:
            merged.append((b_start, b_end))
        else:
            last_start, last_end = merged[-1]
            if b_start <= last_end:
                merged[-1] = (last_start, max(last_end, b_end))
            else:
                merged.append((b_start, b_end))

    # ==================== BUILD FREE GAPS ====================

    free_gaps = []
    cursor = effective_start_dt

    for b_start, b_end in merged:
        if b_start > cursor:
            free_gaps.append((cursor, b_start))
        cursor = max(cursor, b_end)

    if cursor < effective_end_dt:
        free_gaps.append((cursor, effective_end_dt))

    # ==================== GENERATE SLOTS ====================


    slots = []

    meeting_length = duration
    step = duration + buffer  # sequential scheduling with buffer between meetings

    for gap_start, gap_end in free_gaps:
        slot_cursor = gap_start

        while slot_cursor + meeting_length <= gap_end:

            new_slot_end = slot_cursor + meeting_length

            # Ensure slot fits within effective window
            if not (effective_start_dt <= slot_cursor and new_slot_end <= effective_end_dt):
                slot_cursor += step
                continue

            slots.append(Slot(start_time=slot_cursor.time()))

            if len(slots) == n:
                return slots

            # Move cursor by meeting duration + buffer
            slot_cursor += step

    # ==================== FALLBACK (SHORTER GAPS) ====================

    if not slots:
        shorter = []
        for gap_start, gap_end in free_gaps:
            if gap_end > gap_start:
                shorter.append(Slot(start_time=gap_start.time()))
                if len(shorter) == n:
                    break
        return shorter

    return slots