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
  - **Slack channel**: leave it on `auto` (runs on `main` post to the release channel, runs on any other branch post to **#qa-branch-test-results**), or pick `release channel` / `branch test channel` to override
  - Run!

## Script Results

 -  Every run (pass or fail) posts a results message to Slack, with the summary chart image attached:
    - **#qa-sureadhere-automated-test-results** (the release channel): post-deploy runs, and manual runs from `main`.
    - **#qa-branch-test-results**: pull request runs, merges to `main`, and runs on any other branch, so testing changes doesn't flood the release channel. This channel is shared by QA scripts from other repos too.
    - A manual run can override this with the `slack_channel` option. The channel IDs are the `SLACK_CHANNEL_ID_SA_RELEASE` and `SLACK_CHANNEL_ID_BRANCH_TEST` secrets, and QA-Bot must be a member of both channels.

<img width="517" height="172" alt="image" src="https://github.com/user-attachments/assets/20248e98-84df-4217-accb-b176fc3c8107" />

Each run reports **two separate results**: the **smoke tests** (the checklist) and **performance**. That way a slow run is never mistaken for a broken release, or the other way round. The Slack message is laid out like this:

```
📊 [Staging] SureAdhere Tests Run #741 — MANUAL TRIGGER
Smoke tests: ✅ Passed   |   Performance: ❌ Slow

Smoke Tests - Staging[ Release <version>] - Client: <client name>
🟢 Logged in, existing staff (<username>)
...one line per checklist step...
🟢 All pages loading fine.
Summary: PASS

  ┌──────────────────────────────── (Slack code block) ─┐
  │ PERFORMANCE: ❌ SLOW - see the lines marked ❌        │
  │ ...action times, whole run, server responses...     │
  │ Full details: see the Performance report link below │
  └─────────────────────────────────────────────────────┘

📎 Artifact: Download here
📈 Performance report: View here
🔗 Dashboard: https://dimagi.github.io/dimagi-qa-sureadhere/
```

The thread under the message is used only for the AI failure analysis, which is posted when tests fail.

### Smoke tests (the checklist)

The checklist has one fixed line per scripted workflow step, matching the automated workflow steps 1:1:

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

- 🟢 green: that step ran and passed.
- 🔴 red: that step ran and failed.
- 🟡 mustard/yellow: that step never ran at all, usually because an earlier step in its dependency chain failed or was skipped. It wasn't actively verified as broken; it just never got the chance to run.
- `Summary` covers the **smoke tests only**. It is `PASS` only when every step is green. A single mustard or red line flips it to `FAIL`, even when pytest's own pass/fail counts wouldn't have caught it. A smoke `FAIL` is what fails the CI run.
- The canonical, ordered list of checklist steps and their labels lives in `common_utilities/step_reporter.py` (`STEP_TEMPLATE`). That's the place to add, rename or reorder a line.

### Performance

The performance box comes after the checklist and is written in plain language:

```
PERFORMANCE: ❌ SLOW - see the lines marked ❌

✅ Login to dashboard ........... 38s     (expected under 2m 30s)
✅ Create patient ............... 35s     (expected under 1m 40s)
✅ Create regimen ............... 1m 23s  (expected under 2m 30s)
✅ Edit regimen ................. 2m 37s  (expected under 4m 40s)
✅ In-app messaging round trip .. 1m 46s  (expected under 3m)
✅ Mobile video submit .......... 1m 36s  (expected under 5m)
✅ Whole smoke run .............. 32m     (expected under 1h 15m)
❌ Server responses: 7 of 56 kinds of request were slow
     - Messaging: recent messages: usually 17.8s (expected under 3s)
     - Dashboard: recent videos: one request took 19.3s (expected under 10s)
     - ...

Full details: see the Performance report link below (also performance_report_banner.txt in the report attachment).
```

- **Action times**: `common_utilities/perf.py`'s `perf_budget` times six actions: login to dashboard, patient creation, regimen creation and editing, the in-app messaging round trip, and mobile video submission. The limits are in `DEFAULT_BUDGETS`, and the whole run's duration is checked against `SUITE_DURATION_BUDGET_SECONDS`. Each line shows the worst time across tests and attempts, so a rerun that finishes in time doesn't hide a slow first attempt.
- **Server responses**: the browser's own timings for every backend call made during the run are checked. A kind of request is slow when it *usually* takes over 3s (its median, across 3 or more calls) or when any single request takes over 10s (the `API_*` constants in `perf.py`). The box lists the 10 slowest (`MAX_SLOW_ENDPOINTS_SHOWN`), then "...and N more". Names come from `friendly_endpoint()`.
- **Compared with recent runs**: each action is also compared with its median over the last 10 runs on that environment. The history comes from the metrics branch's `metrics/runs.jsonl`, which the workflow fetches as `perf_history.jsonl` before the run.
  - **2x or more** (`TREND_FAIL_FACTOR`) is a **regression** (❌ "Much slower than usual … REGRESSION"). It fails the performance check, because a jump like that is often an early sign of an expensive query, especially right after a release.
  - **1.5x–2x** (`TREND_WARN_FACTOR`) is a ⚠️ "slower than usual" warning.
  - The comparison starts once an action has at least 5 earlier measurements on that environment (`TREND_MIN_SAMPLES`).
- **Warnings (⚠️)** never fail the performance check:
  - mobile video submission, which depends on BrowserStack's devices and network (`NOISY_KEYS`). This includes its comparison with recent runs;
  - a step that didn't complete, which the checklist already reports;
  - "slower than usual" (1.5x–2x, see above).
- **A slow step doesn't fail its test**, so the rest of that test's functional checks still run, and the test isn't rerun just for being slow.
- **Performance never fails the CI run.** A slow run is reported in Slack, the email and the performance report, and as a ⚠️ warning on the run, but the run stays green if the smoke tests passed.

**Full performance report**: every run also writes `performance_report_<env>.txt` with all the details the box leaves out:
- every timed action from every test, with reruns marked;
- every kind of server request with its number of calls, usual time, slowest time and result;
- the comparison with recent runs, including any regressions and "slower than usual" warnings.

It is shown in three places:
- **Slack**: the 📈 **Performance report: View here** link opens the run's GitHub summary page, where each environment has its own section.
- **Email**: the file is attached, and the box's last line reads "see the attached performance report" instead.
- **Artifacts**: the file is inside the reports zip, along with the raw data (`slack_perf_<env>.jsonl`, `slack_api_<env>.jsonl`, `perf_api_summary_<env>.json`).

**Performance trend**: the Slack message and the email both have a 📉 **Performance trend** link. It opens the [dashboard](https://dimagi.github.io/dimagi-qa-sureadhere/) directly at its **Performance trend** section, showing only the performance trends, with the run's environment already selected (`?perf_env=<env>`; the full dashboard is one click away).
- There is one small chart per timed action, showing its time on each recent run of that environment.
- Each run's dot is coloured by the performance check: green is normal, amber is slower than usual (1.5x), red is a regression (2x) or over its limit, and grey means not enough history yet.
- Dashed lines mark the usual time (median of the last 10) and 2x usual, where a regression starts.
- Hover a point for its numbers, or click it to open the run. The section follows the dashboard's time-window and trigger filters.

### Status, email and dashboard

- Both results are written to `slack_status_<env>.json`. **Only the smoke tests decide whether the CI run passes.** A performance failure is shown in Slack, the email and the performance report, and as a warning annotation on the run, but the run stays green. The dashboard's overall status follows the smoke tests too.
- The Slack header shows ✅/❌ for each result. The single leading icon is only used if the status file is missing, for example if pytest crashed.
- The result email contains the same checklist and performance box. Its subject says both results (for example "Smoke PASSED, Performance SLOW"), and it attaches the reports zip and the performance report.
- The dashboard's `run_summary.json` records `smoke_status` and `perf_status`, plus the timing data used for the comparison with recent runs.
- Posting to Slack is retried if Slack errors or times out, falling back to a text-only message if the chart upload keeps failing. It checks the channel first, so a report is never posted twice.
- **Public repo:** this repo and its CI logs, artifacts and dashboard are public. Recorded endpoint names keep only the app's own route words (`_KNOWN_ROUTE_SEGMENTS` in `perf.py`). Every other path segment becomes `{id}`: IDs, emails, MRNs, tokens, and also plain words like a name. Hosts and query values are dropped. A new route that isn't in the list still works, but shows up as `{id}` until its word is added.

### Waiting for the app instead of fixed sleeps

The long fixed `time.sleep()` calls on the timed paths were there because the app really is slow to load. These are login 35s, the dashboard 10s twice, patient search 10s, opening a patient 15s, the patient profile 15s, the regimen tab 10s and creating a schedule 15s. Each is replaced with `BasePage.wait_for_app_idle(timeout=<old sleep>)`:
- It waits *up to* the old sleep time, but returns once the page has settled for 1.5s. Settled means the page is loaded, no API call is in flight, and none of the app's loading indicators (`spinner-absolute-100`, `kendo-loader`, `*-loader`, Kendo's loading mask) is visible.
- The in-flight counter is registered through Chrome DevTools, so it also counts calls made while a page is starting up.
- It doesn't wait for a fully quiet network, because the dashboard polls the API all the time.
- In the worst case a step takes exactly as long as before. Otherwise the step timings show how long the app really took.
- Each wait prints an `[app-idle]` line in the test log.

If a step turns flaky after this change, give it its time back where it's needed. For example, `check_for_video_review()` now waits up to 30s for the review form's data, and the auto-filled tag check allows 45s. Both were needed on Staging, whose server is slow.

 -  You should be able to find the zipped results in the **Artifacts** section, of the corresponding run (after a run is complete).

<img width="738" height="115" alt="image" src="https://github.com/user-attachments/assets/71fc1a5a-d388-4c1a-ad2d-57f49016ae91" />


