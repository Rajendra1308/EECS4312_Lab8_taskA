## Student Name: Rajendra Brahmbhatt
## Student ID: 217925157

"""
Tests for the Appointment Schedule Recommender.

Organisation:
  - test_ac*      → Acceptance Criteria (AC1–AC9)
  - test_ec*      → Edge Cases (EC1–EC7)
  - test_val*     → Input validation / ValueError cases
  - test_inv*     → Invariant checks
  - test_tie*     → Tie-breaking rule checks
  - test_neg*     → Negative-requirement checks
  - test_fr*      → Functional-requirement checks
  - test_cov*     → Extra coverage / data-class behaviour
  - test_buf*     → Buffer-specific scenarios
  - test_cand*    → Candidate-window scenarios
  - test_misc*    → Miscellaneous / stress / boundary
"""

import pytest
from solution import (
    TimeSlot,
    Interval,
    recommend_slots,
    _merge_intervals,
    _compute_free_gaps,
    _clip_busy_to_working_hours,
    _intersect_with_candidates,
    _fill_slots,
    _validate_inputs,
)


# ── Shorthand Helpers ─────────────────────────────────────────────────────────

def ts(h: int, m: int = 0) -> TimeSlot:
    """Shorthand constructor for TimeSlot."""
    return TimeSlot(h, m)


def iv(sh: int, sm: int, eh: int, em: int) -> Interval:
    """Shorthand constructor for Interval."""
    return Interval(ts(sh, sm), ts(eh, em))


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA-CLASS COVERAGE  (TimeSlot & Interval repr, eq, str, ordering)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimeSlot:
    """Unit tests for the TimeSlot data class."""

    def test_to_minutes(self):
        assert ts(0, 0).to_minutes() == 0
        assert ts(9, 30).to_minutes() == 570
        assert ts(23, 59).to_minutes() == 1439

    def test_from_minutes(self):
        assert TimeSlot.from_minutes(0) == ts(0, 0)
        assert TimeSlot.from_minutes(570) == ts(9, 30)
        assert TimeSlot.from_minutes(1439) == ts(23, 59)

    def test_str(self):
        assert str(ts(9, 5)) == "09:05"
        assert str(ts(0, 0)) == "00:00"
        assert str(ts(23, 59)) == "23:59"

    def test_repr(self):
        """Covers line 54: TimeSlot.__repr__"""
        assert repr(ts(9, 30)) == "TimeSlot(9, 30)"
        assert repr(ts(0, 0)) == "TimeSlot(0, 0)"

    def test_ordering(self):
        assert ts(9, 0) < ts(9, 1)
        assert ts(8, 59) < ts(9, 0)
        assert ts(10, 0) > ts(9, 59)
        assert ts(9, 0) == ts(9, 0)
        assert ts(9, 0) <= ts(9, 0)
        assert ts(9, 0) >= ts(9, 0)

    def test_frozen(self):
        """TimeSlot is immutable."""
        slot = ts(9, 0)
        with pytest.raises(AttributeError):
            slot.hour = 10


