# common_utilities/load_settings.py

import os
from pathlib import Path
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse

# def load_settings():
#     env_keys = [
#         "url", "admin_username", "admin_password", "login_username", "login_password", "bs_user", "bs_key"
#     ]
#     settings = {}
#     for key in env_keys:
#         env_var = f"DIMAGIQA_{key.upper()}"
#         if env_var in os.environ:
#             settings[key] = os.environ[env_var]
#
#     if os.environ.get("CI") == "true":
#         settings["CI"] = "true"
#         if any(x not in settings for x in env_keys):
#             lines = settings.__doc__.splitlines()
#             vars_ = "\n  ".join(line.strip() for line in lines if "DIMAGIQA_" in line)
#             raise RuntimeError(
#                 f"Environment variables not set:\n  {vars_}\n\n"
#                 "See https://docs.github.com/en/actions/reference/encrypted-secrets "
#                 "for instructions on how to set them."
#             )
#         return settings
#     if "url" not in settings:
#         env = os.environ.get("DIMAGIQA_ENV") or "staging"
#         cfg_path = Path(__file__).parent.parent / "settings.cfg"
#         if not cfg_path.exists():
#             raise FileNotFoundError(f"Missing settings.cfg at: {cfg_path}")
#
#         parser = ConfigParser()
#         parser.read(cfg_path)
#         defaults = parser["default"]
#
#         # fill from file
#         for key in env_keys:
#             settings[key] = defaults.get(key)
#
#         # special handling for embedded login
#         if defaults.get("url") == "https://banner.sureadherelabs.com/":
#             settings["url"] = f"https://{settings['admin_username']}:{settings['admin_password']}@banner.sureadherelabs.com/"
#         else:
#             settings["url"] = defaults["url"]
#
#     return settings


# Keep this list in sync with what your tests expect
_BANNER_HOST = "banner.sureadherelabs.com"
_ROGERS_HOST = "rogers.sureadherelabs.com:8008/"

