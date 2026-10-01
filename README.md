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

**Performance check**: the Slack report starts with a performance block, placed before the checklist template:

```
Performance check: FAIL
:large_green_circle: Login to dashboard: 41s (limit 150s)
:large_green_circle: Create patient: 38s (limit 100s)
:red_circle: Edit regimen: 291s (limit 280s) - too slow in test_case_06_regimen_created_and_edited
:large_yellow_circle: Mobile video submit: 320s (limit 300s) - BrowserStack-dependent, warning only
:red_circle: API response times: 1 slow endpoint(s) out of 23
      - /treatment/patients: p95 4.2s over 12 calls (limit 3s)

Smoke Tests - Staging - Client: ...
...
Summary: FAIL
```

- **Step timings**: `common_utilities/perf.py`'s `perf_budget` times login to dashboard, patient and regimen creation and editing, the in-app messaging round trip and mobile video submission. Each step's limit is in `DEFAULT_BUDGETS`. A line shows the worst time across tests and attempts, because a rerun that finishes in time doesn't erase a slow first attempt.
- **API response times**: the browser's own timings for every backend XHR/fetch call made during the run (Resource Timing API) are checked. An endpoint fails when its p95 is over 3s across 3 or more calls, or when any single call takes over 10s (`API_*` constants in `perf.py`). All endpoint timings are written to `perf_api_summary_<env>.json`.
- **Red fails the run**: any red line forces `Summary: FAIL`, which fails the CI job. A slow step doesn't fail the test itself, so the rest of that test's functional checks still run and it isn't rerun just for being slow. `mobile_video_submit` depends on BrowserStack's devices and network, so it is warning-only (`NOISY_KEYS`).
- **Slower than usual (warning only)**: a step that takes more than 1.5x its median over the last 10 runs on that environment gets a warning. The history comes from the metrics branch's `metrics/runs.jsonl`, which the workflow fetches as `perf_history.jsonl`.
- **The overall suite-duration budget** is still checked at the end of the run.

**Waiting for the app instead of fixed sleeps**: the long fixed `time.sleep()` calls on the timed paths were there because the app really is slow to load. They are replaced with `BasePage.wait_for_app_idle(timeout=<old sleep>)`. It waits *up to* the old sleep time but returns as soon as the page has loaded, no API call is in flight, no Kendo loading indicator is showing and the network has been quiet for 1.5s. In the worst case a step takes exactly as long as before; otherwise the step timings now show how long the app actually took. The test log prints an `[app-idle]` line for each wait. If a step turns flaky after this change, put that one `time.sleep()` back.

 -  You should be able to find the zipped results in the **Artifacts** section, of the corresponding run (after a run is complete).

<img width="738" height="115" alt="image" src="https://github.com/user-attachments/assets/71fc1a5a-d388-4c1a-ad2d-57f49016ae91" />


