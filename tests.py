

## Student Name: Rajendra Brahmbhatt
## Student ID: 217925157

"""
Tests for the Appointment Schedule Recommender.

Each test_ac* function maps directly to an acceptance criterion (AC1–AC9)
from the requirements document.  Additional tests cover input validation
and edge cases.
"""

import pytest
from solution import TimeSlot, Interval, recommend_slots


# ── Shorthand Helpers ─────────────────────────────────────────────────────────

def ts(h: int, m: int = 0) -> TimeSlot:
    """Shorthand constructor for TimeSlot."""
    return TimeSlot(h, m)


def iv(sh: int, sm: int, eh: int, em: int) -> Interval:
    """Shorthand constructor for Interval."""
    return Interval(ts(sh, sm), ts(eh, em))


# ── AC1: Fully busy window returns empty list ────────────────────────────────

def test_ac1_fully_busy_returns_empty():
    """
    AC1: working 09:00–10:00, busy [(09:00,10:00)], dur=30, buffer=0, N=5
    Expected: []
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(10),
        busy_intervals=[iv(9, 0, 10, 0)],
        meeting_duration=30,
        n=5,
        buffer_time=0,
    )
    assert result == []


# ── AC2: No busy intervals, three hourly slots ───────────────────────────────

def test_ac2_no_busy_three_hourly_slots():
    """
    AC2: working 09:00–17:00, no busy, dur=60, buffer=0, N=3
    Expected: [(09:00,10:00),(10:00,11:00),(11:00,12:00)]
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(17),
        busy_intervals=[],
        meeting_duration=60,
        n=3,
        buffer_time=0,
    )
    assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]


# ── AC3: Busy interval in the middle is skipped ──────────────────────────────

def test_ac3_busy_interval_skipped():
    """
    AC3: working 09:00–17:00, busy [(10:00,11:00)], dur=30, buffer=0, N=3
    Expected: [(09:00,09:30),(09:30,10:00),(11:00,11:30)]
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(17),
        busy_intervals=[iv(10, 0, 11, 0)],
        meeting_duration=30,
        n=3,
        buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 30), iv(9, 30, 10, 0), iv(11, 0, 11, 30)]


# ── AC4: Candidate window restricts slots ────────────────────────────────────

def test_ac4_candidate_window_filter():
    """
    AC4: working 09:00–17:00, no busy, dur=30, buffer=0,
         candidate=[(12:00,14:00)], N=3
    Expected: [(12:00,12:30),(12:30,13:00),(13:00,13:30)]
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(17),
        busy_intervals=[],
        meeting_duration=30,
        n=3,
        buffer_time=0,
        candidate_windows=[iv(12, 0, 14, 0)],
    )
    assert result == [iv(12, 0, 12, 30), iv(12, 30, 13, 0), iv(13, 0, 13, 30)]


# ── AC5: Deterministic output under identical inputs ─────────────────────────

def test_ac5_deterministic_output():
    """
    AC5: Same inputs twice must yield identical results.
    working 09:00–17:00, no busy, dur=60, buffer=0, N=3
    """
    kwargs = dict(
        work_start=ts(9),
        work_end=ts(17),
        busy_intervals=[],
        meeting_duration=60,
        n=3,
        buffer_time=0,
    )
    assert recommend_slots(**kwargs) == recommend_slots(**kwargs)


# ── AC6: Unsorted busy intervals are handled correctly ───────────────────────

def test_ac6_unsorted_busy_intervals():
    """
    AC6: working 09:00–12:00, busy [(10:00,10:30),(9:30,10:00)], dur=30,
         buffer=0, N=1
    Expected: [(09:00,09:30)]
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[iv(10, 0, 10, 30), iv(9, 30, 10, 0)],
        meeting_duration=30,
        n=1,
        buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 30)]


# ── AC7: Buffer time is included in slot duration ────────────────────────────

def test_ac7_buffer_time_included_in_slot():
    """
    AC7: working 09:00–12:00, busy [(10:00,11:00)], dur=30, buffer=10, N=1
    Expected: [(09:00,09:40)]  — 30 min meeting + 10 min buffer
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[iv(10, 0, 11, 0)],
        meeting_duration=30,
        n=1,
        buffer_time=10,
    )
    assert result == [iv(9, 0, 9, 40)]


# ── AC8: Tight gaps may return fewer than N slots ────────────────────────────

