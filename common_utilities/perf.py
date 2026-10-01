"""Lightweight performance budgets for the smoke suite.

Each `perf_budget(...)` block times the code it wraps. Every measurement
(pass or fail) is appended to a per-environment JSONL file so it can be
folded into the Slack step-checklist report by conftest.py. A breach is
recorded and reported at the end of the run (Summary: FAIL + non-zero exit
code) rather than raised mid-test, so a slow step doesn't abort the rest of
that test's functional checks or trigger a --reruns retry of the whole test.

Budgets are judged on the raw wall clock (elapsed_s). The big fixed
sleeps on the timed paths were there because the app really is slow to
load; they've been replaced with BasePage.wait_for_app_idle(), which waits
*up to* the same time but stops as soon as the app is idle, so elapsed_s
now tracks how long the app actually took. On top of that:

1. Fixed sleeps: time still spent in literal `time.sleep(<number>)` calls
   from this repo's own code during the block is recorded as
   fixed_sleep_s -- a diagnostic showing how much of a step is still
   hard-coded padding, not part of the pass/fail verdict.
2. API timings: when a `driver` is passed, the browser's own Resource
   Timing entries for XHR/fetch calls made during the block are recorded
   per endpoint (see collect_api_timings). conftest.py also does this per
   test for every web test. api_breaches() fails the run when a backend
   endpoint is consistently slow.
3. Trend vs history: if a perf_history.jsonl (the metrics branch's
   runs.jsonl, fetched by the workflow) is present, elapsed_s is compared
   to the median of recent runs and a slowdown is flagged as a warning.
"""

import json
import linecache
import math
import os
import re
import statistics
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from common_utilities.path_settings import PathSettings

# Generous default budgets (seconds) for known-slow, meaningful actions,
# judged against the raw wall clock (elapsed_s) as an absolute backstop.
# These are intentionally loose so normal CI variance doesn't trip them --
# they exist to catch real regressions (multiples of normal), not to police
# every second. This suite relies heavily on fixed time.sleep() calls for UI
# stability (e.g. PatientProfilePage.verify_patient_profile_page() alone
# sleeps 15s), so "normal" is already slow -- a live CI run measured
# create_regimen at ~73-75s doing nothing wrong, which is why that budget is
# set well above its apparent baseline. edit_regimen's budget was raised
# again (180s -> 280s) after real CI data showed it consistently landing
# right at ~180.2s on banner on both a first attempt and its rerun -- not a
# regression, just a budget with no real headroom over the actual baseline.
# Tighten these once the trend history (TREND_WARN_FACTOR below) shows
# what normal looks like now that the big fixed sleeps are bounded waits.
DEFAULT_BUDGETS = {
    "login_and_dashboard": 150,
    "create_patient": 100,
    "create_regimen": 150,
    "edit_regimen": 280,
    "mobile_video_submit": 300,
    "in_app_message_roundtrip": 180,
}

# Total smoke-suite wall clock budget per environment, checked once at the end
# of the run (see conftest.py::pytest_terminal_summary). Recent main-branch
# CI runs (gh run list) took ~48-50 minutes end to end even before this
# work, so this only covers the pytest-only portion (excludes dependency
# install/tesseract setup) but is still set with real headroom above that.
SUITE_DURATION_BUDGET_SECONDS = 75 * 60

# A step whose elapsed_s exceeds this multiple of its historical median is
# flagged as a trend warning (reported, never fails the run on its own).
TREND_WARN_FACTOR = 1.5
# Need at least this many historical samples before trusting a median.
TREND_MIN_SAMPLES = 5
# Only the most recent N historical samples per step feed the median.
TREND_WINDOW = 10

# Keys marked noisy (BrowserStack device/network dominated) are recorded and
# trend-checked but a budget breach is reported as a warning, not a failure.
NOISY_KEYS = {"mobile_video_submit"}

PERF_HISTORY_FILE = "perf_history.jsonl"

# Friendly names for the Slack performance block, in display order.
STEP_LABELS = {
    "login_and_dashboard": "Login to dashboard",
    "create_patient": "Create patient",
    "create_regimen": "Create regimen",
    "edit_regimen": "Edit regimen",
    "in_app_message_roundtrip": "In-app messaging round trip",
    "mobile_video_submit": "Mobile video submit",
}

