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

Two things are NOT yet verified against a live banner/secure/securevoteu
environment (only inferred): the direct API base URL, and the numeric
clientId these endpoints expect (UserData.client stores names, not ids).
`probe()` is a read-only reconnaissance helper for gathering real data from
a CI run before anything here is wired in to replace working UI behavior --
call it, look at what it prints, then implement set_feature_flag() for real.
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


def iam_base_url(app_url: str) -> str:
    override = os.environ.get("DIMAGIQA_IAM_BASE_URL")
    if override:
        return override.rstrip("/")
    # Best guess for prod-like single-origin environments (banner/secure/
    # securevoteu all serve the SPA with no explicit port, unlike the
    # dual-port staging pattern rogers/Parker use) -- unverified.
    return app_url.rstrip("/") + "/iam"


def _probe_output_path(env: str) -> str:
    return os.path.join(PathSettings.ROOT, f"ff_api_probe_{env}.txt")


def probe(driver, app_url: str, env: str | None = None) -> None:
    """Read-only reconnaissance: extract the token, decode its claims, and
    try the feature-flag GET endpoints. Never raises past its own
    try/except -- safe to call from any test without risking the actual
    test's outcome. Delete once set_feature_flag() is built and verified
    from what this writes.

    Written to ff_api_probe_<env>.txt (not just printed): pytest only
    shows captured stdout for FAILING tests by default, and this runs
    inside a test that's expected to pass, so print() alone would never
    actually surface in the CI log.
    """
    env = env or os.environ.get("DIMAGIQA_ENV", "default_env")
    lines = []

    def log(msg):
        print(msg)
        lines.append(msg)

    try:
        try:
            token = extract_auth_token(driver)
            log(f"[ff_api probe] got token, length={len(token)}")
        except FeatureFlagApiError as e:
            log(f"[ff_api probe] FAILED to extract token: {e}")
            return

        try:
            claims = decode_jwt_claims(token)
            log(f"[ff_api probe] JWT claims: {json.dumps(claims)}")
        except FeatureFlagApiError as e:
            log(f"[ff_api probe] FAILED to decode claims: {e}")
            claims = {}

        base = iam_base_url(app_url)
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = requests.get(f"{base}/Features", headers=headers, timeout=15)
            log(f"[ff_api probe] GET {base}/Features -> {resp.status_code}: {resp.text[:2000]}")
        except Exception as e:
            log(f"[ff_api probe] GET {base}/Features FAILED: {e}")

        candidate_client_ids = sorted({
            v for k, v in claims.items()
            if isinstance(v, (int, str)) and "client" in k.lower()
        } | {1, 2, 3, 4})  # small numeric fallback guesses if no claim matches
        for cid in candidate_client_ids:
            try:
                resp = requests.get(f"{base}/ClientFeatures", params={"clientId": cid}, headers=headers, timeout=15)
                log(f"[ff_api probe] GET {base}/ClientFeatures?clientId={cid} -> {resp.status_code}: {resp.text[:1500]}")
            except Exception as e:
                log(f"[ff_api probe] GET {base}/ClientFeatures?clientId={cid} FAILED: {e}")
    finally:
        try:
            with open(_probe_output_path(env), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"[ff_api probe] could not write probe output file: {e}")