def test_ac8_tight_gaps_return_fewer_than_n():
    """
    AC8: working 09:00–12:00,
         busy [(9:20,9:50),(10:10,10:50),(11:10,11:40)],
         dur=30, buffer=0, N=3

    Free gaps: 9:00–9:20 (20 min), 9:50–10:10 (20 min),
               10:50–11:10 (20 min), 11:40–12:00 (20 min).
    None is >= 30 min, so no slot fits.  Returns [].

    NOTE: The original AC8 expected [(9:50,10:10)] which is only 20 min
    for a 30-min meeting — likely a typo.  Our implementation correctly
    returns [] because no gap can hold a 30-minute meeting.
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[iv(9, 20, 9, 50), iv(10, 10, 10, 50), iv(11, 10, 11, 40)],
        meeting_duration=30,
        n=3,
        buffer_time=0,
    )
    # Mathematically correct: no gap >= 30 min exists
    assert result == []


# ── AC9: Overlapping busy intervals are merged ───────────────────────────────

def test_ac9_overlapping_busy_merged():
    """
    AC9: working 09:00–12:00, busy [(9:00,10:30),(10:00,11:00)], dur=30,
         buffer=0, N=1
    Expected: [(11:00,11:30)]
    Overlapping busy blocks merge into 9:00–11:00.
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[iv(9, 0, 10, 30), iv(10, 0, 11, 0)],
        meeting_duration=30,
        n=1,
        buffer_time=0,
    )
    assert result == [iv(11, 0, 11, 30)]


# ── Validation / Error Tests ─────────────────────────────────────────────────

def test_error_start_ge_end():
    """ValueError when working-hours start >= end."""
    with pytest.raises(ValueError):
        recommend_slots(ts(17), ts(9), [], 30, 1)


def test_error_start_equals_end():
    """ValueError when working-hours start == end."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(9), [], 30, 1)


def test_error_duration_zero():
    """ValueError when meeting_duration == 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 0, 1)


def test_error_duration_negative():
    """ValueError when meeting_duration < 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], -10, 1)


def test_error_negative_buffer():
    """ValueError when buffer_time < 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 30, 1, buffer_time=-5)


# ── Extra Edge-Case Tests ────────────────────────────────────────────────────

def test_n_zero_returns_empty():
    """Requesting 0 slots returns an empty list."""
    result = recommend_slots(ts(9), ts(17), [], 30, n=0)
    assert result == []


def test_buffer_after_busy_respected():
    """
    Buffer pushes first available slot past busy end + buffer.
    Working 09:00–12:00, busy [(09:00,09:30)], dur=30, buffer=15, N=1
    Effective busy expands to 09:00–09:45, first slot starts at 09:45.
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[iv(9, 0, 9, 30)],
        meeting_duration=30,
        n=1,
        buffer_time=15,
    )
    assert result == [iv(9, 45, 10, 30)]


def test_multiple_candidate_windows():
    """Slots are placed across multiple candidate windows."""
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(17),
        busy_intervals=[],
        meeting_duration=30,
        n=4,
        buffer_time=0,
        candidate_windows=[iv(9, 0, 10, 0), iv(14, 0, 15, 0)],
    )
    assert result == [
        iv(9, 0, 9, 30),
        iv(9, 30, 10, 0),
        iv(14, 0, 14, 30),
        iv(14, 30, 15, 0),
    ]


def test_chronological_order():
    """All returned slots are in strictly chronological order."""
    result = recommend_slots(
        work_start=ts(8),
        work_end=ts(18),
        busy_intervals=[iv(10, 0, 12, 0), iv(14, 0, 15, 0)],
        meeting_duration=60,
        n=5,
        buffer_time=0,
    )
    for i in range(len(result) - 1):
        assert result[i].end.to_minutes() <= result[i + 1].start.to_minutes()


def test_slot_does_not_exceed_working_hours():
    """A slot must fit entirely within working hours."""
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(9, 45),
        busy_intervals=[],
        meeting_duration=60,
        n=1,
        buffer_time=0,
    )
    # 60-min slot cannot fit in a 45-min window
    assert result == []


def test_buffer_between_consecutive_slots():
    """
    With buffer=10, consecutive 30-min meetings are 40 min apart.
    Working 09:00–12:00, no busy, dur=30, buffer=10, N=3
    Expected: [(09:00,09:40),(09:40,10:20),(10:20,11:00)]
    """
    result = recommend_slots(
        work_start=ts(9),
        work_end=ts(12),
        busy_intervals=[],
        meeting_duration=30,
        n=3,
        buffer_time=10,
    )
    assert result == [iv(9, 0, 9, 40), iv(9, 40, 10, 20), iv(10, 20, 11, 0)]