## Student Name: Rajendra Brahmbhatt
## Student ID: 217925157

"""
Tests for the Appointment Schedule Recommender.

Organisation:
  - test_ac*    → Acceptance Criteria (AC1–AC9)
  - test_ec*    → Edge Cases (EC1–EC7)
  - test_val*   → Input validation / ValueError cases
  - test_inv*   → Invariant checks
  - test_tie*   → Tie-breaking rule checks
  - test_neg*   → Negative-requirement checks
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


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCEPTANCE CRITERIA  (AC1 – AC9)
# ═══════════════════════════════════════════════════════════════════════════════

def test_ac1_fully_busy_returns_empty():
    """
    AC1: working 09:00–10:00, busy [(09:00,10:00)], dur=30, buffer=0, N=5
    Expected: []
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(10),
        busy_intervals=[iv(9, 0, 10, 0)],
        meeting_duration=30, n=5, buffer_time=0,
    )
    assert result == []


def test_ac2_no_busy_three_hourly_slots():
    """
    AC2: working 09:00–17:00, no busy, dur=60, buffer=0, N=3
    Expected: [(09:00,10:00),(10:00,11:00),(11:00,12:00)]
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[],
        meeting_duration=60, n=3, buffer_time=0,
    )
    assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]


def test_ac3_busy_interval_skipped():
    """
    AC3: working 09:00–17:00, busy [(10:00,11:00)], dur=30, buffer=0, N=3
    Expected: [(09:00,09:30),(09:30,10:00),(11:00,11:30)]
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(10, 0, 11, 0)],
        meeting_duration=30, n=3, buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 30), iv(9, 30, 10, 0), iv(11, 0, 11, 30)]


def test_ac4_candidate_window_filter():
    """
    AC4: working 09:00–17:00, no busy, dur=30, buffer=0,
         candidate=[(12:00,14:00)], N=3
    Expected: [(12:00,12:30),(12:30,13:00),(13:00,13:30)]
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[],
        meeting_duration=30, n=3, buffer_time=0,
        candidate_windows=[iv(12, 0, 14, 0)],
    )
    assert result == [iv(12, 0, 12, 30), iv(12, 30, 13, 0), iv(13, 0, 13, 30)]


def test_ac5_deterministic_output():
    """
    AC5: Same inputs twice must yield identical results.
    working 09:00–17:00, no busy, dur=60, buffer=0, N=3
    """
    kwargs = dict(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[],
        meeting_duration=60, n=3, buffer_time=0,
    )
    assert recommend_slots(**kwargs) == recommend_slots(**kwargs)


def test_ac6_unsorted_busy_intervals():
    """
    AC6: working 09:00–12:00, busy [(10:00,10:30),(9:30,10:00)], dur=30,
         buffer=0, N=1
    Expected: [(09:00,09:30)]
    Busy intervals given out of order — system must sort them.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(10, 0, 10, 30), iv(9, 30, 10, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 30)]


def test_ac7_buffer_time_included_in_slot():
    """
    AC7: working 09:00–12:00, busy [(10:00,11:00)], dur=30, buffer=10, N=1
    Expected: [(09:00,09:40)]  — 30 min meeting + 10 min buffer
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(10, 0, 11, 0)],
        meeting_duration=30, n=1, buffer_time=10,
    )
    assert result == [iv(9, 0, 9, 40)]


def test_ac8_no_gap_fits_full_meeting():
    """
    AC8: working 09:00–12:00,
         busy [(9:20,9:50),(10:10,10:50),(11:10,11:40)],
         dur=30, buffer=0, N=3

    Free gaps: 9:00–9:20 (20m), 9:50–10:10 (20m),
               10:50–11:10 (20m), 11:40–12:00 (20m).
    None is >= 30 min.

    The spec AC8 expects [(9:50,10:10)].  However, the invariant states
    "returned slots must be at least as long as the required duration".
    Since 20 < 30, returning that gap would violate the invariant.

    Our implementation returns [] — no gap can hold a 30-min meeting.
    If the AC intended a 20-minute meeting, the test below can be
    adjusted accordingly.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 20, 9, 50), iv(10, 10, 10, 50), iv(11, 10, 11, 40)],
        meeting_duration=30, n=3, buffer_time=0,
    )
    assert result == []


