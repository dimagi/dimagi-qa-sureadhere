"""
Robust ML-based locator extractor (merged & hardened)

Flow:
1) Load model + vectorizer
2) Login
3) Crawl pages_to_visit (click-or-open)
4) Extract locators (BeautifulSoup) using ML + heuristics
5) Save <page>_page.json mapping logical_name -> XPath
6) Click "Cancel", click "Add user", then open "add patient" and extract again

Key robustness:
- DOM stability wait (readyState + innerHTML length steady)
- Safe clicking with scroll-into-view + retries
- Heuristic fallback when ML confidence is low
- Attribute/text cleaning + unique logical names
- Skips noisy tags; handles timeouts cleanly
"""

import os
import json
import time
import re
from typing import Dict, Tuple

from bs4 import BeautifulSoup

from joblib import load
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common_utilities.load_settings import load_settings


# ----------------------- Config -----------------------

SKIP_TAGS = {"script", "style", "meta", "link", "svg", "path", "noscript", "iframe"}
MODEL_PATH = "ml_model/locator_ml_model.pkl"
VECTORIZER_PATH = "ml_model/vectorizer.pkl"

INPUT_DIR = "self_healing_locators_ml"
PROBA_THRESHOLD = 0.35  # lenient but sane
DOM_STABLE_TIMEOUT = 15
DOM_STABLE_PAUSE = 0.45  # seconds between innerHTML samples

# Pages to visit: http URL or XPATH to click
PAGE_BEFORE_LOGIN = {
    "login": None
    }
PAGES_PRIMARY = {
    "dashboard": None,  # special: we just are on dashboard after login
    "patients": "//p[text()='Patients']",
    "staff": "//p[text()='Staff']",
    "reports": "//p[text()='Reports']",
    "admin": "//p[text()='Admin']",
    "feature_flags": "//li/span[.='Feature Flags']",
    "announcements": "//li/span[.='Announcements']",
    "user": "//button//*[contains(@class,'circle-user')]",
    "add_users": "//button//*[contains(@class,'user-plus')]",
    "add_staff": "//a[contains(.,'New staff')]",
}

PAGES_AFTER_ADD_USER = {
    "add_patient": "//a[contains(.,'New patient')]",
}


# ----------------------- Utilities -----------------------

def load_model() -> Tuple:
    model = load(MODEL_PATH)
    vectorizer = load(VECTORIZER_PATH)
    print("✅ ML model + vectorizer loaded")
    return model, vectorizer


def ensure_dirs():
    os.makedirs(INPUT_DIR, exist_ok=True)


