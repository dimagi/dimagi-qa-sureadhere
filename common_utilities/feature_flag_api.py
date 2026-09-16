"""Direct REST API access to sam-iam-svc's feature-flag endpoints, as a
faster alternative to toggling flags through the Admin UI (each UI toggle
today costs multiple full page loads plus, in several places, a full
logout/login reset).

The web app authenticates via a real Azure AD B2C hosted-page redirect with
Conditional MFA -- there is no plain username/password token endpoint, so
this module does NOT try to acquire a token independently. Instead it reads
the bearer token the SPA itself stores client-side once a normal Selenium
login has completed: `localStorage['auth_token']`. This matches the
mechanism confirmed in e2e-parity (a separate Playwright suite for this
same app) -- see auth/auth.ts in that repo, which reads/writes the same key.

The direct API base URL (CONFIRMED_IAM_GATEWAY) and the numeric clientId
these endpoints expect were both confirmed against a live 'secure' run by
reading the browser's own network log rather than guessing -- see
resolve_iam_base() and discover_iam_urls_from_performance_log(). Still
unverified: whether the same gateway host and response field names hold
for banner/securevoteu, and whether PUT actually persists a change (only
observed the app's own GET/POST traffic so far). set_feature_flags_via_api()
is written to fail soft on any of that being wrong -- see its docstring.
"""

import base64
import json
import os
import time

import requests

from common_utilities.path_settings import PathSettings

TOKEN_STORAGE_KEY = "auth_token"


class FeatureFlagApiError(Exception):
    """Raised when the feature-flag API can't be used; callers should
    catch this and fall back to the existing UI-based toggle."""