class TestInterval:
    """Unit tests for the Interval data class."""

    def test_to_minutes(self):
        assert iv(9, 0, 10, 30).to_minutes() == (540, 630)

    def test_eq_same(self):
        assert iv(9, 0, 10, 0) == iv(9, 0, 10, 0)

    def test_eq_different(self):
        assert iv(9, 0, 10, 0) != iv(9, 0, 11, 0)

    def test_eq_non_interval(self):
        """Covers line 72: Interval.__eq__ returns NotImplemented for non-Interval."""
        result = iv(9, 0, 10, 0).__eq__("not an interval")
        assert result is NotImplemented

    def test_eq_non_interval_via_operator(self):
        """Equality with a non-Interval type using == operator."""
        assert not (iv(9, 0, 10, 0) == 42)
        assert iv(9, 0, 10, 0) != 42
        assert iv(9, 0, 10, 0) != "string"
        assert iv(9, 0, 10, 0) != None

    def test_repr(self):
        r = repr(iv(9, 0, 10, 30))
        assert "09:00" in r
        assert "10:30" in r

    def test_frozen(self):
        """Interval is immutable."""
        interval = iv(9, 0, 10, 0)
        with pytest.raises(AttributeError):
            interval.start = ts(8, 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  INTERNAL HELPER UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergeIntervals:
    """Unit tests for _merge_intervals."""

    def test_empty_list(self):
        assert _merge_intervals([]) == []

    def test_single_interval(self):
        assert _merge_intervals([(10, 20)]) == [(10, 20)]

    def test_non_overlapping(self):
        assert _merge_intervals([(10, 20), (30, 40)]) == [(10, 20), (30, 40)]

    def test_overlapping(self):
        assert _merge_intervals([(10, 30), (20, 40)]) == [(10, 40)]

    def test_adjacent(self):
        assert _merge_intervals([(10, 20), (20, 30)]) == [(10, 30)]

    def test_contained(self):
        assert _merge_intervals([(10, 50), (20, 30)]) == [(10, 50)]

    def test_unsorted(self):
        assert _merge_intervals([(30, 40), (10, 20)]) == [(10, 20), (30, 40)]

    def test_multiple_overlapping(self):
        result = _merge_intervals([(10, 20), (15, 25), (24, 35), (50, 60)])
        assert result == [(10, 35), (50, 60)]

    def test_all_same(self):
        assert _merge_intervals([(10, 20), (10, 20), (10, 20)]) == [(10, 20)]


class TestClipBusyToWorkingHours:
    """Unit tests for _clip_busy_to_working_hours."""

    def test_fully_inside(self):
        result = _clip_busy_to_working_hours([(600, 660)], 540, 720)
        assert result == [(600, 660)]

    def test_fully_outside_before(self):
        result = _clip_busy_to_working_hours([(400, 500)], 540, 720)
        assert result == []

    def test_fully_outside_after(self):
        result = _clip_busy_to_working_hours([(800, 900)], 540, 720)
        assert result == []

    def test_partial_overlap_start(self):
        result = _clip_busy_to_working_hours([(500, 600)], 540, 720)
        assert result == [(540, 600)]

    def test_partial_overlap_end(self):
        result = _clip_busy_to_working_hours([(700, 800)], 540, 720)
        assert result == [(700, 720)]

    def test_empty_busy(self):
        result = _clip_busy_to_working_hours([], 540, 720)
        assert result == []


class TestComputeFreeGaps:
    """Unit tests for _compute_free_gaps."""

    def test_no_busy(self):
        result = _compute_free_gaps(540, 720, [])
        assert result == [(540, 720)]

    def test_busy_at_start(self):
        result = _compute_free_gaps(540, 720, [(540, 600)])
        assert result == [(600, 720)]

    def test_busy_at_end(self):
        result = _compute_free_gaps(540, 720, [(660, 720)])
        assert result == [(540, 660)]

    def test_busy_in_middle(self):
        result = _compute_free_gaps(540, 720, [(600, 660)])
        assert result == [(540, 600), (660, 720)]

    def test_fully_busy(self):
        result = _compute_free_gaps(540, 720, [(540, 720)])
        assert result == []

    def test_multiple_gaps(self):
        result = _compute_free_gaps(540, 720, [(560, 580), (620, 660)])
        assert result == [(540, 560), (580, 620), (660, 720)]


class TestIntersectWithCandidates:
    """Unit tests for _intersect_with_candidates."""

    def test_full_overlap(self):
        gaps = [(540, 720)]
        cands = [Interval(ts(9, 0), ts(12, 0))]
        result = _intersect_with_candidates(gaps, cands)
        assert result == [(540, 720)]

    def test_partial_overlap(self):
        gaps = [(540, 720)]
        cands = [Interval(ts(10, 0), ts(11, 0))]
        result = _intersect_with_candidates(gaps, cands)
        assert result == [(600, 660)]

    def test_no_overlap(self):
        gaps = [(540, 600)]
        cands = [Interval(ts(11, 0), ts(12, 0))]
        result = _intersect_with_candidates(gaps, cands)
        assert result == []

    def test_multiple_candidates(self):
        gaps = [(540, 720)]
        cands = [Interval(ts(9, 0), ts(10, 0)), Interval(ts(11, 0), ts(12, 0))]
        result = _intersect_with_candidates(gaps, cands)
        assert result == [(540, 600), (660, 720)]


class TestFillSlots:
    """Unit tests for _fill_slots."""

    def test_empty_gaps(self):
        assert _fill_slots([], 30, 5) == []

    def test_gap_too_small(self):
        assert _fill_slots([(540, 560)], 30, 5) == []

    def test_exact_fit(self):
        result = _fill_slots([(540, 570)], 30, 5)
        assert result == [Interval(ts(9, 0), ts(9, 30))]

    def test_n_limits_output(self):
        result = _fill_slots([(540, 720)], 30, 2)
        assert len(result) == 2

    def test_multiple_gaps(self):
        result = _fill_slots([(540, 600), (660, 720)], 30, 4)
        assert len(result) == 4


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCEPTANCE CRITERIA  (AC1 – AC9)
# ═══════════════════════════════════════════════════════════════════════════════

def test_ac1_fully_busy_returns_empty():
    """AC1: working 09:00–10:00, busy [(09:00,10:00)], dur=30, buffer=0, N=5 → []"""
    result = recommend_slots(ts(9), ts(10), [iv(9, 0, 10, 0)], 30, 5, 0)
    assert result == []


def test_ac2_no_busy_three_hourly_slots():
    """AC2: working 09:00–17:00, no busy, dur=60, buffer=0, N=3"""
    result = recommend_slots(ts(9), ts(17), [], 60, 3, 0)
    assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]


