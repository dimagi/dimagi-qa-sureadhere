"""Step-checklist reporter for the SureAdhere smoke suite's Slack summary.

Tests call `report_step(key, passed, detail=...)` at the point a checklist
milestone actually happens. Each call appends one JSON line to a
per-environment JSONL file (safe to call concurrently from pytest-xdist
worker processes -- see the note in common_utilities/perf.py). At the end of
the run, conftest.py's `pytest_terminal_summary` reads the file and renders
the exact Slack template requested by the project team, followed by a
separate performance box (see render_performance_block):

    Smoke Tests - <server><release> - Client: <client name>
    :large_green_circle: Logged in, existing staff (<username>)
    ...
    Summary: <PASS/FAIL>          <- smoke tests only

    ```
    PERFORMANCE: OK / SLOW
    ...
    ```

The two results are reported separately (slack_status_<env>.json) so the
Slack header can say e.g. "Smoke tests: Passed | Performance: Slow"
instead of one combined pass/fail.
"""

import json
import os
import time
from pathlib import Path

from common_utilities.path_settings import PathSettings

GREEN = ":large_green_circle:"
RED = ":red_circle:"
YELLOW = ":large_yellow_circle:"  # mustard, matches the "Skipped" slice color (#fad000) in the summary chart

# Canonical, ordered checklist -- (key, label template). `label` uses
# str.format placeholders that get filled from the values passed to
# report_step(..., detail=...) / the values dict built in conftest.py.
STEP_TEMPLATE = [
    ("login_existing_staff", "Logged in, existing staff ({admin_username})"),
    ("staff_created", "Staff Created ({new_staff_username})"),
    ("staff_edited", "Staff edited"),
    ("login_new_staff", "Logged in, new staff"),
    ("patient_created", "Created patient (SA-{admin_patient_sa_id})"),
    ("patient_edited", "Edit patient"),
    ("regimen_created", "Create new Regimen (SA-{admin_patient_sa_id})"),
    ("regimen_edited", "Edit Regimen (SA-{admin_patient_sa_id})"),
    ("patient_pin_generated", "Generated patient PIN"),
    ("mobile_login", "Mobile login ({device_type})"),
    ("video_submitted", "Video submitted"),
    ("in_app_messaging", "In app messaging: bi-directionally functional"),
    ("mobile_data_on_web", "Mobile data looks good on the web (Video functions all tested)"),
    ("dose_submitted_pda_on", "Dose submitted with Per Drug Adherence (36) enabled"),
    ("auto_complete_in_person", "Test Per Drug Auto Complete - In Person Visit - Provider Yes (SA-{mobile_patient_sa_id})"),
    ("auto_complete_self_report", "Test Per Drug Auto Complete - Self Report - Provider No (SA-{patient2_sa_id})"),
    ("taken_count_updated", "Taken count updated correctly on overview tab"),
    ("dose_submitted_pda_off", "Dose submitted with Per Drug Adherence (36) disabled (SA-{patient2_sa_id})"),
    ("all_pages_loading", "All pages loading fine."),
]
STEP_KEYS = {key for key, _ in STEP_TEMPLATE}


def _current_env() -> str:
    return os.environ.get("DIMAGIQA_ENV", "default_env")


def _steps_log_path(env: str) -> Path:
    return Path(PathSettings.ROOT) / f"slack_steps_{env}.jsonl"