def test_ac8_variant_with_20min_meeting():
    """
    AC8 variant: same scenario but with dur=20 (matching gap size).
    Gaps are each 20 min.  With dur=20, all four gaps fit.  N=3 → 3 slots.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 20, 9, 50), iv(10, 10, 10, 50), iv(11, 10, 11, 40)],
        meeting_duration=20, n=3, buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 20), iv(9, 50, 10, 10), iv(10, 50, 11, 10)]


def test_ac9_overlapping_busy_merged():
    """
    AC9: working 09:00–12:00, busy [(9:00,10:30),(10:00,11:00)], dur=30,
         buffer=0, N=1
    Expected: [(11:00,11:30)]
    Overlapping busy blocks merge → effective busy 9:00–11:00.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 0, 10, 30), iv(10, 0, 11, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    assert result == [iv(11, 0, 11, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  EDGE CASES  (EC1 – EC7)
# ═══════════════════════════════════════════════════════════════════════════════

def test_ec1_entire_window_busy():
    """EC1: Entire working window occupied → no slots available."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(10),
        busy_intervals=[iv(9, 0, 10, 0)],
        meeting_duration=30, n=5, buffer_time=0,
    )
    assert result == []


def test_ec2_adjacent_busy_no_gap():
    """EC2: Two adjacent busy intervals leave no gap between them."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 0, 10, 0), iv(10, 0, 11, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    # Only gap is 11:00–12:00
    assert result == [iv(11, 0, 11, 30)]


def test_ec3_unsorted_busy_handled():
    """EC3: Busy intervals given out of chronological order."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(10, 0, 10, 30), iv(9, 30, 10, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    assert result == [iv(9, 0, 9, 30)]


def test_ec4_meeting_longer_than_any_gap():
    """EC4: Meeting duration exceeds every available gap."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(11),
        busy_intervals=[iv(9, 40, 10, 20)],
        meeting_duration=60, n=1, buffer_time=0,
    )
    # Gaps: 9:00–9:40 (40m), 10:20–11:00 (40m).  Neither fits 60m.
    assert result == []


def test_ec5_buffer_eliminates_otherwise_valid_slot():
    """EC5: Buffer time consumes a gap that otherwise fits the meeting."""
    # Gap before busy: 9:00–10:00 (60 min).
    # Meeting=30, buffer=35 → slot_block=65 > 60 → does not fit.
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(10, 0, 11, 0)],
        meeting_duration=30, n=1, buffer_time=35,
    )
    # First gap 9:00–9:50 after expansion (busy expands to 10:00–11:35).
    # 9:00–9:50 is only 50 min; need 65 → doesn't fit.
    # Second gap: 11:35–12:00 = 25 min → doesn't fit.
    # Actually let's recalculate: expanded busy = (600, 695).
    # Gaps within 540–720: 540–600 (60 min), 695–720 (25 min).
    # slot_block = 65 → 60 < 65 → first gap doesn't fit. 25 < 65 → nope.
    assert result == []


def test_ec6_very_small_gaps():
    """EC6: Gaps between meetings are too small for the meeting duration."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 10, 9, 50), iv(10, 0, 10, 50), iv(11, 0, 11, 50)],
        meeting_duration=15, n=5, buffer_time=0,
    )
    # Gaps: 9:00–9:10 (10m, <15), 9:50–10:00 (10m, <15),
    #        10:50–11:00 (10m, <15), 11:50–12:00 (10m, <15)
    assert result == []


def test_ec7_overlapping_busy_intervals():
    """EC7: Overlapping busy intervals are merged correctly."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 0, 10, 30), iv(10, 0, 11, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    assert result == [iv(11, 0, 11, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  VALIDATION / ValueError TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_val_work_start_after_end():
    """ValueError when working-hours start > end."""
    with pytest.raises(ValueError):
        recommend_slots(ts(17), ts(9), [], 30, 1)


def test_val_work_start_equals_end():
    """ValueError when working-hours start == end."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(9), [], 30, 1)


def test_val_duration_zero():
    """ValueError when meeting_duration == 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 0, 1)


def test_val_duration_negative():
    """ValueError when meeting_duration < 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], -10, 1)


def test_val_negative_buffer():
    """ValueError when buffer_time < 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 30, 1, buffer_time=-5)


