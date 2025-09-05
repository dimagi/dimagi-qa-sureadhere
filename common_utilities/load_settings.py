# common_utilities/self_healing_locators/load_settings.py

import os
from pathlib import Path
from configparser import ConfigParser

def load_settings():
    env_keys = [
        "url", "admin_username", "admin_password", "login_username", "login_password", "bs_user", "bs_key", "imap_password"
    ]
    settings = {}
    for key in env_keys:
        env_var = f"DIMAGIQA_{key.upper()}"
        if env_var in os.environ:
            settings[key] = os.environ[env_var]

    if "url" not in settings:
        cfg_path = Path(__file__).parent.parent / "settings.cfg"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Missing settings.cfg at: {cfg_path}")

        parser = ConfigParser()
        parser.read(cfg_path)
        defaults = parser["default"]

        # fill from file
        for key in env_keys:
            settings[key] = defaults.get(key)

        # special handling for embedded login
        if defaults.get("url") == "https://banner.sureadherelabs.com/":
            settings["url"] = f"https://{settings['admin_username']}:{settings['admin_password']}@banner.sureadherelabs.com/"
        else:
            settings["url"] = defaults["url"]

    return settings