def wait_for_dom_stable(driver, timeout=DOM_STABLE_TIMEOUT, pause=DOM_STABLE_PAUSE):
    """Wait until document.readyState == 'complete' and DOM size is stable across two samples."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # length sample A
    size1 = driver.execute_script("return document.body ? document.body.innerHTML.length : 0")
    time.sleep(pause)
    # length sample B
    size2 = driver.execute_script("return document.body ? document.body.innerHTML.length : 0")
    if size1 != size2:
        # try one more round to avoid flaky transitions
        time.sleep(pause)
        size3 = driver.execute_script("return document.body ? document.body.innerHTML.length : 0")
        if size2 != size3:
            # not strictly equal; proceed anyway but warn (avoids deadlocks on animated pages)
            print(f"⚠️ DOM still changing (sizes: {size1}→{size2}→{size3}); continuing cautiously.")


def safe_find(driver, by, value, timeout=12):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def safe_click(driver, xpath, timeout=12) -> bool:
    """Scroll into view and click with retries; return True if clicked."""
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()
        return True
    except (TimeoutException, NoSuchElementException):
        print(f"❌ Not found/clickable: {xpath}")
        return False
    except ElementClickInterceptedException:
        try:
            # One retry with small scroll nudge
            driver.execute_script("window.scrollBy(0, -120);")
            time.sleep(0.2)
            el = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            el.click()
            return True
        except Exception:
            print(f"❌ Intercepted: {xpath}")
            return False


def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip()
    return s


def has_good_attrs(attrs: Dict, text: str) -> bool:
    """Heuristic fallback: keep if it likely maps to a meaningful element."""
    return bool(text.strip()) or any(k in attrs for k in ("id", "name", "placeholder", "aria-label"))


def get_xpath_bs(el) -> str:
    """Build a simple, stable absolute XPath from a BeautifulSoup element."""
    path_parts = []
    node = el
    while node and getattr(node, "name", None) and node.name != "[document]":
        sibs = list(node.find_previous_siblings(node.name))
        idx = len(sibs) + 1
        path_parts.append(f"{node.name}[{idx}]")
        node = node.parent
    if not path_parts:
        return ""
    return "//" + "/".join(reversed(path_parts))


def unique_name(name: str, used: Dict[str, int]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip()) or "element"
    base = base[:50]  # be kind to filenames/readers
    if base not in used:
        used[base] = 1
        return base
    used[base] += 1
    return f"{base}_{used[base]}"


# ----------------------- Core extraction -----------------------

def extract_locators(driver, model, vectorizer, page_name: str):
    """Parse current DOM with BeautifulSoup, score with ML, fallback to heuristics, save JSON."""
    print(f"\n🔎 Extracting on: {page_name}")
    wait_for_dom_stable(driver)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.find_all(True)
    print(f"  ➤ Total elements found: {len(elements)}")

    locators: Dict[str, str] = {}
    used_names: Dict[str, int] = {}
    kept = skipped = 0

    for el in elements:
        tag = (el.name or "").lower()
        if tag in SKIP_TAGS:
            skipped += 1
            continue

        attrs = el.attrs or {}
        text = clean_text(el.get_text(strip=True))
        feature_str = f"{tag} " + " ".join(f"{k}={clean_text(str(v))}" for k, v in attrs.items())
        if text:
            feature_str += " " + text

        # Default decision via ML probability
        keep = False
        try:
            X = vectorizer.transform([feature_str])
            proba = float(model.predict_proba(X)[0][1])
            keep = proba >= PROBA_THRESHOLD
        except Exception:
            # If vectorizer/model fail for any reason, fallback to heuristic
            proba = -1.0

        if not keep and has_good_attrs(attrs, text):
            keep = True  # heuristic rescue

        if not keep:
            continue

        xpath = get_xpath_bs(el)
        if not xpath:
            continue

        # Build a readable logical name
        label_bits = [
            text,
            attrs.get("placeholder"),
            attrs.get("aria-label"),
            attrs.get("name"),
            tag,
        ]
        label = clean_text(next((b for b in label_bits if b), tag))
        name = unique_name(label, used_names)

        locators[name] = xpath
        kept += 1

    out_path = os.path.join(INPUT_DIR, f"{page_name}_page.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(locators, f, indent=2)
    print(f"  ✅ Accepted: {kept} | ❎ Skipped tags: {skipped} | 🗂️ Saved → {out_path}")


# ----------------------- App flow -----------------------

def login_to_app(driver, settings, model, vectorizer):
    driver.get(settings["url"])
    driver.maximize_window()

    safe_find(driver, By.ID, "email", timeout=30)
    safe_find(driver, By.ID, "password", timeout=30)
    safe_find(driver, By.ID, "next", timeout=30)
    crawl_pages(driver, PAGE_BEFORE_LOGIN, model, vectorizer, settings)
    driver.find_element(By.ID, "email").send_keys(settings["login_username"])
    driver.find_element(By.ID, "password").send_keys(settings["login_password"])
    driver.find_element(By.ID, "next").click()

    # Landed page (Dashboard)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//p[.='Dashboard']")))
    wait_for_dom_stable(driver)
    print("🔐 Logged in successfully.")


def cancel_page(driver):
    if safe_click(driver, "//button//span[.='Cancel']", timeout=8):
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//p[.='Dashboard']")))
            wait_for_dom_stable(driver)
        except TimeoutException:
            pass


def crawl_pages(driver, pages: Dict[str, str], model, vectorizer, settings):
    for page_name, path in pages.items():
        print(f"\n➡️ Visiting: {page_name}")
        try:
            if path is None:
                # Special cases (e.g., dashboard right after login)
                pass
            elif path.startswith("http"):
                driver.get(path)
            else:
                safe_click(driver, path, timeout=12)

            extract_locators(driver, model, vectorizer, page_name)

        except Exception as e:
            print(f"❌ Could not open {page_name}: {e}")


def main():
    ensure_dirs()
    settings = load_settings()

    chrome_options = Options()
    # Honor CI flag for headless
    if str(settings.get("CI", "false")).lower() == "true":
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        model, vectorizer = load_model()
        login_to_app(driver, settings, model, vectorizer)

        # Primary crawl
        crawl_pages(driver, PAGES_PRIMARY, model, vectorizer, settings)

        # Optional interstitial actions
        cancel_page(driver)   # back to dashboard if we were on a modal/page
        # Open "Add user" UI (if present), then continue
        safe_click(driver, "//button//*[contains(@class,'user-plus')]", timeout=6)
        # Then crawl the "add patient" view
        crawl_pages(driver, PAGES_AFTER_ADD_USER, model, vectorizer, settings)

        print("\n✅ Crawling + locator extraction complete.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