def test_val_n_zero():
    """ValueError when N == 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 30, n=0)


def test_val_n_negative():
    """ValueError when N < 0."""
    with pytest.raises(ValueError):
        recommend_slots(ts(9), ts(17), [], 30, n=-1)


def test_val_busy_interval_start_ge_end():
    """ValueError when a busy interval has start >= end."""
    with pytest.raises(ValueError):
        recommend_slots(
            ts(9), ts(17),
            busy_intervals=[iv(11, 0, 10, 0)],   # 11:00 >= 10:00
            meeting_duration=30, n=1,
        )


def test_val_busy_interval_start_equals_end():
    """ValueError when a busy interval has start == end (zero-length)."""
    with pytest.raises(ValueError):
        recommend_slots(
            ts(9), ts(17),
            busy_intervals=[iv(10, 0, 10, 0)],   # zero-length
            meeting_duration=30, n=1,
        )


def test_val_candidate_window_start_ge_end():
    """ValueError when a candidate window has start >= end."""
    with pytest.raises(ValueError):
        recommend_slots(
            ts(9), ts(17), [],
            meeting_duration=30, n=1,
            candidate_windows=[iv(14, 0, 12, 0)],  # 14:00 >= 12:00
        )


def test_val_candidate_window_start_equals_end():
    """ValueError when a candidate window has start == end."""
    with pytest.raises(ValueError):
        recommend_slots(
            ts(9), ts(17), [],
            meeting_duration=30, n=1,
            candidate_windows=[iv(12, 0, 12, 0)],
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  INVARIANT CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def test_inv_slots_within_working_hours():
    """Every returned slot must fall entirely within working hours."""
    result = recommend_slots(
        work_start=ts(10), work_end=ts(14),
        busy_intervals=[iv(11, 0, 12, 0)],
        meeting_duration=30, n=10, buffer_time=0,
    )
    for slot in result:
        s, e = slot.to_minutes()
        assert s >= ts(10).to_minutes()
        assert e <= ts(14).to_minutes()


def test_inv_slot_duration_ge_meeting_duration():
    """Returned slots must be at least as long as meeting_duration."""
    dur = 45
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(10, 0, 11, 0), iv(13, 0, 14, 0)],
        meeting_duration=dur, n=10, buffer_time=0,
    )
    for slot in result:
        s, e = slot.to_minutes()
        assert (e - s) >= dur


def test_inv_no_overlap_between_slots():
    """No two returned slots may overlap."""
    result = recommend_slots(
        work_start=ts(8), work_end=ts(18),
        busy_intervals=[iv(10, 0, 11, 0), iv(14, 0, 15, 0)],
        meeting_duration=30, n=20, buffer_time=10,
    )
    for i in range(len(result) - 1):
        _, end_i = result[i].to_minutes()
        start_next, _ = result[i + 1].to_minutes()
        assert end_i <= start_next


def test_inv_no_overlap_with_busy():
    """No returned slot may overlap any busy interval."""
    busy = [iv(10, 0, 11, 0), iv(13, 30, 14, 30)]
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=busy,
        meeting_duration=30, n=10, buffer_time=0,
    )
    busy_mins = [(b.start.to_minutes(), b.end.to_minutes()) for b in busy]
    for slot in result:
        ss, se = slot.to_minutes()
        for bs, be in busy_mins:
            # Slot must not overlap busy: not (ss < be and se > bs)
            assert not (ss < be and se > bs), (
                f"Slot {slot} overlaps busy ({bs}, {be})"
            )


def test_inv_deterministic_repeated_calls():
    """Multiple identical calls yield identical results (determinism)."""
    kwargs = dict(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(10, 0, 11, 0), iv(14, 0, 15, 0)],
        meeting_duration=30, n=8, buffer_time=5,
    )
    first = recommend_slots(**kwargs)
    for _ in range(5):
        assert recommend_slots(**kwargs) == first


# ═══════════════════════════════════════════════════════════════════════════════
#  TIE-BREAKING RULE CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def test_tie_chronological_first():
    """
    Tie-breaking rule #1: prefer the chronologically earliest slot.
    Two free gaps: 11:00–12:00 and 14:30–15:30.  With N=1, pick 11:00.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(9, 0, 11, 0), iv(12, 0, 14, 30), iv(15, 30, 17, 0)],
        meeting_duration=60, n=1, buffer_time=0,
    )
    assert result == [iv(11, 0, 12, 0)]


