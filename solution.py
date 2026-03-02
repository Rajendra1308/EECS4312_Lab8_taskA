## Student Name: Rajendra Brahmbhatt 
## Student ID: 217925157

"""
Task A: Medication Reminder Scheduler (Stub)

Implement a scheduler that generates medication reminders under user-defined constraints.

Inputs include:
  (i)  a list of medications with frequencies and permissible time windows,
  (ii) user quiet hours during which notifications must not occur,
  (iii) a maximum notification rate (no more than k reminders per hour),
  (iv) an optional snooze operation that shifts a reminder while preserving constraints.

The scheduler outputs the next N reminders in chronological order and must behave
deterministically under ties.
See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption (unless stated otherwise in handout): non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class Medication:
    """
    Medication definition.
      - name: unique medication name
      - every: frequency between reminders (e.g., timedelta(hours=8))
      - windows: allowed time windows during a day
    """
    name: str
    every: timedelta
    windows: Tuple[TimeWindow, ...]


@dataclass(frozen=True)
class Reminder:
    """
    A scheduled reminder.
    Deterministic ordering must be defined (e.g., sort by (when, med_name)).
    """
    when: datetime
    med_name: str


class InfeasibleSchedule(Exception):
    """Raised when constraints make scheduling impossible."""
    pass


class SnoozeViolation(Exception):
    """Raised when a snooze request cannot be satisfied under constraints."""
    pass


def next_reminders(
    start: datetime,
    meds: List[Medication],
    quiet_hours: Optional[TimeWindow],
    max_per_hour: int,
    n: int
) -> List[Reminder]:
    """
    Generate the next n reminders >= start.

    Args:
        start: starting datetime (inclusive).
        meds: list of medications to schedule.
        quiet_hours: daily quiet hours window where reminders must NOT occur (or None).
        max_per_hour: maximum reminders allowed per hour (k).
        n: number of reminders to output.

    Returns:
        A list of n reminders in chronological order with deterministic tie-breaking.

    Raises:
        InfeasibleSchedule: if it is impossible to schedule under constraints.
    """
    # TODO: Implement scheduling algorithm per lab handout
    raise NotImplementedError("next_reminders has not been implemented yet")


def snooze_reminder(
    reminders: List[Reminder],
    target: Reminder,
    snooze_by: timedelta,
    meds: List[Medication],
    quiet_hours: Optional[TimeWindow],
    max_per_hour: int
) -> List[Reminder]:
    """
    Apply a snooze operation to a previously scheduled reminder, and return an updated schedule.

    Args:
        reminders: current reminder list (chronological, deterministic).
        target: the reminder to snooze.
        snooze_by: timedelta to shift the reminder (typically forward).
        meds: medication definitions (same as scheduling).
        quiet_hours: quiet window (same as scheduling).
        max_per_hour: rate limit (same as scheduling).

    Returns:
        Updated reminders list that still satisfies all constraints and remains deterministic.

    Raises:
        SnoozeViolation or InfeasibleSchedule: if snooze cannot be satisfied.
    """
    # TODO: Implement snooze behavior per lab handout
    raise NotImplementedError("snooze_reminder has not been implemented yet")