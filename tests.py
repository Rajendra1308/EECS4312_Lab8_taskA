import pytest
from datetime import date, datetime, time, timedelta

# Update import path to match your project structure:
from solution import TimeWindow, BusyInterval, Slot, suggest_slots


# ---------- Helpers ----------

def combine(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def in_window(win: TimeWindow, t: time) -> bool:
    return win.start <= t < win.end


def assert_slots_basic_constraints(
    slots,
    day,
    working_hours,
    busy_intervals,
    duration,
    n,
    buffer,
    candidate_window,
):
    # Return type / length
    assert isinstance(slots, list)
    assert len(slots) <= n

    # Deterministic ordering: start_time ascending
    assert slots == sorted(slots, key=lambda s: s.start_time)

    # Each slot start must be within working_hours and candidate_window (if any)
    for s in slots:
        assert in_window(working_hours, s.start_time)
        if candidate_window is not None:
            assert in_window(candidate_window, s.start_time)

    # Each slot must fit fully inside working_hours and candidate_window
    for s in slots:
        start_dt = combine(day, s.start_time)
        end_dt = start_dt + duration

        wh_end = combine(day, working_hours.end)
        assert end_dt <= wh_end

        if candidate_window is not None:
            cw_end = combine(day, candidate_window.end)
            assert end_dt <= cw_end

    # No overlap with busy intervals, considering buffer:
    # busy interval is expanded to [start-buffer, end+buffer)
    for s in slots:
        slot_start = combine(day, s.start_time)
        slot_end = slot_start + duration

        for b in busy_intervals:
            b_start = combine(day, b.start) - buffer
            b_end = combine(day, b.end) + buffer
            assert not overlaps(slot_start, slot_end, b_start, b_end)


# ---------- Tests ----------

def test_a1_no_busy_simple_slots():
    """
    Like original "single med exact times": here, no busy events.
    Expect earliest slots within working hours (we only assert constraints + non-empty).
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(
        day=day,
        working_hours=working,
        busy_intervals=busy,
        duration=duration,
        n=3,
        buffer=timedelta(0),
        candidate_window=None
    )

    assert_slots_basic_constraints(out, day, working, busy, duration, 3, timedelta(0), None)
    # Should at least return 1 slot if implementation uses a reasonable slot step
    assert len(out) > 0
    # Earliest slot should be at or after working start
    assert out[0].start_time >= time(9, 0)


def test_a2_deterministic_same_inputs_same_outputs():
    """
    Like original tie/determinism check: same inputs must return identical outputs.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [
        BusyInterval(time(10, 0), time(10, 30)),
        BusyInterval(time(13, 0), time(14, 0)),
    ]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=0)

    out1 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)
    out2 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)

    assert [s.start_time for s in out1] == [s.start_time for s in out2]
    assert_slots_basic_constraints(out1, day, working, busy, duration, 10, buffer, None)


def test_a3_overlapping_and_unsorted_busy_intervals_handled():
    """
    Busy intervals may be unsorted/overlapping; suggestions must still avoid conflicts.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(10, 30), time(11, 0)),
        BusyInterval(time(10, 0), time(10, 45)),   # overlaps with above
        BusyInterval(time(9, 30), time(9, 45)),    # unsorted relative order
    ]
    duration = timedelta(minutes=15)

    out = suggest_slots(day, working, busy, duration, n=8, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out, day, working, busy, duration, 8, timedelta(0), None)


def test_a4_candidate_window_respected():
    """
    Like original allowed_window respected: here we add an extra candidate window restriction.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(13, 0), time(15, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5, buffer=timedelta(0), candidate_window=candidate)
    assert_slots_basic_constraints(out, day, working, busy, duration, 5, timedelta(0), candidate)

    # Every slot must start within candidate window
    assert all(candidate.start <= s.start_time < candidate.end for s in out)


