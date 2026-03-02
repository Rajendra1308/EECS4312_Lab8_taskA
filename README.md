# Task A: Appointment Slot Recommender

## System Description

You are asked to implement Python functions that can recommend available meeting slots given working hours, busy intervals, meeting duration, optional buffer time, and a candidate window. The function must return chronologically ordered suggestions that fit within working hours and do not overlap busy intervals under buffering rules. It must handle edge cases such as adjacent intervals, tiny gaps, and buffers eliminating availability.

For full requirements, constraints, acceptance criteria, and edge cases, see `Appointment Scheduling System.md`.

## Structure

```
EECS4312_Lab8_taskA/
    Appointment Scheduling System.md   # System specification document
    LAB8_MANUAL_A.docx                 # Lab manual
    solution.py                        # Implementation (recommend_slots, TimeSlot, Interval)
    tests.py                           # Test cases (pytest)
    prompt_log.txt                     # Prompt log
    README.md                          # This file
```

- **solution.py** – Contains the `recommend_slots` function along with `TimeSlot` and `Interval` classes. Do not rename this file.
- **tests.py** – Test cases you can run to check correctness. Uses `pytest`.
- **Appointment Scheduling System.md** – Full specification including functional requirements, constraints, acceptance criteria, and edge cases.

## Running Tests

1. Install Python 3 if not already installed.
2. Implement your solution in `solution.py`.
3. Run tests using:

```bash
pytest tests.py -v
```

4. Fix any failing tests before moving on. Remember that hidden tests will check additional requirements.

---

## How to Run Test Cases

### 1. Install pytest

If you don't already have `pytest` installed, you can install it using pip:

```bash
pip install pytest
```

Verify the installation:

```bash
pytest --version
```

---

### 2. File Organization

Your implementation and test files should be in the same directory:

```
/project-folder
    solution.py    # your implementation
    tests.py       # your test cases
```

- `solution.py` contains the `recommend_slots` function, `TimeSlot`, and `Interval` classes.
- `tests.py` contains the test functions.

---

### 3. Import in Test File

In `tests.py`, the implementation is imported as:

```python
import pytest
from solution import TimeSlot, Interval, recommend_slots
```

---

### 4. Run All Tests

Navigate to the folder containing the files and run:

```bash
pytest tests.py
```

Or with more detailed output:

```bash
pytest tests.py -v
```

---

### 5. Run a Specific Test Function

To run a single test function, use the `-k` option:

```bash
pytest tests.py -v -k test_name
```

---

## Summary

1. Install `pytest`
2. Ensure `solution.py` and `tests.py` are in the same directory
3. Run all tests: `pytest tests.py -v`
4. Run a single test: `pytest tests.py -v -k <test_name>`
