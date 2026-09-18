"""Step-checklist reporter for the SureAdhere smoke suite's Slack summary.

Tests call `report_step(key, passed, detail=...)` at the point a checklist
milestone actually happens. Each call appends one JSON line to a
per-environment JSONL file (safe to call concurrently from pytest-xdist
worker processes -- see the note in common_utilities/perf.py). At the end of
the run, conftest.py's `pytest_terminal_summary` reads the file and renders
the exact Slack template requested by the project team:

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


def render_slack_report(env: str, server: str, client: str, release: str = "") -> str:
    """Render the exact Slack checklist template for this environment."""
    steps, values = read_step_results(env)
    header = f"Smoke Tests - {server}{release} - Client: {client}"

    lines = [header]
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

    lines.append(f"Summary: {'PASS' if overall_pass else 'FAIL'}")

    # A perf_budget breach on a first attempt that a rerun later passes
    # cleanly leaves no trace in the checklist above (steps use last-write-
    # wins, so the rerun's clean timing silently overwrites the earlier
    # failure) -- surface it here regardless of whether the test ultimately
    # passed, since the slowness genuinely happened.
    from common_utilities.perf import read_perf_failures
    perf_failures = read_perf_failures(env)
    if perf_failures:
        lines.append("")
        lines.append("Performance issues:")
        for failure in perf_failures:
            lines.append(
                f"- {failure.get('test', 'unknown_test')}: '{failure['key']}' took "
                f"{failure['elapsed_s']:.1f}s, exceeding the {failure['budget_s']:.0f}s budget"
            )

    return "\n".join(lines)