def test_a5_buffer_eliminates_small_gaps():
    """
    Like original rate-limit constraint: here buffer is the key extra constraint.
    With buffer, some slots that would otherwise fit should be invalid.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(11, 0))
    # Two busy intervals leaving a 20-minute gap between them
    busy = [
        BusyInterval(time(9, 30), time(9, 50)),
        BusyInterval(time(10, 10), time(10, 30)),
    ]
    duration = timedelta(minutes=20)

    # Without buffer: the gap 9:50–10:10 is exactly 20 minutes -> potentially valid
    out_no_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out_no_buffer, day, working, busy, duration, 10, timedelta(0), None)

    # With 5-min buffer: effective busy expands, gap shrinks -> should reduce or remove those slots
    buf = timedelta(minutes=5)
    out_with_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=buf, candidate_window=None)
    assert_slots_basic_constraints(out_with_buffer, day, working, busy, duration, 10, buf, None)

    # Buffer should not increase number of available slots (monotonicity)
    assert len(out_with_buffer) <= len(out_no_buffer)


#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
################################################################################## 
# ---------------- Acceptance Criteria Explicit Tests ----------------

def test_ac1_full_busy_no_slots():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))
    busy = [BusyInterval(time(9, 0), time(10, 0))]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5, buffer=timedelta(0), candidate_window=None)

    assert out == []


def test_ac2_simple_sequential_slots():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = []
    duration = timedelta(minutes=60)

    out = suggest_slots(day, working, busy, duration, n=3, buffer=timedelta(0), candidate_window=None)

    assert [s.start_time for s in out] == [
        time(9, 0),
        time(10, 0),
        time(11, 0),
    ]


def test_ac3_busy_blocks_middle():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [BusyInterval(time(10, 0), time(11, 0))]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=3, buffer=timedelta(0), candidate_window=None)

    assert [s.start_time for s in out] == [
        time(9, 0),
        time(9, 30),
        time(11, 0),
    ]


def test_ac4_candidate_window_intersection():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(12, 0), time(14, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=3, buffer=timedelta(0), candidate_window=candidate)

    assert [s.start_time for s in out] == [
        time(12, 0),
        time(12, 30),
        time(13, 0),
    ]


def test_ac6_unsorted_busy_intervals():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(10, 0), time(10, 30)),
        BusyInterval(time(9, 30), time(10, 0)),  # unsorted
    ]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1, buffer=timedelta(0), candidate_window=None)

    assert [s.start_time for s in out] == [time(9, 0)]


def test_ac7_buffer_respected():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [BusyInterval(time(10, 0), time(11, 0))]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=10)

    out = suggest_slots(day, working, busy, duration, n=1, buffer=buffer, candidate_window=None)

    # 9:00–9:30 meeting occupies until 9:40 because of buffer
    assert [s.start_time for s in out] == [time(9, 0)]


def test_ac9_overlapping_busy_intervals_merged():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(9, 0), time(10, 30)),
        BusyInterval(time(10, 0), time(11, 0)),  # overlaps
    ]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1, buffer=timedelta(0), candidate_window=None)

    assert [s.start_time for s in out] == [time(11, 0)]


# ---------------- Validation & Edge Cases ----------------

def test_invalid_working_hours_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(10, 0), time(9, 0))  # invalid

    with pytest.raises(ValueError):
        suggest_slots(day, working, [], timedelta(minutes=30), n=1)


def test_zero_duration_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))

    with pytest.raises(ValueError):
        suggest_slots(day, working, [], timedelta(0), n=1)


def test_negative_buffer_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))

    with pytest.raises(ValueError):
        suggest_slots(day, working, [], timedelta(minutes=30), n=1, buffer=timedelta(minutes=-5))


def test_n_zero_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))

    with pytest.raises(ValueError):
        suggest_slots(day, working, [], timedelta(minutes=30), n=0)

def test_fallback_to_shorter_gap_when_no_full_duration():
    """
    No 30-min gap exists, but smaller gaps exist.
    Should return up to N maximum shorter gaps.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))
    busy = [
        BusyInterval(time(9, 10), time(9, 40)),
        BusyInterval(time(9, 50), time(10, 0)),
    ]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=2, buffer=timedelta(0), candidate_window=None)

    # Only small gaps exist: 9:00–9:10 and 9:40–9:50
    assert len(out) > 0
    assert out[0].start_time == time(9, 0)


def test_candidate_window_no_overlap_with_working():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))
    candidate = TimeWindow(time(11, 0), time(12, 0))

    out = suggest_slots(day, working, [], timedelta(minutes=30), n=5, candidate_window=candidate)

    assert out == []
def test_invalid_candidate_window_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(14, 0), time(12, 0))  # invalid

    with pytest.raises(ValueError):
        suggest_slots(day, working, [], timedelta(minutes=30), n=1, candidate_window=candidate)
def test_invalid_busy_interval_raises():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [BusyInterval(time(10, 0), time(9, 30))]  # invalid

    with pytest.raises(ValueError):
        suggest_slots(day, working, busy, timedelta(minutes=30), n=1)
def test_busy_outside_working_ignored():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))

    busy = [
        BusyInterval(time(7, 0), time(8, 0)),   # fully before
        BusyInterval(time(13, 0), time(14, 0)), # fully after
    ]

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=2)

    assert [s.start_time for s in out] == [time(9, 0), time(9, 30)]

def test_candidate_partially_outside_working():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(8, 0), time(10, 0))  # overlaps partially

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=2, candidate_window=candidate)

    # Effective window should be 9:00–10:00
    assert [s.start_time for s in out] == [time(9, 0), time(9, 30)]