def test_ac3_busy_interval_skipped():
    """AC3: working 09:00–17:00, busy [(10:00,11:00)], dur=30, buffer=0, N=3"""
    result = recommend_slots(ts(9), ts(17), [iv(10, 0, 11, 0)], 30, 3, 0)
    assert result == [iv(9, 0, 9, 30), iv(9, 30, 10, 0), iv(11, 0, 11, 30)]


def test_ac4_candidate_window_filter():
    """AC4: working 09:00–17:00, no busy, dur=30, buffer=0, candidate=[(12:00,14:00)], N=3"""
    result = recommend_slots(
        ts(9), ts(17), [], 30, 3, 0,
        candidate_windows=[iv(12, 0, 14, 0)],
    )
    assert result == [iv(12, 0, 12, 30), iv(12, 30, 13, 0), iv(13, 0, 13, 30)]


def test_ac5_deterministic_output():
    """AC5: identical inputs yield identical output."""
    kwargs = dict(work_start=ts(9), work_end=ts(17), busy_intervals=[], meeting_duration=60, n=3, buffer_time=0)
    assert recommend_slots(**kwargs) == recommend_slots(**kwargs)


def test_ac6_unsorted_busy_intervals():
    """AC6: working 09:00–12:00, busy [(10:00,10:30),(9:30,10:00)], dur=30, buffer=0, N=1"""
    result = recommend_slots(ts(9), ts(12), [iv(10, 0, 10, 30), iv(9, 30, 10, 0)], 30, 1, 0)
    assert result == [iv(9, 0, 9, 30)]


def test_ac7_buffer_time_included_in_slot():
    """AC7: working 09:00–12:00, busy [(10:00,11:00)], dur=30, buffer=10, N=1 → [(9:00,9:40)]"""
    result = recommend_slots(ts(9), ts(12), [iv(10, 0, 11, 0)], 30, 1, 10)
    assert result == [iv(9, 0, 9, 40)]


def test_ac8_no_gap_fits_full_meeting():
    """AC8: no gap ≥ 30 min → []"""
    result = recommend_slots(
        ts(9), ts(12),
        [iv(9, 20, 9, 50), iv(10, 10, 10, 50), iv(11, 10, 11, 40)],
        30, 3, 0,
    )
    assert result == []


def test_ac8_variant_with_20min_meeting():
    """AC8 variant with dur=20 to match gap sizes."""
    result = recommend_slots(
        ts(9), ts(12),
        [iv(9, 20, 9, 50), iv(10, 10, 10, 50), iv(11, 10, 11, 40)],
        20, 3, 0,
    )
    assert result == [iv(9, 0, 9, 20), iv(9, 50, 10, 10), iv(10, 50, 11, 10)]