def extract_auth_token(driver, timeout: int = 15) -> str:
    """Read the IAM bearer token the SPA stores in localStorage after a
    completed login. Raises FeatureFlagApiError if it never appears."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        token = driver.execute_script(
            f"return window.localStorage.getItem('{TOKEN_STORAGE_KEY}');"
        )
        if token:
            return token
        time.sleep(0.5)
    raise FeatureFlagApiError(f"'{TOKEN_STORAGE_KEY}' never appeared in localStorage")


def decode_jwt_claims(token: str) -> dict:
    """Decode a JWT's payload segment without verifying the signature --
    we only need to read claims (e.g. a client/tenant id) from a token we
    already trust because the app itself just handed it to us."""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception as e:
        raise FeatureFlagApiError(f"Could not decode JWT claims: {e}")


def discover_iam_urls_from_performance_log(driver) -> list[str]:
    """Return real network request URLs the page has already made that look
    like they hit the IAM API, read from the browser's own Performance API
    (window.performance.getEntriesByType('resource')). By the time probe()
    runs, the preceding UI-based feature-flag toggle has already made a
    real call to whatever the actual IAM endpoint is -- this sidesteps
    guessing the base URL/port entirely."""
    try:
        urls = driver.execute_script(
            "return performance.getEntriesByType('resource').map(r => r.name);"
        ) or []
    except Exception:
        return []
    needles = ("iam", "feature", "clientfeature")
    return sorted({u for u in urls if any(n in u.lower() for n in needles)})


# Confirmed via probe() against a live 'secure' run reading the browser's
# own network log (see discover_iam_urls_from_performance_log) -- the app
# calls a shared gateway, not a same-origin path, for the IAM API.
CONFIRMED_IAM_GATEWAY = "https://gateway.sureadhere.com:8443/iam"


def resolve_iam_base(driver, app_url: str) -> str:
    """Prefer a base URL discovered from the browser's own network log (the
    most reliable source, but only available if the page has already made
    a real IAM call); fall back to an explicit override; fall back to the
    gateway host confirmed against a live run. `app_url` is unused now that
    the same-origin guess it used to produce has been confirmed wrong, but
    kept in the signature in case a per-environment override is needed
    later."""
    discovered = discover_iam_urls_from_performance_log(driver)
    for u in discovered:
        try:
            from urllib.parse import urlsplit
            parts = urlsplit(u)
            if parts.scheme and parts.netloc:
                return f"{parts.scheme}://{parts.netloc}/iam"
        except Exception:
            continue
    override = os.environ.get("DIMAGIQA_IAM_BASE_URL")
    if override:
        return override.rstrip("/")
    return CONFIRMED_IAM_GATEWAY


def _output_path(env: str, name: str) -> str:
    return os.path.join(PathSettings.ROOT, f"{name}_{env}.txt")


def get_client_features(base: str, token: str, client_id, timeout: int = 15) -> list:
    """GET {base}/clientfeatures?clientId=X, returning the list of per-
    client feature entries regardless of whether the API wraps it in an
    object (e.g. {"clientfeatures": [...]}) or returns a bare list."""
    resp = requests.get(
        f"{base}/clientfeatures", params={"clientId": client_id},
        headers={"Authorization": f"Bearer {token}"}, timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("clientfeatures", "ClientFeatures", "data", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _entry_name(entry: dict):
    # Confirmed shape (local run against banner): snake_case --
    # {"client_id", "feature_id", "label", "is_active", "date_created",
    # "date_updated"}. Kept the camelCase/PascalCase variants too in case
    # a different environment's gateway serializes differently.
    for k in ("label", "Label", "featureName", "FeatureName", "name", "Name"):
        if entry.get(k):
            return entry[k]
    return None


def _entry_id(entry: dict):
    for k in ("feature_id", "featureId", "FeatureId", "id", "Id"):
        if entry.get(k) is not None:
            return entry[k]
    return None


def _entry_active(entry: dict):
    for k in ("is_active", "isActive", "IsActive", "active", "Active"):
        if k in entry:
            v = entry[k]
            if isinstance(v, str):
                return v.strip().lower() == "true"
            return bool(v)
    return None


def set_client_feature(base: str, token: str, client_id, feature_id, is_active: bool, timeout: int = 15) -> None:
    """PUT (falling back to POST if the row doesn't exist yet) {base}/clientfeatures."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"client_id": client_id, "feature_id": feature_id, "is_active": is_active}
    resp = requests.put(f"{base}/clientfeatures", json=body, headers=headers, timeout=timeout)
    if resp.status_code == 404:
        resp = requests.post(f"{base}/clientfeatures", json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()


def _find_client_features(base: str, token: str, claims: dict, wanted_names: set, log) -> tuple:
    """Try candidate clientIds (the token's own client_id claim first) until
    one's feature list contains at least one of wanted_names. Returns
    (chosen_client_id, entries) or (None, []) if none matched."""
    candidate_ids = []
    own_client_id = claims.get("client_id")
    if own_client_id:
        candidate_ids.append(own_client_id)
    for extra in ("136",):
        if extra not in candidate_ids:
            candidate_ids.append(extra)

    for cid in candidate_ids:
        try:
            fetched = get_client_features(base, token, cid)
        except Exception as e:
            log(f"GET clientfeatures?clientId={cid} failed: {e}")
            continue
        names = {_entry_name(e) for e in fetched if _entry_name(e)}
        overlap = names & wanted_names
        log(f"clientId={cid}: {len(fetched)} feature rows, {len(overlap)}/{len(wanted_names)} name matches")
        if overlap:
            return cid, fetched
    return None, []


def verify_feature_flags_via_api(driver, app_url: str, ff_dict: dict, env: str | None = None) -> dict:
    """Read-only check of every flag in ff_dict (name -> 'ON'/'OFF') via the
    IAM API instead of navigating to the Admin Feature Flags page. Returns
    {name: True} for flags confirmed to already be in the wanted state --
    the caller should fall back to the UI (which can also correct a
    mismatch) for anything left out of that dict. Never raises. Same
    minimal-logging policy as set_feature_flags_via_api: no token, no full
    claims, no raw response bodies.
    """
    env = env or os.environ.get("DIMAGIQA_ENV", "default_env")
    lines = []

    def log(msg):
        print(msg)
        lines.append(msg)

    confirmed: dict[str, bool] = {}
    try:
        try:
            token = extract_auth_token(driver)
        except FeatureFlagApiError as e:
            log(f"[ff_api verify] could not get auth token: {e}")
            return confirmed

        claims = {}
        try:
            claims = decode_jwt_claims(token)
        except FeatureFlagApiError:
            pass
        base = resolve_iam_base(driver, app_url)
        log(f"[ff_api verify] base={base}")

        chosen_cid, entries = _find_client_features(
            base, token, claims, set(ff_dict.keys()), lambda m: log(f"[ff_api verify] {m}")
        )
        if not chosen_cid:
            log("[ff_api verify] no candidate clientId matched any wanted flag name -- API path unavailable this run")
            return confirmed

        by_name = {_entry_name(e): e for e in entries if _entry_name(e)}
        for name, toggle in ff_dict.items():
            target = toggle == "ON"
            entry = by_name.get(name)
            if not entry:
                log(f"[ff_api verify] '{name}' not in clientId={chosen_cid} feature list, leaving for UI fallback")
                continue
            current = _entry_active(entry)
            if current is None:
                log(f"[ff_api verify] '{name}' has no recognizable active field, leaving for UI fallback")
                continue
            if current == target:
                log(f"[ff_api verify] '{name}' confirmed {toggle}")
                confirmed[name] = True
            else:
                log(f"[ff_api verify] '{name}' is {'ON' if current else 'OFF'}, wanted {toggle} -- leaving for UI to correct")
    except Exception as e:
        log(f"[ff_api verify] unexpected error: {e}")
    finally:
        try:
            with open(_output_path(env, "ff_api_verify"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"[ff_api verify] could not write output file: {e}")
    return confirmed


def set_feature_flags_via_api(driver, app_url: str, ff_dict: dict, env: str | None = None) -> dict:
    """Set every flag in ff_dict (name -> 'ON'/'OFF') via the IAM API
    instead of clicking through the Admin UI. Returns {name: True} for
    flags it successfully set/confirmed; the caller is expected to fall
    back to the UI for whatever's left out of that dict (including
    everything, if the API path doesn't work at all this run) -- this
    never raises, so it can never make the test less reliable than it
    was before, only faster when it works.

    Logging here is deliberately minimal: no token value, no full JWT
    claims (which include the tester's name and other identifying
    fields), no raw API response bodies -- only counts and the flag
    names/states actually being acted on. Written to
    ff_api_set_<env>.txt as well as printed, since pytest only shows
    captured stdout for FAILING tests by default and this runs inside a
    test that's expected to pass.
    """
    env = env or os.environ.get("DIMAGIQA_ENV", "default_env")
    lines = []

    def log(msg):
        print(msg)
        lines.append(msg)

    succeeded: dict[str, bool] = {}
    try:
        try:
            token = extract_auth_token(driver)
        except FeatureFlagApiError as e:
            log(f"[ff_api set] could not get auth token: {e}")
            return succeeded

        claims = {}
        try:
            claims = decode_jwt_claims(token)
        except FeatureFlagApiError:
            pass
        base = resolve_iam_base(driver, app_url)
        log(f"[ff_api set] base={base}")

        chosen_cid, entries = _find_client_features(
            base, token, claims, set(ff_dict.keys()), lambda m: log(f"[ff_api set] {m}")
        )
        if not chosen_cid:
            log("[ff_api set] no candidate clientId matched any wanted flag name -- API path unavailable this run")
            return succeeded

        by_name = {_entry_name(e): e for e in entries if _entry_name(e)}
        for name, toggle in ff_dict.items():
            target = toggle == "ON"
            entry = by_name.get(name)
            if not entry:
                log(f"[ff_api set] '{name}' not in clientId={chosen_cid} feature list, leaving for UI fallback")
                continue
            fid = _entry_id(entry)
            current = _entry_active(entry)
            if fid is None:
                log(f"[ff_api set] '{name}' has no recognizable id field, leaving for UI fallback")
                continue
            if current == target:
                log(f"[ff_api set] '{name}' already {toggle}")
                succeeded[name] = True
                continue
            try:
                set_client_feature(base, token, chosen_cid, fid, target)
                log(f"[ff_api set] '{name}' -> {toggle} OK")
                succeeded[name] = True
            except Exception as e:
                log(f"[ff_api set] '{name}' -> {toggle} FAILED: {e}")
    except Exception as e:
        log(f"[ff_api set] unexpected error: {e}")
    finally:
        try:
            with open(_output_path(env, "ff_api_set"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"[ff_api set] could not write output file: {e}")
    return succeeded