# Backend API check (see api_breaches). Only endpoints with one of these
# path segments count as backend calls -- third-party scripts, telemetry
# and static files are ignored.
API_SERVICE_SEGMENTS = {"treatment", "iam", "reporting", "messaging", "merm", "session", "video", "vdot"}
# SignalR (in-app chat) can fall back to long-polling, whose requests stay
# open on purpose.
API_IGNORED_SEGMENTS = {"chathub", "negotiate", "signalr"}
# Fail when an endpoint called at least API_MIN_CALLS_FOR_P95 times has a
# p95 above API_P95_BUDGET_MS, or when any single call takes longer than
# API_SINGLE_CALL_BUDGET_MS.
API_P95_BUDGET_MS = 3000
API_MIN_CALLS_FOR_P95 = 3
API_SINGLE_CALL_BUDGET_MS = 10000


def _perf_log_path(env: str) -> Path:
    return Path(PathSettings.ROOT) / f"slack_perf_{env}.jsonl"


def _api_log_path(env: str) -> Path:
    return Path(PathSettings.ROOT) / f"slack_api_{env}.jsonl"


def api_summary_path(env: str) -> Path:
    return Path(PathSettings.ROOT) / f"perf_api_summary_{env}.json"


def _current_env() -> str:
    return os.environ.get("DIMAGIQA_ENV", "default_env")


def reset_perf_logs(env: str) -> None:
    """Clear this env's perf/API logs. Called once per pytest session on the
    xdist master, so local runs don't keep reporting old runs' breaches."""
    for path in (_perf_log_path(env), _api_log_path(env), api_summary_path(env)):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


# Set once per test by conftest.py's pytest_runtest_setup (item.name), so a
# perf_budget failure can be attributed to the test it happened in without
# every call site having to pass that in itself. Process-local is fine here
# -- each pytest-xdist worker only ever runs one test at a time.
_current_test_name = "unknown_test"


def set_current_test(name: str) -> None:
    global _current_test_name
    _current_test_name = name


def _append_line(path: Path, entry: dict) -> None:
    # A single small write() to a file opened with O_APPEND is atomic on
    # Linux for lines well under PIPE_BUF (4096 bytes), so this is safe to
    # call concurrently from multiple pytest-xdist worker processes without
    # an extra file-locking dependency. Callers keep each line small.
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
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


# ---------------------------------------------------------------------------
# Fixed-sleep accounting
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.normcase(os.path.abspath(PathSettings.ROOT))
_FIXED_SLEEP_RE = re.compile(r"\btime\.sleep\(\s*\d+(?:\.\d+)?\s*\)")
_real_sleep = time.sleep
_active_blocks: list["perf_budget"] = []
_fixed_sleep_site_cache: dict[tuple[str, int], bool] = {}


def _is_fixed_sleep_site(filename: str, lineno: int) -> bool:
    """True when the call site is this repo's own code (not .venv/site-
    packages) and the source line is a literal `time.sleep(<number>)`."""
    cache_key = (filename, lineno)
    cached = _fixed_sleep_site_cache.get(cache_key)
    if cached is not None:
        return cached
    path = os.path.normcase(os.path.abspath(filename))
    in_repo = (
        path.startswith(_REPO_ROOT)
        and "site-packages" not in path
        and f"{os.sep}.venv{os.sep}" not in path
    )
    result = bool(in_repo and _FIXED_SLEEP_RE.search(linecache.getline(filename, lineno)))
    _fixed_sleep_site_cache[cache_key] = result
    return result


def _tracking_sleep(seconds):
    if _active_blocks:
        caller = sys._getframe(1)
        if _is_fixed_sleep_site(caller.f_code.co_filename, caller.f_lineno):
            t0 = time.perf_counter()
            _real_sleep(seconds)
            slept = time.perf_counter() - t0
            for block in _active_blocks:
                block.fixed_sleep_s += slept
            return
    _real_sleep(seconds)


def _push_block(block: "perf_budget") -> None:
    if not _active_blocks:
        time.sleep = _tracking_sleep
    _active_blocks.append(block)