def test_returned_slots_do_not_overlap_each_other():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(11, 0))

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=10)

    for i in range(len(out) - 1):
        start1 = combine(day, out[i].start_time)
        end1 = start1 + duration

        start2 = combine(day, out[i+1].start_time)

        assert end1 <= start2
def test_n_larger_than_possible_slots():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(10, 0))
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=10)

    # Only 2 possible slots
    assert len(out) == 2

def test_buffer_eliminates_all_slots():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [BusyInterval(time(10, 0), time(10, 30))]
    duration = timedelta(minutes=30)

    # Large buffer wipes out availability
    out = suggest_slots(day, working, busy, duration, n=5, buffer=timedelta(hours=2))

    assert out == []
def test_tie_breaking_chronology():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [BusyInterval(time(9, 0), time(11, 30))]

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1)

    # First available slot is 11:30
    assert out[0].start_time == time(11, 30)
def test_sequential_gap_filling():
    day = date(2026, 2, 24)
    working = TimeWindow(time(13, 0), time(16, 0))

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=4)

    assert [s.start_time for s in out] == [
        time(13, 0),
        time(13, 30),
        time(14, 0),
        time(14, 30),
    ]
def test_fallback_only_when_no_full_duration():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(9, 20))
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=3)

    # No full-duration slot possible
    assert len(out) == 1
    assert out[0].start_time == time(9, 0)


#################################################################################
# Additional Edge Case Tests (not already covered above)
#################################################################################

def test_meeting_can_end_exactly_when_busy_starts():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(11, 0))

    busy = [BusyInterval(time(10, 0), time(11, 0))]
    duration = timedelta(minutes=60)

    out = suggest_slots(day, working, busy, duration, n=1)

    # 9:00–10:00 should be allowed
    assert out[0].start_time == time(9, 0)


def test_meeting_can_start_exactly_when_busy_ends():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))

    busy = [BusyInterval(time(9, 0), time(10, 0))]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1)

    # Meeting should start exactly when busy interval ends
    assert out[0].start_time == time(10, 0)


def test_busy_partially_outside_working_trimmed():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))

    busy = [
        BusyInterval(time(8, 30), time(9, 30))  # partially overlaps working window
    ]

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1)

    # First valid slot should start after 9:30
    assert out[0].start_time == time(9, 30)


def test_adjacent_busy_intervals_merge():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))

    busy = [
        BusyInterval(time(9, 0), time(10, 0)),
        BusyInterval(time(10, 0), time(11, 0)),  # touches previous interval
    ]

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=1)

    # merged interval should block until 11
    assert out[0].start_time == time(11, 0)


def test_duration_exceeds_working_window():
    day = date(2026, 2, 24)

    working = TimeWindow(time(9, 0), time(10, 0))
    duration = timedelta(hours=2)

    out = suggest_slots(day, working, [], duration, n=3)

    # No full-duration slot possible, fallback should return the start of the gap
    assert len(out) == 1
    assert out[0].start_time == time(9, 0)


def test_candidate_window_equals_working_window():
    day = date(2026, 2, 24)

    working = TimeWindow(time(9, 0), time(12, 0))
    candidate = TimeWindow(time(9, 0), time(12, 0))

    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, [], duration, n=2, candidate_window=candidate)

    assert [s.start_time for s in out] == [
        time(9, 0),
        time(9, 30),
    ]


def test_buffer_pushes_slot_outside_working_window():
    day = date(2026, 2, 24)

    working = TimeWindow(time(9, 0), time(10, 0))

    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=40)

    out = suggest_slots(day, working, [], duration, n=3, buffer=buffer)

    # Only first slot should be valid
    assert out == [Slot(start_time=time(9, 0))]


def test_exact_gap_equal_to_duration():
    day = date(2026, 2, 24)

    working = TimeWindow(time(9, 0), time(12, 0))

    busy = [
        BusyInterval(time(9, 30), time(10, 30))
    ]

    duration = timedelta(hours=1)

    out = suggest_slots(day, working, busy, duration, n=1)

    # 10:30–11:30 should be valid
    assert out[0].start_time == time(10, 30)


def test_many_busy_intervals_deterministic():
    day = date(2026, 2, 24)

    working = TimeWindow(time(9, 0), time(17, 0))

    busy = [
        BusyInterval(time(9, 30), time(10, 0)),
        BusyInterval(time(11, 0), time(11, 30)),
        BusyInterval(time(13, 0), time(13, 30)),
        BusyInterval(time(15, 0), time(15, 30)),
    ]

    duration = timedelta(minutes=30)

    out1 = suggest_slots(day, working, busy, duration, n=5)
    out2 = suggest_slots(day, working, busy, duration, n=5)

    assert out1 == out2

