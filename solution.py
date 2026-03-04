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
    def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:

        # -------------------- Validations --------------------

        if working_hours.start >= working_hours.end:
            raise ValueError("Working hours start time must be before end time")

        if duration <= timedelta(0):
            raise ValueError("Meeting duration must be greater than zero")

        if buffer < timedelta(0):
            raise ValueError("Buffer time cannot be negative")

        if n == 0:
            return []

        # -------------------- Effective Window --------------------

        effective_start = working_hours.start
        effective_end = working_hours.end

        if candidate_window:
            if candidate_window.start >= candidate_window.end:
                raise ValueError("Candidate window start must be before end")

            effective_start = max(effective_start, candidate_window.start)
            effective_end = min(effective_end, candidate_window.end)

            if effective_start >= effective_end:
                return []

        # -------------------- Normalize Busy Intervals --------------------

        # Sort busy intervals
        busy_intervals_sorted = sorted(busy_intervals, key=lambda x: x.start)

        # Merge overlapping intervals
        merged_busy = []
        for interval in busy_intervals_sorted:
            if interval.start >= interval.end:
                continue

            if not merged_busy:
                merged_busy.append(interval)
            else:
                last = merged_busy[-1]
                if interval.start <= last.end:
                    merged_busy[-1] = BusyInterval(
                        start=last.start,
                        end=max(last.end, interval.end)
                    )
                else:
                    merged_busy.append(interval)

        # -------------------- Build Free Gaps --------------------

        free_gaps = []

        current_start = effective_start

        for busy in merged_busy:
            if busy.end <= effective_start:
                continue
            if busy.start >= effective_end:
                break

            busy_start = max(busy.start, effective_start)
            busy_end = min(busy.end, effective_end)

            if busy_start > current_start:
                free_gaps.append((current_start, busy_start))

            current_start = max(current_start, busy_end)

        if current_start < effective_end:
            free_gaps.append((current_start, effective_end))

        # -------------------- Generate Slots --------------------

        slots = []
        full_block = duration + buffer

        for gap_start, gap_end in free_gaps:
            cursor = gap_start

            # Generate full-duration slots first
            while cursor + full_block <= gap_end:
                slots.append(Slot(start_time=cursor))
                if len(slots) == n:
                    return slots
                cursor = cursor + full_block

        # -------------------- If No Full Slots Exist --------------------

        if not slots:
            # Return maximum shorter gaps (deterministic left-to-right)
            shorter_slots = []

            for gap_start, gap_end in free_gaps:
                gap_length = datetime.combine(day, gap_end) - datetime.combine(day, gap_start)
                if gap_length > timedelta(0):
                    shorter_slots.append(
                        Slot(start_time=gap_start)
                    )
                    if len(shorter_slots) == n:
                        break

            return shorter_slots

        return slots