def report_step(key: str, passed: bool, detail: str | None = None, env: str | None = None) -> None:
    """Record one checklist milestone. `key` must be one of STEP_KEYS."""
    if key not in STEP_KEYS:
        raise ValueError(f"Unknown step key '{key}' -- add it to STEP_TEMPLATE first")
    env = env or _current_env()
    entry = {
        "key": key,
        "passed": bool(passed),
        "detail": detail,
        "ts": time.time(),
    }
    with open(_steps_log_path(env), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class checklist_step:
    """Context manager pairing a checklist key with the code that fulfils it.

    Records a green step on clean exit, a red step (with the exception text
    as detail) if the wrapped block raises -- then lets the exception
    propagate so the test still fails normally.

        with checklist_step("staff_created"):
            ...create the staff member...
    """

    def __init__(self, key: str, env: str | None = None):
        self.key = key
        self.env = env

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            report_step(self.key, True, env=self.env)
        else:
            report_step(self.key, False, detail=str(exc_val), env=self.env)
        return False


def report_values(values: dict, env: str | None = None) -> None:
    """Record dynamic values (username, sa_id_1, device_type, ...) used to
    fill in the checklist labels. Safe to call multiple times; later values
    for the same key win when the report is rendered."""
    env = env or _current_env()
    entry = {"values": values, "ts": time.time()}
    with open(_steps_log_path(env), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_step_results(env: str) -> tuple[dict, dict]:
    """Return (steps, values): steps maps key -> latest {"passed", "detail"};
    values merges all report_values() calls (later calls win)."""
    path = _steps_log_path(env)
    steps: dict = {}
    values: dict = {}
    if not path.exists():
        return steps, values
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "values" in entry:
                values.update(entry["values"])
            elif "key" in entry:
                # Last write per key wins, but a failure should never be
                # silently overwritten by a stale earlier pass.
                prev = steps.get(entry["key"])
                if prev is None or entry["ts"] >= prev.get("ts", 0):
                    steps[entry["key"]] = entry
    return steps, values


def wait_for_step(key: str, timeout: int = 900, poll_interval: int = 10, env: str | None = None) -> None:
    """Block until `key` has been recorded by report_step()/checklist_step()
    -- pass or fail, either counts as done. Used to sequence a test in one
    xdist worker after a test in a different file/class whose completion
    pytest-dependency's `depends=[...]` can't reliably order across worker
    processes."""
    env = env or _current_env()
    deadline = time.time() + timeout
    while True:
        steps, _ = read_step_results(env)
        if key in steps:
            return
        if time.time() >= deadline:
            raise AssertionError(f"Timed out after {timeout}s waiting for checklist step '{key}' to be recorded")
        time.sleep(poll_interval)


PERF_OK, PERF_BAD, PERF_WARN = "\u2705", "\u274c", "\u26a0\ufe0f"  # inside a code block, so real emoji
# Every slow kind of request is listed (Slack code blocks can't scroll;
# Slack folds a long message behind "Show more" itself). The cap is only a
# safety net against a pathological run blowing past Slack's size limit.
MAX_SLOW_ENDPOINTS_SHOWN = 50


def render_performance_block(env: str, suite_duration_s: float | None = None) -> tuple[list[str], bool]:
    """The plain-English performance box shown after the checklist: one line
    per timed action (worst measurement across tests and attempts, since a
    rerun finishing in time doesn't erase a slow first attempt), the whole
    run's duration, server response times, then "slower than usual"
    warnings. Returns (lines, passed). Technical detail (endpoints, p95s)
    stays in the log and the report attachment, not here."""
    from common_utilities import perf

    by_key: dict[str, list[dict]] = {}
    for entry in perf.read_perf_results(env):
        by_key.setdefault(entry.get("key"), []).append(entry)

    rows = []  # (icon, label, value, note)
    passed = True
    ordered_keys = list(perf.STEP_LABELS) + sorted(k for k in by_key if k not in perf.STEP_LABELS)
    for key in ordered_keys:
        label = perf.STEP_LABELS.get(key, key)
        entries = by_key.get(key)
        if not entries:
            rows.append((PERF_WARN, label, "not measured", "the step did not complete - see the checklist"))
            continue
        worst = max(entries, key=lambda e: e["elapsed_s"])
        value = perf.fmt_duration(worst["elapsed_s"])
        expected = f"expected under {perf.fmt_duration(worst['budget_s'])}"
        breached = any(not e.get("passed") for e in entries)
        if breached and key in perf.NOISY_KEYS:
            rows.append((PERF_WARN, label, value, f"{expected}; depends on BrowserStack, not counted"))
        elif breached:
            passed = False
            rows.append((PERF_BAD, label, value, f"{expected} - TOO SLOW"))
        else:
            rows.append((PERF_OK, label, value, expected))

    if suite_duration_s is not None:
        budget = perf.SUITE_DURATION_BUDGET_SECONDS
        too_long = suite_duration_s > budget
        passed = passed and not too_long
        rows.append((PERF_BAD if too_long else PERF_OK, "Whole smoke run", perf.fmt_duration(suite_duration_s),
                     f"expected under {perf.fmt_duration(budget)}" + (" - TOO SLOW" if too_long else "")))

    width = max(len(label) for _, label, _, _ in rows) + 3
    value_width = max(len(value) for _, _, value, _ in rows) + 2
    lines = [f"{icon} {(label + ' ').ljust(width, '.')} {value.ljust(value_width)}({note})"
             for icon, label, value, note in rows]

    api_rows = [r for r in perf.summarize_api_timings(env) if perf.is_backend_endpoint(r["endpoint"])]
    slow = perf.api_breaches(api_rows)
    if not api_rows:
        lines.append(f"{PERF_WARN} Server responses: none recorded")
    elif slow:
        passed = False
        lines.append(f"{PERF_BAD} Server responses: {len(slow)} of {len(api_rows)} kinds of request were slow")
        for row in slow[:MAX_SLOW_ENDPOINTS_SHOWN]:
            lines.append(f"     - {perf.friendly_endpoint(row['endpoint'])}: {row['reason']}")
        if len(slow) > MAX_SLOW_ENDPOINTS_SHOWN:
            lines.append(f"     - ...and {len(slow) - MAX_SLOW_ENDPOINTS_SHOWN} more (details in the report attachment)")
    else:
        lines.append(f"{PERF_OK} Server responses: all {len(api_rows)} kinds of request were quick")

    for w in perf.read_perf_warnings(env):
        if w.get("trend_warning"):
            label = perf.STEP_LABELS.get(w["key"], w["key"])
            lines.append(f"{PERF_WARN} Slower than usual: {label} took {perf.fmt_duration(w['elapsed_s'])} "
                         f"(usually {perf.fmt_duration(w['baseline_elapsed_s'])})")

    title = (f"PERFORMANCE: {PERF_OK} OK - everything loaded within the expected time" if passed
             else f"PERFORMANCE: {PERF_BAD} SLOW - see the lines marked {PERF_BAD}")
    return [title, ""] + lines, passed


def build_slack_report(env: str, server: str, client: str, release: str = "",
                       suite_duration_s: float | None = None) -> dict:
    """The smoke checklist (with its own Summary, smoke tests only), then the
    performance box. Returns {"text", "smoke", "performance"} with each
    status "PASS"/"FAIL"."""
    steps, values = read_step_results(env)
    header = f"Smoke Tests - {server}{release} - Client: {client}"

    lines = [header]
    smoke_pass = True
    for key, label_tmpl in STEP_TEMPLATE:
        result = steps.get(key)
        if result is None:
            # A checklist item nobody reported on this run -- typically a
            # test skipped via pytest-dependency after an earlier step in
            # the chain failed. Distinct mustard/yellow, not red: it wasn't
            # actively verified as broken, it just never ran.
            icon = YELLOW
            smoke_pass = False
        else:
            icon = GREEN if result["passed"] else RED
            smoke_pass = smoke_pass and result["passed"]
        try:
            label = label_tmpl.format(**values)
        except KeyError:
            # Missing dynamic value (e.g. the step never got that far) --
            # show the template with a placeholder rather than crashing the
            # whole report.
            label = label_tmpl
            for k in values:
                label = label.replace(f"{{{k}}}", str(values[k]))
        lines.append(f"{icon} {label}")
    lines.append(f"Summary: {'PASS' if smoke_pass else 'FAIL'}")

    # A slow step doesn't fail its test (so it can't hide the rest of that
    # test's functional checks); it's reported in this box instead, and
    # both results drive the Slack header and the job status.
    perf_lines, perf_pass = render_performance_block(env, suite_duration_s)
    lines += ["", "```"] + perf_lines + ["```"]
    return {
        "text": "\n".join(lines),
        "smoke": "PASS" if smoke_pass else "FAIL",
        "performance": "PASS" if perf_pass else "FAIL",
    }


def render_slack_report(env: str, server: str, client: str, release: str = "",
                        suite_duration_s: float | None = None) -> str:
    return build_slack_report(env, server, client, release, suite_duration_s)["text"]