def test_ac9_overlapping_busy_merged():
    """AC9: busy [(9:00,10:30),(10:00,11:00)] merge → 9:00–11:00, slot at 11:00."""
    result = recommend_slots(ts(9), ts(12), [iv(9, 0, 10, 30), iv(10, 0, 11, 0)], 30, 1, 0)
    assert result == [iv(11, 0, 11, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  EDGE CASES  (EC1 – EC7)
# ═══════════════════════════════════════════════════════════════════════════════

def test_ec1_entire_window_busy():
    """EC1: Entire working window occupied → []."""
    assert recommend_slots(ts(9), ts(10), [iv(9, 0, 10, 0)], 30, 5, 0) == []


def test_ec2_adjacent_busy_no_gap():
    """EC2: Adjacent busy intervals leave no gap between them."""
    result = recommend_slots(ts(9), ts(12), [iv(9, 0, 10, 0), iv(10, 0, 11, 0)], 30, 1, 0)
    assert result == [iv(11, 0, 11, 30)]


def test_ec3_unsorted_busy_handled():
    """EC3: Busy intervals given out of chronological order."""
    result = recommend_slots(ts(9), ts(12), [iv(10, 0, 10, 30), iv(9, 30, 10, 0)], 30, 1, 0)
    assert result == [iv(9, 0, 9, 30)]


def test_ec4_meeting_longer_than_any_gap():
    """EC4: Meeting duration exceeds every available gap."""
    result = recommend_slots(ts(9), ts(11), [iv(9, 40, 10, 20)], 60, 1, 0)
    assert result == []


def test_ec5_buffer_eliminates_otherwise_valid_slot():
    """EC5: Buffer time consumes a gap that otherwise fits the meeting."""
    result = recommend_slots(ts(9), ts(12), [iv(10, 0, 11, 0)], 30, 1, 35)
    assert result == []


def test_ec6_very_small_gaps():
    """EC6: Gaps between meetings are too small for the meeting duration."""
    result = recommend_slots(
        ts(9), ts(12),
        [iv(9, 10, 9, 50), iv(10, 0, 10, 50), iv(11, 0, 11, 50)],
        15, 5, 0,
    )
    assert result == []


def test_ec7_overlapping_busy_intervals():
    """EC7: Overlapping busy intervals are merged correctly."""
    result = recommend_slots(ts(9), ts(12), [iv(9, 0, 10, 30), iv(10, 0, 11, 0)], 30, 1, 0)
    assert result == [iv(11, 0, 11, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  VALIDATION / ValueError TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidation:
    """Comprehensive input-validation tests."""

    # ── Working hours ─────────────────────────────────────────────────────

    def test_work_start_after_end(self):
        with pytest.raises(ValueError, match="start time must be strictly before"):
            recommend_slots(ts(17), ts(9), [], 30, 1)

    def test_work_start_equals_end(self):
        with pytest.raises(ValueError, match="start time must be strictly before"):
            recommend_slots(ts(9), ts(9), [], 30, 1)

    def test_work_start_one_minute_before_end_valid(self):
        """Minimal valid window (1 minute) should not raise."""
        result = recommend_slots(ts(9, 0), ts(9, 1), [], 1, 1, 0)
        assert len(result) == 1

    # ── Meeting duration ──────────────────────────────────────────────────

    def test_duration_zero(self):
        with pytest.raises(ValueError, match="greater than 0"):
            recommend_slots(ts(9), ts(17), [], 0, 1)

    def test_duration_negative(self):
        with pytest.raises(ValueError, match="greater than 0"):
            recommend_slots(ts(9), ts(17), [], -10, 1)

    def test_duration_one_minute_valid(self):
        """Minimal valid duration (1 minute) should not raise."""
        result = recommend_slots(ts(9), ts(10), [], 1, 1, 0)
        assert len(result) == 1

    # ── Buffer time ───────────────────────────────────────────────────────

    def test_negative_buffer(self):
        with pytest.raises(ValueError, match="non-negative"):
            recommend_slots(ts(9), ts(17), [], 30, 1, buffer_time=-5)

    def test_negative_buffer_minus_one(self):
        with pytest.raises(ValueError, match="non-negative"):
            recommend_slots(ts(9), ts(17), [], 30, 1, buffer_time=-1)

    def test_zero_buffer_valid(self):
        """Buffer of 0 is valid."""
        result = recommend_slots(ts(9), ts(17), [], 60, 1, buffer_time=0)
        assert len(result) == 1

    # ── N (number of slots) ──────────────────────────────────────────────

    def test_n_zero(self):
        with pytest.raises(ValueError, match="greater than 0"):
            recommend_slots(ts(9), ts(17), [], 30, n=0)

    def test_n_negative(self):
        with pytest.raises(ValueError, match="greater than 0"):
            recommend_slots(ts(9), ts(17), [], 30, n=-1)

    def test_n_negative_large(self):
        with pytest.raises(ValueError, match="greater than 0"):
            recommend_slots(ts(9), ts(17), [], 30, n=-100)

    def test_n_one_valid(self):
        """N=1 is valid."""
        result = recommend_slots(ts(9), ts(17), [], 60, n=1)
        assert len(result) == 1

    # ── Busy interval validation ─────────────────────────────────────────

    def test_busy_start_after_end(self):
        with pytest.raises(ValueError, match="Busy interval"):
            recommend_slots(ts(9), ts(17), [iv(11, 0, 10, 0)], 30, 1)

    def test_busy_start_equals_end(self):
        with pytest.raises(ValueError, match="Busy interval"):
            recommend_slots(ts(9), ts(17), [iv(10, 0, 10, 0)], 30, 1)

    def test_busy_second_interval_invalid(self):
        """Error raised even if the invalid interval is not the first one."""
        with pytest.raises(ValueError, match="Busy interval"):
            recommend_slots(
                ts(9), ts(17),
                [iv(10, 0, 11, 0), iv(13, 0, 12, 0)],
                30, 1,
            )

    def test_busy_multiple_invalid(self):
        """First invalid interval triggers the error."""
        with pytest.raises(ValueError, match="Busy interval"):
            recommend_slots(
                ts(9), ts(17),
                [iv(11, 0, 10, 0), iv(14, 0, 13, 0)],
                30, 1,
            )

    # ── Candidate window validation ──────────────────────────────────────

    def test_candidate_start_after_end(self):
        with pytest.raises(ValueError, match="Candidate window"):
            recommend_slots(ts(9), ts(17), [], 30, 1, candidate_windows=[iv(14, 0, 12, 0)])

    def test_candidate_start_equals_end(self):
        with pytest.raises(ValueError, match="Candidate window"):
            recommend_slots(ts(9), ts(17), [], 30, 1, candidate_windows=[iv(12, 0, 12, 0)])

    def test_candidate_second_window_invalid(self):
        """Error raised even if invalid candidate is not the first."""
        with pytest.raises(ValueError, match="Candidate window"):
            recommend_slots(
                ts(9), ts(17), [], 30, 1,
                candidate_windows=[iv(10, 0, 11, 0), iv(15, 0, 13, 0)],
            )

    # ── _validate_inputs direct calls ────────────────────────────────────

    def test_validate_inputs_no_error(self):
        """Valid inputs should not raise."""
        _validate_inputs(ts(9), ts(17), 30, 0, 1, [], None)

    def test_validate_inputs_with_valid_candidate(self):
        """Valid candidate windows should not raise."""
        _validate_inputs(ts(9), ts(17), 30, 0, 1, [], [iv(10, 0, 12, 0)])


# ═══════════════════════════════════════════════════════════════════════════════
#  INVARIANT CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

class TestInvariants:
    """Verify system invariants hold across varied inputs."""

    def test_slots_within_working_hours(self):
        result = recommend_slots(ts(10), ts(14), [iv(11, 0, 12, 0)], 30, 10, 0)
        for slot in result:
            s, e = slot.to_minutes()
            assert s >= ts(10).to_minutes()
            assert e <= ts(14).to_minutes()

    def test_slot_duration_ge_meeting_duration(self):
        dur = 45
        result = recommend_slots(ts(9), ts(17), [iv(10, 0, 11, 0), iv(13, 0, 14, 0)], dur, 10, 0)
        for slot in result:
            s, e = slot.to_minutes()
            assert (e - s) >= dur

    def test_slot_duration_equals_duration_plus_buffer(self):
        dur, buf = 30, 10
        result = recommend_slots(ts(9), ts(17), [], dur, 5, buf)
        for slot in result:
            s, e = slot.to_minutes()
            assert (e - s) == dur + buf

    def test_no_overlap_between_slots(self):
        result = recommend_slots(ts(8), ts(18), [iv(10, 0, 11, 0), iv(14, 0, 15, 0)], 30, 20, 10)
        for i in range(len(result) - 1):
            _, end_i = result[i].to_minutes()
            start_next, _ = result[i + 1].to_minutes()
            assert end_i <= start_next

    def test_no_overlap_with_busy(self):
        busy = [iv(10, 0, 11, 0), iv(13, 30, 14, 30)]
        result = recommend_slots(ts(9), ts(17), busy, 30, 10, 0)
        busy_mins = [(b.start.to_minutes(), b.end.to_minutes()) for b in busy]
        for slot in result:
            ss, se = slot.to_minutes()
            for bs, be in busy_mins:
                assert not (ss < be and se > bs)

    def test_deterministic_repeated_calls(self):
        kwargs = dict(
            work_start=ts(9), work_end=ts(17),
            busy_intervals=[iv(10, 0, 11, 0), iv(14, 0, 15, 0)],
            meeting_duration=30, n=8, buffer_time=5,
        )
        first = recommend_slots(**kwargs)
        for _ in range(10):
            assert recommend_slots(**kwargs) == first

    def test_output_sorted_chronologically(self):
        result = recommend_slots(
            ts(8), ts(20),
            [iv(9, 0, 10, 0), iv(12, 0, 13, 0), iv(16, 0, 17, 0)],
            45, 10, 5,
        )
        for i in range(len(result) - 1):
            assert result[i].start.to_minutes() < result[i + 1].start.to_minutes()


# ═══════════════════════════════════════════════════════════════════════════════
#  TIE-BREAKING RULE CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def test_tie_chronological_first():
    """Rule #1: prefer the chronologically earliest slot."""
    result = recommend_slots(
        ts(9), ts(17),
        [iv(9, 0, 11, 0), iv(12, 0, 14, 30), iv(15, 30, 17, 0)],
        60, 1, 0,
    )
    assert result == [iv(11, 0, 12, 0)]


def test_tie_fill_from_gap_start():
    """Rule #2: fill from start of a gap, not the middle."""
    result = recommend_slots(ts(9), ts(17), [iv(9, 0, 13, 0)], 30, 3, 15)
    # Busy expands to (9:00, 13:15). slot_block=45.
    assert result == [iv(13, 15, 14, 0), iv(14, 0, 14, 45), iv(14, 45, 15, 30)]


def test_tie_no_workload_spreading():
    """Rule #3: first available slot chosen even if a larger gap exists later."""
    result = recommend_slots(
        ts(9), ts(17),
        [iv(9, 0, 11, 30), iv(12, 0, 14, 0)],
        30, 1, 0,
    )
    assert result == [iv(11, 30, 12, 0)]


def test_tie_first_gap_used_not_biggest():
    """System picks the first gap, not the largest."""
    result = recommend_slots(
        ts(9), ts(17),
        [iv(9, 30, 10, 0), iv(10, 30, 15, 0)],
        30, 1, 0,
    )
    assert result == [iv(9, 0, 9, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  NEGATIVE REQUIREMENT CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def test_neg_no_slot_outside_working_hours():
    result = recommend_slots(ts(10), ts(12), [], 30, 10, 0)
    for slot in result:
        s, e = slot.to_minutes()
        assert s >= ts(10).to_minutes()
        assert e <= ts(12).to_minutes()


def test_neg_no_short_slots():
    result = recommend_slots(
        ts(9), ts(12),
        [iv(9, 20, 9, 50), iv(10, 10, 10, 50)],
        30, 5, 0,
    )
    for slot in result:
        s, e = slot.to_minutes()
        assert (e - s) >= 30


def test_neg_no_slot_overlapping_busy():
    busy = [iv(10, 0, 11, 0)]
    result = recommend_slots(ts(9), ts(12), busy, 30, 10, 0)
    for slot in result:
        ss, se = slot.to_minutes()
        assert not (ss < 660 and se > 600)


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCTIONAL REQUIREMENT CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFunctionalRequirements:
    """Tests mapping directly to each functional requirement."""

    def test_fr_accepts_start_time(self):
        """FR: system shall accept a start time in 24h format."""
        result = recommend_slots(ts(6, 30), ts(17), [], 60, 1, 0)
        assert result[0].start == ts(6, 30)

    def test_fr_accepts_end_time(self):
        """FR: system shall accept an end time in 24h format."""
        result = recommend_slots(ts(9), ts(22, 0), [], 60, 1, 0)
        assert result[0].end.to_minutes() <= ts(22, 0).to_minutes()

    def test_fr_accepts_busy_intervals(self):
        """FR: system shall accept a list of busy intervals."""
        result = recommend_slots(ts(9), ts(12), [iv(9, 0, 10, 0), iv(11, 0, 11, 30)], 30, 1, 0)
        assert result[0] == iv(10, 0, 10, 30)

    def test_fr_accepts_meeting_duration(self):
        """FR: system shall accept a meeting duration."""
        result = recommend_slots(ts(9), ts(10), [], 15, 4, 0)
        for slot in result:
            s, e = slot.to_minutes()
            assert (e - s) == 15

    def test_fr_accepts_buffer_time(self):
        """FR: system shall accept an optional buffer time."""
        result = recommend_slots(ts(9), ts(12), [], 30, 2, buffer_time=20)
        assert result[0] == iv(9, 0, 9, 50)
        assert result[1] == iv(9, 50, 10, 40)

    def test_fr_buffer_default_zero(self):
        """FR: buffer time defaults to 0."""
        result = recommend_slots(ts(9), ts(10), [], 30, 2)
        assert result == [iv(9, 0, 9, 30), iv(9, 30, 10, 0)]

    def test_fr_accepts_candidate_time(self):
        """FR: system shall accept optional candidate time."""
        result = recommend_slots(
            ts(9), ts(17), [], 30, 2, 0,
            candidate_windows=[iv(14, 0, 16, 0)],
        )
        for slot in result:
            assert slot.start.to_minutes() >= ts(14).to_minutes()
            assert slot.end.to_minutes() <= ts(16).to_minutes()

    def test_fr_accepts_n(self):
        """FR: system shall accept total number of meeting slots N."""
        result = recommend_slots(ts(9), ts(17), [], 30, 5, 0)
        assert len(result) == 5

    def test_fr_returns_chronologically_sorted(self):
        """FR: output is chronologically sorted in 24h format."""
        result = recommend_slots(
            ts(8), ts(18),
            [iv(10, 0, 12, 0), iv(15, 0, 16, 0)],
            60, 5, 0,
        )
        times = [slot.start.to_minutes() for slot in result]
        assert times == sorted(times)

    def test_fr_busy_sorted_internally(self):
        """FR: system must sort busy intervals if not already sorted."""
        result_sorted = recommend_slots(
            ts(9), ts(12),
            [iv(9, 30, 10, 0), iv(10, 0, 10, 30)],
            30, 3, 0,
        )
        result_unsorted = recommend_slots(
            ts(9), ts(12),
            [iv(10, 0, 10, 30), iv(9, 30, 10, 0)],
            30, 3, 0,
        )
        assert result_sorted == result_unsorted


# ═══════════════════════════════════════════════════════════════════════════════
#  BUFFER-SPECIFIC SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestBufferScenarios:
    """Detailed tests for buffer behaviour."""

    def test_buffer_after_busy_respected(self):
        """Buffer pushes slot past busy_end + buffer."""
        result = recommend_slots(ts(9), ts(12), [iv(9, 0, 9, 30)], 30, 1, 15)
        assert result == [iv(9, 45, 10, 30)]

    def test_buffer_between_consecutive_slots(self):
        """Consecutive slots include buffer in their duration."""
        result = recommend_slots(ts(9), ts(12), [], 30, 3, 10)
        assert result == [iv(9, 0, 9, 40), iv(9, 40, 10, 20), iv(10, 20, 11, 0)]

    def test_large_buffer_eliminates_all_slots(self):
        """Very large buffer leaves no room for any slot."""
        result = recommend_slots(ts(9), ts(10), [], 30, 1, 60)
        # slot_block=90 > 60-min window
        assert result == []

    def test_buffer_after_multiple_busy(self):
        """Buffer applies after every busy interval."""
        # busy: 9:00–9:30, 10:00–10:30.  buffer=15
        # expanded: 9:00–9:45, 10:00–10:45
        # gaps: 9:45–10:00 (15m too small for 30+15=45), 10:45–12:00 (75m)
        result = recommend_slots(
            ts(9), ts(12),
            [iv(9, 0, 9, 30), iv(10, 0, 10, 30)],
            30, 1, 15,
        )
        assert result == [iv(10, 45, 11, 30)]

    def test_buffer_zero_no_gap_between_slots(self):
        """With buffer=0, slots are placed back-to-back."""
        result = recommend_slots(ts(9), ts(11), [], 30, 4, 0)
        assert result == [
            iv(9, 0, 9, 30), iv(9, 30, 10, 0),
            iv(10, 0, 10, 30), iv(10, 30, 11, 0),
        ]

    def test_buffer_exact_fit_in_gap(self):
        """Slot block fits exactly in the gap."""
        # Gap: 9:00–10:00 = 60 min.  dur=30 + buf=30 = 60 → exactly 1 slot
        result = recommend_slots(ts(9), ts(12), [iv(10, 0, 12, 0)], 30, 5, 30)
        assert result == [iv(9, 0, 10, 0)]


# ═══════════════════════════════════════════════════════════════════════════════
#  CANDIDATE WINDOW SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCandidateWindows:
    """Tests for candidate-window filtering behaviour."""

    def test_candidate_none_uses_full_working_hours(self):
        """No candidate window → full working hours available."""
        result = recommend_slots(ts(9), ts(17), [], 60, 1, 0, candidate_windows=None)
        assert result[0] == iv(9, 0, 10, 0)

    def test_candidate_empty_list_uses_full_working_hours(self):
        """Empty candidate list treated like None."""
        result = recommend_slots(ts(9), ts(17), [], 60, 1, 0, candidate_windows=[])
        assert result[0] == iv(9, 0, 10, 0)

    def test_single_candidate_restricts_slots(self):
        result = recommend_slots(
            ts(9), ts(17), [], 30, 3, 0,
            candidate_windows=[iv(12, 0, 14, 0)],
        )
        for slot in result:
            assert slot.start.to_minutes() >= 720
            assert slot.end.to_minutes() <= 840

    def test_multiple_candidate_windows(self):
        result = recommend_slots(
            ts(9), ts(17), [], 30, 4, 0,
            candidate_windows=[iv(9, 0, 10, 0), iv(14, 0, 15, 0)],
        )
        assert result == [
            iv(9, 0, 9, 30), iv(9, 30, 10, 0),
            iv(14, 0, 14, 30), iv(14, 30, 15, 0),
        ]

    def test_candidate_with_busy_inside(self):
        """Busy interval within candidate window reduces available time."""
        result = recommend_slots(
            ts(9), ts(17),
            [iv(12, 30, 13, 0)],
            30, 3, 0,
            candidate_windows=[iv(12, 0, 14, 0)],
        )
        assert result == [iv(12, 0, 12, 30), iv(13, 0, 13, 30), iv(13, 30, 14, 0)]

    def test_candidate_outside_working_hours_yields_nothing(self):
        """Candidate window entirely outside working hours → no slots."""
        result = recommend_slots(
            ts(9), ts(12), [], 30, 3, 0,
            candidate_windows=[iv(14, 0, 16, 0)],
        )
        assert result == []

    def test_candidate_partially_inside_working_hours(self):
        """Candidate window partially overlapping working hours is clipped."""
        result = recommend_slots(
            ts(9), ts(12), [], 30, 2, 0,
            candidate_windows=[iv(11, 0, 14, 0)],
        )
        # Effective candidate within work: 11:00–12:00
        assert result == [iv(11, 0, 11, 30), iv(11, 30, 12, 0)]

    def test_overlapping_candidate_windows_merged(self):
        """Overlapping candidate windows are merged."""
        result = recommend_slots(
            ts(9), ts(17), [], 60, 3, 0,
            candidate_windows=[iv(10, 0, 12, 0), iv(11, 0, 14, 0)],
        )
        # Merged candidate: 10:00–14:00
        assert result == [iv(10, 0, 11, 0), iv(11, 0, 12, 0), iv(12, 0, 13, 0)]


# ═══════════════════════════════════════════════════════════════════════════════
#  BUSY INTERVAL HANDLING (outside / partial / complex)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBusyIntervalHandling:
    """Tests for busy intervals that are outside, partial, or complex."""

    def test_busy_fully_before_working_hours_ignored(self):
        result = recommend_slots(ts(9), ts(12), [iv(7, 0, 8, 0)], 60, 3, 0)
        assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]

    def test_busy_fully_after_working_hours_ignored(self):
        result = recommend_slots(ts(9), ts(12), [iv(13, 0, 14, 0)], 60, 3, 0)
        assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]

    def test_busy_starts_before_work_ends_inside(self):
        result = recommend_slots(ts(9), ts(12), [iv(8, 0, 10, 0)], 30, 1, 0)
        assert result == [iv(10, 0, 10, 30)]

    def test_busy_starts_inside_ends_after_work(self):
        result = recommend_slots(ts(9), ts(12), [iv(11, 0, 14, 0)], 60, 1, 0)
        assert result == [iv(9, 0, 10, 0)]

    def test_busy_spans_entire_working_window(self):
        result = recommend_slots(ts(9), ts(12), [iv(8, 0, 14, 0)], 30, 1, 0)
        assert result == []

    def test_many_busy_intervals(self):
        """Many non-overlapping busy intervals."""
        busy = [iv(9, 0 + i * 30, 9, 15 + i * 30) for i in range(6)]
        # busy: 9:00–9:15, 9:30–9:45, 10:00–10:15, 10:30–10:45, 11:00–11:15, 11:30–11:45
        result = recommend_slots(ts(9), ts(12), busy, 15, 10, 0)
        # gaps: 9:15–9:30(15m), 9:45–10:00(15m), 10:15–10:30(15m),
        #        10:45–11:00(15m), 11:15–11:30(15m), 11:45–12:00(15m)
        assert len(result) == 6

    def test_three_overlapping_busy(self):
        """Three mutually overlapping intervals merge into one."""
        result = recommend_slots(
            ts(9), ts(14),
            [iv(10, 0, 11, 30), iv(10, 30, 12, 0), iv(11, 0, 12, 30)],
            30, 1, 0,
        )
        # Merged: 10:00–12:30.  First slot at 9:00.
        assert result == [iv(9, 0, 9, 30)]


# ═══════════════════════════════════════════════════════════════════════════════
#  MISCELLANEOUS / STRESS / BOUNDARY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMiscellaneous:
    """Boundary, stress, and miscellaneous tests."""

    def test_full_day_no_busy(self):
        """Full day (0:00–23:59) with no busy intervals."""
        result = recommend_slots(ts(0, 0), ts(23, 59), [], 60, 24, 0)
        # 23 hrs 59 min = 1439 min. 1439 // 60 = 23 full slots.
        assert len(result) == 23

    def test_single_minute_meeting(self):
        """1-minute meeting in a 1-minute window."""
        result = recommend_slots(ts(9, 0), ts(9, 1), [], 1, 1, 0)
        assert result == [Interval(ts(9, 0), ts(9, 1))]

    def test_n_larger_than_possible(self):
        """N much larger than available slots returns as many as fit."""
        result = recommend_slots(ts(9), ts(10), [], 30, 100, 0)
        assert len(result) == 2

    def test_exact_n_slots_fit(self):
        """Exactly N slots fit in the window."""
        result = recommend_slots(ts(9), ts(11), [], 60, 2, 0)
        assert len(result) == 2

    def test_slot_does_not_exceed_working_hours(self):
        """Slot must fit entirely within working hours."""
        result = recommend_slots(ts(9), ts(9, 45), [], 60, 1, 0)
        assert result == []

    def test_early_morning_window(self):
        """Working hours starting at midnight."""
        result = recommend_slots(ts(0, 0), ts(2, 0), [], 30, 4, 0)
        assert len(result) == 4

    def test_late_night_window(self):
        """Working hours ending near midnight."""
        result = recommend_slots(ts(22, 0), ts(23, 59), [], 30, 3, 0)
        assert len(result) == 3

    def test_many_small_slots(self):
        """Lots of 5-minute meetings across a full day."""
        result = recommend_slots(ts(0, 0), ts(23, 59), [], 5, 200, 0)
        # 1439 min // 5 = 287 slots possible, but N=200
        assert len(result) == 200

    def test_buffer_larger_than_duration(self):
        """Buffer can be larger than meeting duration."""
        result = recommend_slots(ts(9), ts(12), [], 10, 3, 50)
        # slot_block = 60
        assert result == [iv(9, 0, 10, 0), iv(10, 0, 11, 0), iv(11, 0, 12, 0)]

    def test_combined_busy_buffer_candidate(self):
        """All features combined: busy, buffer, candidate windows."""
        result = recommend_slots(
            ts(8), ts(18),
            [iv(9, 0, 10, 0), iv(13, 0, 14, 0)],
            30, 3, 10,
            candidate_windows=[iv(10, 0, 12, 0), iv(14, 0, 16, 0)],
        )
        # Busy expanded: 9:00–10:10, 13:00–14:10
        # Free: 8:00–9:00, 10:10–13:00, 14:10–18:00
        # Intersect with candidates: 10:10–12:00, 14:10–16:00
        # slot_block = 40
        # From 10:10: 10:10–10:50, 10:50–11:30, 11:30–12:10(>12:00 nope) → 2 in first
        # Need 1 more from 14:10–16:00: 14:10–14:50
        assert len(result) == 3
        assert result[0] == iv(10, 10, 10, 50)
        assert result[1] == iv(10, 50, 11, 30)
        assert result[2] == iv(14, 10, 14, 50)