def _needs_admin_auth(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return host.lower() == _BANNER_HOST
    except Exception:
        return False

def _inject_basic_auth(url: str, user: str | None, pwd: str | None) -> str:
    if not url or not user or not pwd:
        return url
    p = urlparse(url)
    netloc = p.hostname or ""
    if p.port:
        netloc += f":{p.port}"
    netloc = f"{user}:{pwd}@{netloc}"
    return urlunparse(p._replace(netloc=netloc))

def _load_from_env() -> dict:
    env_keys = [
        "url", "admin_username", "admin_password",
        "login_username", "login_password",
        "bs_user", "bs_key", "sa_imap_password",
    ]
    s = {}
    for k in env_keys:
        v = os.environ.get(f"DIMAGIQA_{k.upper()}")
        if v:
            s[k] = v
    if not s.get("url"):
        env = os.environ.get("DIMAGIQA_ENV")
        if not env:
            raise RuntimeError("Missing DIMAGIQA_ENV in CI – cannot build URL")

        suffix = ":8008/" if "rogers" in env else "/"
        labs = "." if "secure" in env else "labs."

        # Choose correct login creds
        s["login_username"] = s.get("admin_username") if "secure" in env else s.get("login_username")
        s["login_password"] = s.get("admin_password") if "secure" in env else s.get("login_password")

        s["url"] = f"https://{env}.sureadhere{labs}com{suffix}"
        s["domain"] = env
        print(f"[INFO] Auto-generated CI URL: {s['url']}")

    return s

def _load_from_file() -> dict:
    cfg_path = Path(__file__).parent.parent / "settings.cfg"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing settings.cfg at: {cfg_path}")
    parser = ConfigParser()
    parser.read(cfg_path)
    defaults = parser["default"]
    env_keys = [
        "url", "admin_username", "admin_password",
        "login_username", "login_password",
        "bs_user", "bs_key", "sa_imap_password"
    ]
    s = {k: defaults.get(k) for k in env_keys if defaults.get(k) is not None}
    base_url = defaults.get("url")
    if base_url:
        subdomain = base_url.split("//")[1].split(".")[0]   # <-- clean extraction
        s["url"] = base_url
        s["domain"] = subdomain
        s["login_username"] = defaults.get("admin_username") if "secure" in base_url else defaults.get("login_username")
        s["login_password"] = defaults.get("admin_password") if "secure" in base_url else defaults.get("login_password")
    else:
        env = os.environ.get("DIMAGIQA_ENV")
        suffix = ":8008/" if "rogers" in env else "/"
        labs = "labs." if "secure" in env else "."
        s["login_username"] = defaults.get("admin_username") if "secure" in env else defaults.get("login_username")
        s["login_password"] = defaults.get("admin_password") if "secure" in env else defaults.get("login_password")
        s["url"] = f"https://{env}.sureadhere{labs}com{suffix}"
        print(s["url"])
        s["domain"] = env
        # fallback if no url given in config
    return s

    # if "url" not in env_keys:
    #     env = os.environ.get("DIMAGIQA_ENV") or "banner"
    #     if env == "secure":
    #         subdomain = "secure"
    #         suffix = "/"
    #     elif env == "rogers":
    #         subdomain = "rogers"
    #         suffix = ":8008/"
    #     elif env == "securevoteu":
    #         subdomain = "securevoteu"
    #         suffix = "/"
    #     else:
    #         subdomain = "banner"
    #         suffix = "/"
    #     s["url"] = f"https://{subdomain}.sureadherelabs.com{suffix}"
    #     s["domain"] = subdomain

    # Special handling: banner host gets embedded admin auth
    # base_url = defaults.get("url", "")
    # if base_url == f"https://{_BANNER_HOST}/":
    #     s["url"] = _inject_basic_auth(
    #         base_url, s.get("admin_username"), s.get("admin_password")
    #     )
    # else:
    #     base_url = defaults.get("url")
    #     subdomain = base_url.split("//")[1].split(".")[0]
    #     s["url"] = base_url
    #     s["domain"] = subdomain
    # return s

# def load_settings() -> dict:
#     s = _load_from_env()
#
#     # CI path: env is source of truth, but only minimal required keys
#     if os.environ.get("CI", "").lower() == "true":
#         s["CI"] = "true"
#         missing = []
#
#         # url + login creds always required
#         for k in ("url", "login_username", "login_password"):
#             if not s.get(k):
#                 missing.append(f"DIMAGIQA_{k.upper()}")
#
#         # If banner host, require admin creds for basic auth
#         if s.get("url") and _needs_admin_auth(s["url"]):
#             for k in ("admin_username", "admin_password"):
#                 if not s.get(k):
#                     missing.append(f"DIMAGIQA_{k.upper()}")
#
#         if missing:
#             raise RuntimeError(
#                 "Missing required environment secrets:\n  " + "\n  ".join(missing)
#             )
#
#         # Inject basic auth for banner
#         if _needs_admin_auth(s["url"]):
#             s["url"] = _inject_basic_auth(
#                 s["url"], s.get("admin_username"), s.get("admin_password")
#             )
#         return s
#
#     # Local path: if no URL in env, read from settings.cfg
#     if not s.get("url"):
#         s = _load_from_file()
#         return s
#
#     # Local with URL provided via env: allow it, and inject if banner
#     if _needs_admin_auth(s["url"]):
#         s["url"] = _inject_basic_auth(
#             s["url"], s.get("admin_username"), s.get("admin_password")
#         )
#     return s

def load_settings() -> dict:
    # CI path: env is source of truth, only minimal required keys
    if os.environ.get("CI", "").lower() == "true":
        s = _load_from_env()
        s["CI"] = "true"
        missing = []
        # url + login creds always required
        for k in ("url", "login_username", "login_password", "sa_imap_password"):
            if not s.get(k):
                missing.append(f"DIMAGIQA_{k.upper()}")

        if missing:
            raise RuntimeError(
                "Missing required environment secrets:\n  " + "\n  ".join(missing)
            )
        return s

    # Local path: always read from settings.cfg
    s = _load_from_file()
    return s