def test_tie_fill_from_gap_start():
    """
    Tie-breaking rule #2: fill from the start of a gap, not the middle.
    Free gap 13:00–16:00, dur=30, buffer=15.  Slots should start at 13:00.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(9, 0, 13, 0)],
        meeting_duration=30, n=3, buffer_time=15,
    )
    # Busy (9:00–13:00) expands by buffer → (9:00–13:15).
    # Free gap starts at 13:15.  slot_block = 45.
    # Slots: 13:15–14:00, 14:00–14:45, 14:45–15:30
    assert result == [iv(13, 15, 14, 0), iv(14, 0, 14, 45), iv(14, 45, 15, 30)]


def test_tie_no_workload_spreading():
    """
    Tie-breaking rule #3: system does NOT try to spread meetings evenly.
    Gap at 11:30–12:00 (30 min) and 14:00–17:00 (180 min).
    With dur=30 and N=1, the 11:30 gap is chosen despite 14:00 being larger.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[iv(9, 0, 11, 30), iv(12, 0, 14, 0)],
        meeting_duration=30, n=1, buffer_time=0,
    )
    assert result == [iv(11, 30, 12, 0)]


# ═══════════════════════════════════════════════════════════════════════════════
#  NEGATIVE REQUIREMENT CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def test_neg_no_slot_outside_working_hours():
    """System must NOT return slots outside the working window."""
    result = recommend_slots(
        work_start=ts(10), work_end=ts(12),
        busy_intervals=[],
        meeting_duration=30, n=10, buffer_time=0,
    )
    for slot in result:
        s, e = slot.to_minutes()
        assert s >= ts(10).to_minutes()
        assert e <= ts(12).to_minutes()


def test_neg_no_short_slots():
    """System must NOT return a slot shorter than meeting_duration."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 20, 9, 50), iv(10, 10, 10, 50)],
        meeting_duration=30, n=5, buffer_time=0,
    )
    for slot in result:
        s, e = slot.to_minutes()
        assert (e - s) >= 30


# ═══════════════════════════════════════════════════════════════════════════════
#  ADDITIONAL EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

def test_busy_outside_working_hours_ignored():
    """Busy intervals fully outside working hours are ignored."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(7, 0, 8, 0), iv(13, 0, 14, 0)],
        meeting_duration=60, n=3, buffer_time=0,
    )
    # Entire 9–12 window is free
    assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]


def test_busy_partially_outside_working_hours_clipped():
    """Busy intervals partially outside working hours are clipped."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(8, 0, 10, 0)],   # starts before work
        meeting_duration=30, n=1, buffer_time=0,
    )
    # Effective busy within work: 9:00–10:00.  First slot at 10:00.
    assert result == [iv(10, 0, 10, 30)]


def test_buffer_after_busy_respected():
    """
    Buffer pushes the first available slot past busy end + buffer.
    Working 09:00–12:00, busy [(09:00,09:30)], dur=30, buffer=15, N=1
    Expanded busy: 09:00–09:45.  First slot at 09:45.
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[iv(9, 0, 9, 30)],
        meeting_duration=30, n=1, buffer_time=15,
    )
    assert result == [iv(9, 45, 10, 30)]


def test_multiple_candidate_windows():
    """Slots placed across multiple disjoint candidate windows."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(17),
        busy_intervals=[],
        meeting_duration=30, n=4, buffer_time=0,
        candidate_windows=[iv(9, 0, 10, 0), iv(14, 0, 15, 0)],
    )
    assert result == [
        iv(9, 0, 9, 30), iv(9, 30, 10, 0),
        iv(14, 0, 14, 30), iv(14, 30, 15, 0),
    ]


def test_chronological_order():
    """All returned slots are in strictly chronological order."""
    result = recommend_slots(
        work_start=ts(8), work_end=ts(18),
        busy_intervals=[iv(10, 0, 12, 0), iv(14, 0, 15, 0)],
        meeting_duration=60, n=5, buffer_time=0,
    )
    for i in range(len(result) - 1):
        _, end_i = result[i].to_minutes()
        start_next, _ = result[i + 1].to_minutes()
        assert end_i <= start_next


def test_buffer_between_consecutive_slots():
    """
    With buffer=10, consecutive 30-min meetings produce 40-min slots.
    Working 09:00–12:00, no busy, dur=30, buffer=10, N=3
    """
    result = recommend_slots(
        work_start=ts(9), work_end=ts(12),
        busy_intervals=[],
        meeting_duration=30, n=3, buffer_time=10,
    )
    assert result == [iv(9, 0, 9, 40), iv(9, 40, 10, 20), iv(10, 20, 11, 0)]


def test_slot_does_not_exceed_working_hours():
    """A slot must fit entirely within working hours."""
    result = recommend_slots(
        work_start=ts(9), work_end=ts(9, 45),
        busy_intervals=[],
        meeting_duration=60, n=1, buffer_time=0,
    )
    assert result == []