"""Step-checklist reporter for the SureAdhere smoke suite's Slack summary.

Tests call `report_step(key, passed, detail=...)` at the point a checklist
milestone actually happens. Each call appends one JSON line to a
per-environment JSONL file (safe to call concurrently from pytest-xdist
worker processes -- see the note in common_utilities/perf.py). At the end of
the run, conftest.py's `pytest_terminal_summary` reads the file and renders
a performance block (see render_performance_block) followed by the exact
Slack template requested by the project team:

    Performance check: <PASS/FAIL>
    :large_green_circle: Login to dashboard: 42s (limit 150s)
    ...
    :large_green_circle: API response times: 24 endpoints within limits (...)

    Smoke Tests - <server><release> - Client: <client name>
    :large_green_circle: Logged in, existing staff (<username>)
    ...
    Summary: <PASS/FAIL>
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


def render_performance_block(env: str) -> tuple[list[str], bool]:
    """The performance validation shown at the top of the Slack report:
    one line per timed step (worst measurement across tests and attempts,
    since a rerun finishing in time doesn't erase a slow first attempt),
    one line for backend API response times, then any trend warnings.
    Returns (lines, passed)."""
    from common_utilities import perf

    results = perf.read_perf_results(env)
    by_key: dict[str, list[dict]] = {}
    for entry in results:
        by_key.setdefault(entry.get("key"), []).append(entry)

    passed = True
    step_lines = []
    ordered_keys = list(perf.STEP_LABELS) + sorted(k for k in by_key if k not in perf.STEP_LABELS)
    for key in ordered_keys:
        label = perf.STEP_LABELS.get(key, key)
        entries = by_key.get(key)
        if not entries:
            # The step never completed (its functional check failed or was
            # skipped), which the checklist below already reports.
            step_lines.append(f"{YELLOW} {label}: not measured")
            continue
        worst = max(entries, key=lambda e: e["elapsed_s"])
        breached = [e for e in entries if not e.get("passed")]
        text = f"{label}: {worst['elapsed_s']:.0f}s (limit {worst['budget_s']:.0f}s)"
        if breached and key in perf.NOISY_KEYS:
            step_lines.append(f"{YELLOW} {text} - BrowserStack-dependent, warning only")
        elif breached:
            passed = False
            step_lines.append(f"{RED} {text} - too slow in {worst.get('test', 'unknown_test')}")
        else:
            step_lines.append(f"{GREEN} {text}")

    api_rows = [r for r in perf.summarize_api_timings(env) if perf.is_backend_endpoint(r["endpoint"])]
    api_breaches = perf.api_breaches(api_rows)
    if not api_rows:
        step_lines.append(f"{YELLOW} API response times: no backend API calls recorded")
    elif api_breaches:
        passed = False
        step_lines.append(f"{RED} API response times: {len(api_breaches)} slow endpoint(s) out of {len(api_rows)}")
        for row in api_breaches:
            step_lines.append(f"      - {row['endpoint']}: {row['reason']}")
    else:
        slowest = max(api_rows, key=lambda r: r["p95_ms"])
        step_lines.append(
            f"{GREEN} API response times: {len(api_rows)} endpoints within limits "
            f"(slowest p95 {slowest['p95_ms'] / 1000:.1f}s, {slowest['endpoint']})"
        )

    lines = [f"Performance check: {'PASS' if passed else 'FAIL'}"] + step_lines

    trend = [w for w in perf.read_perf_warnings(env) if w.get("trend_warning")]
    if trend:
        lines.append("Slower than usual (warning only):")
        for w in trend:
            label = perf.STEP_LABELS.get(w["key"], w["key"])
            lines.append(
                f"      - {label}: {w['elapsed_s']:.0f}s, {w['trend_ratio']:.1f}x its recent median "
                f"of {w['baseline_elapsed_s']:.0f}s"
            )
    return lines, passed


def render_slack_report(env: str, server: str, client: str, release: str = "") -> str:
    """Render the performance block followed by the exact Slack checklist
    template for this environment."""
    steps, values = read_step_results(env)
    header = f"Smoke Tests - {server}{release} - Client: {client}"

    # perf_budget doesn't fail the test itself (so a slow step can't hide
    # the rest of that test's functional checks); a performance failure
    # shows up in this block and forces Summary: FAIL below instead.
    perf_lines, perf_passed = render_performance_block(env)

    lines = perf_lines + ["", header]
    overall_pass = True
    for key, label_tmpl in STEP_TEMPLATE:
        result = steps.get(key)
        if result is None:
            # A checklist item nobody reported on this run -- typically a
            # test skipped via pytest-dependency after an earlier step in
            # the chain failed. Distinct mustard/yellow, not red: it wasn't
            # actively verified as broken, it just never ran.
            icon = YELLOW
            overall_pass = False
        else:
            icon = GREEN if result["passed"] else RED
            overall_pass = overall_pass and result["passed"]
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

    overall_pass = overall_pass and perf_passed
    lines.append(f"Summary: {'PASS' if overall_pass else 'FAIL'}")
    return "\n".join(lines)