def _pop_block(block: "perf_budget") -> None:
    if block in _active_blocks:
        _active_blocks.remove(block)
    if not _active_blocks:
        time.sleep = _real_sleep


# ---------------------------------------------------------------------------
# Browser-side API timings (Resource Timing API)
# ---------------------------------------------------------------------------

# Returns [url, duration_ms] for every XHR/fetch entry since the previous
# call with the same mark name, then moves the mark. The mark lives on
# `window`, so a full page load (new document, new timeline) naturally
# resets it and everything in the new document is returned. `duration` is
# populated even for cross-origin API calls without a Timing-Allow-Origin
# header (only the detailed phase fields are zeroed), which is all we use.
_API_TIMINGS_JS = """
const mark = arguments[0];
const since = window[mark];
try { performance.setResourceTimingBufferSize(5000); } catch (e) {}
const out = performance.getEntriesByType('resource')
  .filter(e => (e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch')
               && (since === undefined || e.startTime >= since))
  .map(e => [e.name, Math.round(e.duration)]);
window[mark] = performance.now();
return out;
"""

# Query params that change what an endpoint actually does (e.g. the
# multiplexed /treatment/videos dashboard endpoint) are kept in the
# endpoint name; every other query param is dropped.
_DISCRIMINATING_PARAMS = ("SearchParamsType", "EntityName")
# This repo is public, so endpoint names end up in public CI logs,
# artifacts, the metrics branch and the GH Pages dashboard. Only plain word
# segments (e.g. "treatment", "patients", "GetByEmail") are kept; anything
# else -- ids, emails, names, MRNs, encoded values, tokens -- becomes {id}.
# Hosts and query values are never kept, except the enum-like values of
# _DISCRIMINATING_PARAMS, which must themselves be plain words.
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z][A-Za-z_-]{0,39}$")
_SAFE_QUERY_VALUE_RE = re.compile(r"^[A-Za-z_]{1,40}$")
# Keep each JSONL line well under PIPE_BUF (see _append_line).
_MAX_DURATIONS_PER_LINE = 100


def normalize_endpoint(url: str) -> str:
    parts = urlsplit(url)
    segments = [s if (not s or _SAFE_SEGMENT_RE.match(s)) else "{id}" for s in parts.path.split("/")]
    endpoint = "/".join(segments) or "/"
    query = parse_qs(parts.query)
    kept = [f"{p}={query[p][0]}" for p in _DISCRIMINATING_PARAMS
            if p in query and _SAFE_QUERY_VALUE_RE.match(query[p][0])]
    if kept:
        endpoint += "?" + "&".join(kept)
    return endpoint


def collect_api_timings(driver, scope: str, mark: str, env: str | None = None) -> int:
    """Record per-endpoint XHR/fetch durations the browser saw since the
    last collection with the same `mark`. Never raises -- a closed window,
    an open alert, or a non-browser driver just means no data. Returns the
    number of requests recorded."""
    if driver is None:
        return 0
    try:
        entries = driver.execute_script(_API_TIMINGS_JS, f"__qaPerfMark_{mark}") or []
    except Exception:
        return 0
    by_endpoint: dict[str, list[int]] = {}
    for url, duration_ms in entries:
        by_endpoint.setdefault(normalize_endpoint(url), []).append(int(duration_ms))
    env = env or _current_env()
    for endpoint, durations in by_endpoint.items():
        for i in range(0, len(durations), _MAX_DURATIONS_PER_LINE):
            _append_line(_api_log_path(env), {
                # "test" lines cover a whole test (conftest.py); "step" lines
                # are a perf_budget block's subset of the same calls.
                "level": "test" if mark == "test" else "step",
                "scope": scope,
                "test": _current_test_name,
                "endpoint": endpoint[:300],
                "durations_ms": durations[i:i + _MAX_DURATIONS_PER_LINE],
                "ts": time.time(),
            })
    return len(entries)


def _percentile(sorted_values: list, pct: float):
    """Nearest-rank percentile of an already-sorted, non-empty list."""
    rank = max(1, math.ceil(pct / 100 * len(sorted_values)))
    return sorted_values[min(rank, len(sorted_values)) - 1]


