# dimagi-qa-sureadhere

## SureAdhere Test Script

This script contains the happy paths workflows of the SureAdhere app. Here are the scripted [automated workflows.](https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723)

## Executing Scripts

### <ins> On Local Machine </ins>

#### Setting up the test environment

```sh

# Create and activate a virtualenv using your preferred method. Example:
python -m venv venv
source venv/bin/activate


# install requirements
pip install -r requires.txt

```

[More on setting up virtual environments](https://confluence.dimagi.com/display/GTD/QA+and+Python+Virtual+Environments)


#### Running Tests


 -   Copy `settings-sample.cfg` to `settings.cfg` and populate `settings.cfg` for
the environment you want to test.
- Run tests using pytest command like:

```sh

# To execute all the test cases 
pytest -v testCases --browser=chrome --reruns 1 --dashboard --html=report.html

```
- You could also pass the following arguments
  - ` -n auto --dist=loadfile` - This will run the tests parallelly in instances assigned automatically. The number of reruns is configurable.
  - ` --reruns 1` - This will re-run the tests once in case of failures. The number of reruns is configurable too.

### <ins> Trigger Manually on Gitaction </ins>

To manually trigger the script,
  - Go to [SA Workflows action](https://github.com/dimagi/dimagi-qa-sureadhere/actions/workflows/sa-workflows.yml)
  - Run workflow
  - Use workflow from ```main```
  - Use the environment as desired
  - Run!

## Script Results

 -  Every run (pass or fail) posts a results message to the Slack channel **#qa-sureadhere-automated-test-results**, with the summary chart image attached.

<img width="517" height="172" alt="image" src="https://github.com/user-attachments/assets/20248e98-84df-4217-accb-b176fc3c8107" />

The message body is a fixed checklist, one line per scripted workflow step, matching the automated workflow steps 1:1:

```
Smoke Tests - <Environment>[ Release <version>] - Client: <client name>
🟢 Logged in, existing staff (<username>)
🟢 Staff Created (<username>)
🟢 Staff edited
🟢 Logged in, new staff
🟢 Created patient (SA-<id>)
🟢 Edit patient
🟢 Create new Regimen (SA-<id>)
🟢 Edit Regimen (SA-<id>)
🟢 Generated patient PIN
🟢 Mobile login (<device>)
🟢 Video submitted
🟢 In app messaging: bi-directionally functional
🟢 Mobile data looks good on the web (Video functions all tested)
🟢 Dose submitted with Per Drug Adherence (36) enabled
🟢 Test Per Drug Auto Complete - In Person Visit - Provider Yes (SA-<id>)
🟡 Test Per Drug Auto Complete - Self Report - Provider No (SA-<id>)
🟢 Taken count updated correctly on overview tab
🟡 Dose submitted with Per Drug Adherence (36) disabled (SA-<id>)
🟢 All pages loading fine.
Summary: FAIL
```

- 🟢 green — that step ran and passed.
- 🔴 red — that step ran and failed.
- 🟡 mustard/yellow — that step never ran at all (usually because an earlier step in its dependency chain failed or was skipped), so it wasn't actively verified as broken, it just never got the chance to run.
- `Summary` is `PASS` only when every step is green **and** the overall suite didn't run far longer than usual (see the suite-duration budget below) — a single mustard/red line, or a run that took far longer than usual, flips it to `FAIL` even when pytest's own pass/fail counts alone wouldn't have caught it. This is also what actually fails the CI job now, not just pytest's exit code.
- The exact same checklist text is also included in the result email (previously the email only ever said a generic "PASSED"/"FAILED, check the attachment").
- The canonical, ordered list of checklist steps and their labels lives in `common_utilities/step_reporter.py` (`STEP_TEMPLATE`) — that's the place to add, rename, or reorder a line.

**Performance budgets**: a handful of the slowest, most meaningful actions (login to dashboard, patient/regimen creation, mobile video submission, in-app messaging round-trip) are timed via `common_utilities/perf.py`'s `perf_budget`, plus one overall suite-duration budget checked at the end of the run. Each measurement records:

- `elapsed_s` - raw wall clock, judged against the step's budget (`DEFAULT_BUDGETS`).
- `fixed_sleep_s` - time spent in this repo's own literal `time.sleep(<number>)` calls during the step, and `active_s = elapsed_s - fixed_sleep_s`, i.e. time actually spent waiting on the app. Polling/backoff sleeps with a variable argument and SeleniumBase's own waits still count as active time.
- the browser's own per-endpoint timings for every XHR/fetch call the step made (Resource Timing API), written to `slack_api_<env>.jsonl`.

A budget breach no longer fails the test mid-run (so a slow step can't hide the rest of that test's functional checks or trigger a rerun of it). Instead it forces `Summary: FAIL` and is listed in a **`Performance issues:`** section after `Summary`, from whichever attempt it happened on, e.g.:

```
Performance issues:
- test_case_06_regimen_created_and_edited: 'edit_regimen' took 280.2s, exceeding the 280s budget
```

A **`Performance warnings (do not fail the run):`** section lists breaches of BrowserStack-dependent steps (`NOISY_KEYS`, currently `mobile_video_submit`) and **trend warnings**: a step whose `active_s` is more than `TREND_WARN_FACTOR` (1.5x) its median over the last 10 runs on that environment. The history comes from the metrics branch's `metrics/runs.jsonl`, which the workflow fetches as `perf_history.jsonl` before the run; each run's `run_summary.json` now carries a `perf` list and the 25 slowest API endpoints (`api`) so the next run, and the dashboard, can use them.

Every web test (smoke and extended) also records the API calls it made, and the end of the run prints the slowest endpoints by p95 and writes them all to `perf_api_summary_<env>.json`. The perf/API files are included in the zipped artifacts.

Both sections are omitted entirely when there is nothing to report.

 -  You should be able to find the zipped results in the **Artifacts** section, of the corresponding run (after a run is complete).

<img width="738" height="115" alt="image" src="https://github.com/user-attachments/assets/71fc1a5a-d388-4c1a-ad2d-57f49016ae91" />


