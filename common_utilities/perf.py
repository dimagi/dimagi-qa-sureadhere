"""Lightweight performance budgets for the smoke suite.

Each `perf_budget(...)` block times the code it wraps and raises loudly
(AssertionError) if it runs slower than the allotted budget. Every measurement
(pass or fail) is also appended to a per-environment JSONL file so it can be
folded into the Slack step-checklist report by conftest.py.
"""

import json
import os
import time
from pathlib import Path

from common_utilities.path_settings import PathSettings

# Generous default budgets (seconds) for known-slow, meaningful actions.
# These are intentionally loose so normal CI variance doesn't trip them --
# they exist to catch real regressions (multiples of normal), not to police
# every second. This suite relies heavily on fixed time.sleep() calls for UI
# stability (e.g. PatientProfilePage.verify_patient_profile_page() alone
# sleeps 15s), so "normal" is already slow -- a live CI run measured
# create_regimen at ~73-75s doing nothing wrong, which is why that budget
# (and the untested edit_regimen, which does similar calendar-verification
# work) are set well above their apparent baseline. Tighten these later once
# slack_perf_<env>.jsonl has real historical data to tune against.
DEFAULT_BUDGETS = {
    "login_and_dashboard": 150,
    "create_patient": 100,
    "create_regimen": 150,
    "edit_regimen": 180,
    "mobile_video_submit": 300,
    "in_app_message_roundtrip": 180,
}

# Total smoke-suite wall clock budget per environment, checked once at the end
# of the run (see conftest.py::pytest_terminal_summary). Recent main-branch
# CI runs (gh run list) took ~48-50 minutes end to end even before this
# work, so this only covers the pytest-only portion (excludes dependency
# install/tesseract setup) but is still set with real headroom above that.
SUITE_DURATION_BUDGET_SECONDS = 75 * 60


def _perf_log_path(env: str) -> Path:
    return Path(PathSettings.ROOT) / f"slack_perf_{env}.jsonl"


def _current_env() -> str:
    return os.environ.get("DIMAGIQA_ENV", "default_env")


def record_perf(key: str, elapsed_s: float, budget_s: float, passed: bool, env: str | None = None) -> None:
    env = env or _current_env()
    entry = {
        "key": key,
        "elapsed_s": round(elapsed_s, 2),
        "budget_s": budget_s,
        "passed": bool(passed),
        "ts": time.time(),
    }
    line = json.dumps(entry)
    # A single small write() to a file opened with O_APPEND is atomic on
    # Linux for lines well under PIPE_BUF (4096 bytes), so this is safe to
    # call concurrently from multiple pytest-xdist worker processes without
    # an extra file-locking dependency.
    with open(_perf_log_path(env), "a", encoding="utf-8") as f:
        f.write(line + "\n")


class perf_budget:
    """Context manager: times a block, fails loudly if it exceeds threshold_s.

    Usage:
        with perf_budget("create_patient"):
            ...do the slow thing...
    """

    def __init__(self, key: str, threshold_s: float | None = None, env: str | None = None):
        self.key = key
        self.threshold_s = threshold_s if threshold_s is not None else DEFAULT_BUDGETS.get(key)
        if self.threshold_s is None:
            raise ValueError(f"No default budget registered for '{key}'; pass threshold_s explicitly")
        self.env = env
        self._t0 = None

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self._t0
        # Only judge performance if the wrapped block actually succeeded --
        # a functional failure should surface as its own (functional) step,
        # not get muddied with a misleading performance verdict.
        if exc_type is not None:
            return False
        passed = elapsed <= self.threshold_s
        record_perf(self.key, elapsed, self.threshold_s, passed, env=self.env)
        if not passed:
            raise AssertionError(
                f"[PERF] '{self.key}' took {elapsed:.1f}s, exceeding the {self.threshold_s:.0f}s budget"
            )
        return False


def read_perf_results(env: str) -> list[dict]:
    path = _perf_log_path(env)
    if not path.exists():
        return []
    results = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results