def summarize_api_timings(env: str) -> list[dict]:
    """Aggregate every recorded API call in this run into one row per
    endpoint, slowest p95 first. Uses the per-test lines only, since a
    perf_budget block's "step" lines are a duplicate subset of them (falls
    back to everything if no per-test lines were recorded)."""
    entries = _read_jsonl(_api_log_path(env))
    test_level = [e for e in entries if e.get("level") == "test"]
    by_endpoint: dict[str, list[int]] = {}
    for entry in test_level or entries:
        by_endpoint.setdefault(entry.get("endpoint", "?"), []).extend(entry.get("durations_ms", []))
    rows = []
    for endpoint, durations in by_endpoint.items():
        if not durations:
            continue
        values = sorted(durations)
        rows.append({
            "endpoint": endpoint,
            "n": len(values),
            "p50_ms": _percentile(values, 50),
            "p95_ms": _percentile(values, 95),
            "max_ms": values[-1],
        })
    rows.sort(key=lambda r: r["p95_ms"], reverse=True)
    return rows


def write_api_summary(env: str) -> list[dict]:
    rows = summarize_api_timings(env)
    with open(api_summary_path(env), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    return rows


def is_backend_endpoint(endpoint: str) -> bool:
    segments = {seg.lower() for seg in endpoint.split("?")[0].split("/") if seg}
    return bool(segments & API_SERVICE_SEGMENTS) and not (segments & API_IGNORED_SEGMENTS)


def api_breaches(rows: list[dict]) -> list[dict]:
    """Backend endpoints that breached the API budgets, each row annotated
    with a human-readable `reason`."""
    breaches = []
    for row in rows:
        if not is_backend_endpoint(row["endpoint"]):
            continue
        if row["n"] >= API_MIN_CALLS_FOR_P95 and row["p95_ms"] > API_P95_BUDGET_MS:
            reason = f"p95 {row['p95_ms'] / 1000:.1f}s over {row['n']} calls (limit {API_P95_BUDGET_MS / 1000:.0f}s)"
        elif row["max_ms"] > API_SINGLE_CALL_BUDGET_MS:
            reason = f"one call took {row['max_ms'] / 1000:.1f}s (limit {API_SINGLE_CALL_BUDGET_MS / 1000:.0f}s)"
        else:
            continue
        breaches.append(dict(row, reason=reason))
    return breaches


# ---------------------------------------------------------------------------
# Historical baseline
# ---------------------------------------------------------------------------

_baseline_cache: dict[str, dict[str, float]] = {}


def load_baseline(env: str) -> dict[str, float]:
    """Median elapsed_s per perf key over the last TREND_WINDOW runs for this
    env, from perf_history.jsonl (one run_summary.json object per line, as
    stored on the metrics branch). Keys with too few samples are omitted.
    Returns {} when there's no history file."""
    if env in _baseline_cache:
        return _baseline_cache[env]
    samples: dict[str, list[float]] = {}
    for run in _read_jsonl(Path(PathSettings.ROOT) / PERF_HISTORY_FILE):
        if run.get("env") != env:
            continue
        for entry in run.get("perf") or []:
            if entry.get("elapsed_s") is None or not entry.get("key"):
                continue
            samples.setdefault(entry["key"], []).append(float(entry["elapsed_s"]))
    baseline = {
        key: statistics.median(values[-TREND_WINDOW:])
        for key, values in samples.items()
        if len(values) >= TREND_MIN_SAMPLES
    }
    _baseline_cache[env] = baseline
    return baseline


# ---------------------------------------------------------------------------
# perf_budget
# ---------------------------------------------------------------------------

def record_perf(key: str, elapsed_s: float, budget_s: float, passed: bool, env: str | None = None,
                fixed_sleep_s: float = 0.0, **extra) -> dict:
    env = env or _current_env()
    entry = {
        "key": key,
        "test": _current_test_name,
        "elapsed_s": round(elapsed_s, 2),
        "fixed_sleep_s": round(fixed_sleep_s, 2),
        "budget_s": budget_s,
        "passed": bool(passed),
        "ts": time.time(),
    }
    entry.update(extra)
    _append_line(_perf_log_path(env), entry)
    return entry


class perf_budget:
    """Context manager: times a block and records whether it exceeded its
    budget. A breach is reported at the end of the run, not raised here,
    unless fail_fast=True.

    Usage:
        with perf_budget("create_patient", driver=self.driver):
            ...do the slow thing...
    """

    def __init__(self, key: str, threshold_s: float | None = None, env: str | None = None,
                 driver=None, fail_fast: bool = False):
        self.key = key
        self.threshold_s = threshold_s if threshold_s is not None else DEFAULT_BUDGETS.get(key)
        if self.threshold_s is None:
            raise ValueError(f"No default budget registered for '{key}'; pass threshold_s explicitly")
        self.env = env
        self.driver = driver
        self.fail_fast = fail_fast
        self.fixed_sleep_s = 0.0
        self._t0 = None

    def __enter__(self):
        if self.driver is not None:
            # Moves this block's mark to "now" so only calls made inside
            # the block are attributed to it; discard what came before.
            try:
                self.driver.execute_script(_API_TIMINGS_JS, f"__qaPerfMark_{self.key}")
            except Exception:
                pass
        _push_block(self)
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self._t0
        _pop_block(self)
        # Only judge performance if the wrapped block actually succeeded --
        # a functional failure should surface as its own (functional) step,
        # not get muddied with a misleading performance verdict.
        if exc_type is not None:
            return False
        env = self.env or _current_env()
        api_calls = collect_api_timings(self.driver, scope=self.key, mark=self.key, env=env)

        passed = elapsed <= self.threshold_s
        noisy = self.key in NOISY_KEYS
        extra = {"noisy": noisy, "api_calls": api_calls}
        median = load_baseline(env).get(self.key)
        if median:
            ratio = elapsed / median if median > 0 else 0.0
            extra.update({
                "baseline_elapsed_s": round(median, 2),
                "trend_ratio": round(ratio, 2),
                "trend_warning": ratio > TREND_WARN_FACTOR,
            })
        # A noisy key's breach is still recorded (passed=False) but flagged
        # so it's reported as a warning rather than failing the run.
        record_perf(self.key, elapsed, self.threshold_s, passed, env=env,
                    fixed_sleep_s=self.fixed_sleep_s, **extra)

        print(
            f"[PERF] '{self.key}' took {elapsed:.1f}s (of which fixed sleeps {self.fixed_sleep_s:.1f}s), "
            f"budget {self.threshold_s:.0f}s, {api_calls} API call(s)"
        )
        if not passed:
            message = f"[PERF] '{self.key}' took {elapsed:.1f}s, exceeding the {self.threshold_s:.0f}s budget"
            print(message + (" (noisy step: warning only)" if noisy else ""))
            if self.fail_fast and not noisy:
                raise AssertionError(message)
        return False


def read_perf_results(env: str) -> list[dict]:
    return _read_jsonl(_perf_log_path(env))


def read_perf_failures(env: str, include_noisy: bool = False) -> list[dict]:
    """One entry per (test, key) that ever breached its budget, across every
    attempt -- a rerun later finishing within budget doesn't erase the fact
    that the first attempt was genuinely slow, so this deliberately doesn't
    use "last write wins" the way the checklist steps do. Noisy keys are
    excluded unless include_noisy=True (see read_perf_warnings)."""
    seen = set()
    failures = []
    for entry in read_perf_results(env):
        if entry.get("passed"):
            continue
        if entry.get("noisy") and not include_noisy:
            continue
        dedupe_key = (entry.get("test", "unknown_test"), entry.get("key"))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        failures.append(entry)
    return failures


def read_perf_warnings(env: str) -> list[dict]:
    """Noisy-step budget breaches plus trend warnings (step time well
    above the historical median) -- reported, but never fail the run."""
    seen = set()
    warnings = []
    for entry in read_perf_results(env):
        noisy_breach = entry.get("noisy") and not entry.get("passed")
        if not (noisy_breach or entry.get("trend_warning")):
            continue
        dedupe_key = (entry.get("test", "unknown_test"), entry.get("key"))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        warnings.append(entry)
    return warnings
