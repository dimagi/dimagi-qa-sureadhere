import os
import json
import re
import difflib
import time
from typing import Dict, Any, Iterable, List, Tuple, Optional
import platform
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import contextlib
import calendar
from collections import defaultdict
from datetime import datetime, date, timedelta
from selenium.common.exceptions import (
        TimeoutException,
        StaleElementReferenceException,
        JavascriptException,
        )

# ---- Tunables ---------------------------------------------------------------

PRIMARY_TIMEOUT = 6         # seconds for fast checks
CLICK_TIMEOUT = 15          # seconds for user actions
VISIBLE_REQUIRED = True     # only accept visible elements
SIM_THRESHOLD = 0.62        # fuzzy match threshold for text-ish attrs
MIN_STABLE_PREFIX = 3       # for dynamic-id starts-with heuristics
PERSIST_HEALED = True       # write healed selectors to self_healed/<page>.json

# ---- Helpers ----------------------------------------------------------------

def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _norm(a).lower(), _norm(b).lower()).ratio()

def _stable_prefix(s: str) -> Optional[str]:
    # take non-trivial prefix up to first obvious dynamic chunk (digits/_/-)
    # e.g., "email_input_123" -> "email_input_"
    m = re.match(r"([A-Za-z-]+)", s or "")
    if m and len(m.group(1)) >= MIN_STABLE_PREFIX:
        return m.group(1)
    return None

def _xpath_attr_contains(attr: str, value: str) -> str:
    return f"contains(@{attr}, {_xpath_literal(value)})"

def _xpath_attr_equals(attr: str, value: str) -> str:
    return f"@{attr}={_xpath_literal(value)}"

def _xpath_literal(s: str) -> str:
    # safe XPath string literal
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    # if both quote types present, concat:
    parts = s.split("'")
    return "concat(" + ", \"'\", ".join([f"'{p}'" for p in parts]) + ")"

def _and(parts: Iterable[str]) -> str:
    parts = [p for p in parts if p]
    return " and ".join(parts)

def _wrap_unique(xpath: str, index: int) -> str:
    return f"({xpath})[{index}]"

# ---- Core -------------------------------------------------------------------

class BasePage:
    """
    Self-healing BasePage for SeleniumBase.

    JSON per page (example keys):
    {
      "email": {
        "id": "email",
        "name": "Email Address",
        "placeholder": "Email Address",
        "aria-label": "Email Address",
        "type": "email",
        "tag": "input",
        "class": "input input-lg",
        "xpath": "//input[@id='email']",
        "alternates": [
          "//label[normalize-space()='Email']/following::input[1]"
        ]
      },
      ...
    }
    """
    _resolved_cache: Dict[Tuple[str, str], str] = {}

    def __init__(self, sb, page_name: Optional[str] = None):
        self.sb = sb
        self.driver = sb.driver
        self.page_name = page_name
        self.locators = self._load_page_locators(page_name) if page_name else {}

    # ----------------- Locator loading & persistence -------------------------

    def _locators_dir(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "self_healing_locators")

    def _healed_dir(self) -> str:
        return os.path.join(self._locators_dir(), "self_healed")

    def _page_json_path(self, page: str, healed: bool = False) -> str:
        base = self._healed_dir() if healed else self._locators_dir()
        return os.path.join(base, f"{page}.json")

    def _load_page_locators(self, page_name: str) -> Dict[str, Any]:
        raw_path = self._page_json_path(page_name, healed=False)
        healed_path = self._page_json_path(page_name, healed=True)

        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Locator file not found: {raw_path}")

        with open(raw_path, "r", encoding="utf-8") as f:
            base = json.load(f)

        if os.path.exists(healed_path):
            with open(healed_path, "r", encoding="utf-8") as f:
                healed = json.load(f)
            # Deep-merge each locator so we KEEP tag/class/aria-colindex from base
            for k, v in healed.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    base[k] = {**base[k], **v}
                else:
                    base[k] = v

        return base

    # add near the top of the class (utilities section)

    # ---------- Scoped & strict resolution ---------------------------------

    def resolve_strict(self, logical_name: str) -> str:
        """Return only the literal selector from JSON (no healed/candidates)."""
        entry = self.locators.get(logical_name) or {}
        for sel in [entry.get("xpath"), entry.get("css")]:
            if sel:
                # keep your attribute guard on strict too
                ok = self._try_selector(sel, entry, timeout=2)
                if ok:
                    return ok
        # return base even if not present to fail fast where it's used
        return entry.get("xpath") or entry.get("css") or ""

    def _resolve_selector(self, logical_name: str, *, strict: bool = False):
        """Selector → (By, value) with optional strict mode to bypass healing."""
        sel = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)
        return self._by_tuple(sel)

    def _find_unique_in(self, root, by, value, *, logical_name: str, timeout: int = 6):
        """Find exactly ONE match under the given root; raise if 0 or >1."""
        import time
        end = time.monotonic() + timeout
        last = []
        while time.monotonic() < end:
            els = (root if hasattr(root, "find_elements") else self.driver).find_elements(by, value)
            last = els
            if len(els) == 1:
                return els[0]
            time.sleep(0.1)
        raise AssertionError(
            f"Locator for '{logical_name}' matched {len(last)} elements under scope (wanted 1): {by}={value}"
            )

    def _lookup(self, logical_name: str, *, within=None, strict: bool = False, timeout: int = 6):
        """
        Resolve logical_name to a unique WebElement.
          within: None | WebElement | logical name of a container
          strict: bypass/limit healing to avoid cross-widget jumps
        """
        by, value = self._resolve_selector(logical_name, strict=strict)
        # decide scope root
        if within is None:
            root = self.driver
        elif hasattr(within, "tag_name"):
            root = within
        else:
            w_by, w_val = self._resolve_selector(within, strict=True)
            root = self._find_unique_in(self.driver, w_by, w_val, logical_name=f"{within} (scope)", timeout=timeout)
        return self._find_unique_in(root, by, value, logical_name=logical_name, timeout=timeout)

    def _healed_path(self, page_name: str) -> str:
        os.makedirs(self._healed_dir(), exist_ok=True)
        return self._page_json_path(page_name, healed=True)

    def _load_healed_page(self, page_name: str) -> dict:
        path = self._healed_path(page_name)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_healed_page(self, page_name: str, data: dict) -> None:
        path = self._healed_path(page_name)
        if not data:
            with contextlib.suppress(Exception):
                os.remove(path)
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def unheal(self, logical_name: str) -> bool:
        """Remove a healed locator for the current page & clear caches (safe even if no in-mem store)."""
        page = self.page_name
        healed = self._load_healed_page(page)
        if logical_name in healed:
            healed.pop(logical_name, None)
            self._save_healed_page(page, healed)
            # clear caches (both tuple and plain key styles)
            try:
                self._resolved_cache.pop((page or "", logical_name), None)
                self._resolved_cache.pop(logical_name, None)
            except Exception:
                pass
            return True
        return False

    # replace your _looks_generic_xpath(...) with a bound method (or @staticmethod) and call it correctly
    def _looks_generic_xpath(self, xp: str) -> bool:
        s = (xp or "").strip()
        # //tag or //tag[1]
        if re.fullmatch(r"//\w+(\[\d+\])?", s):
            return True
        # uses only @class in predicates (contains/starts-with/etc.)
        if "@class" in s:
            attrs = re.findall(r"@([a-zA-Z0-9\-\:_]+)", s)
            if all(a == "class" for a in attrs):
                return True
        return False

    def _resolve_runtime(self, logical_name: str, entry: Dict[str, Any]) -> str:
        cands = list(self._candidates_for(entry))
        # If JSON already had an explicit selector, push class-only guesses to the back
        if entry.get("xpath") or entry.get("css"):
            generic = [c for c in cands if self._looks_generic_xpath(c)]
            strong = [c for c in cands if not self._looks_generic_xpath(c)]
            cands = strong + generic

        for cand in cands:
            elems = self._query(cand)
            if not elems:
                continue
            if len(elems) == 1 and self._score_element(elems[0], entry) > 0:
                return cand
            scores = [(i + 1, self._score_element(e, entry)) for i, e in enumerate(elems)]
            best_index, best_score = max(scores, key=lambda t: t[1]) if scores else (None, 0)
            if best_index and best_score > 0 and (cand.strip().startswith("//") or cand.strip().startswith("(")):
                return _wrap_unique(cand, best_index)
        raise Exception(f"No working locator found for '{logical_name}' on page '{self.page_name}'")

    def unheal_all(self, *logical_names: str) -> None:
        for name in logical_names:
            with contextlib.suppress(Exception):
                self.unheal(name)

    def _persist_healed(self, logical_name: str, final_sel: str):
        if not (PERSIST_HEALED and self.page_name and final_sel):
            return
        s = final_sel.strip()
        is_xpath = s.startswith(("//", "(", ".//"))

        # Don’t persist super-generic heals like //td, //div, or class-only td
        if is_xpath and self._looks_generic_xpath(s):
            return

        healed = self._load_healed_page(self.page_name)
        entry = dict(healed.get(logical_name, {}))

        # keep alternates (dedup, cap)
        alts = list(dict.fromkeys([s] + entry.get("alternates", [])))[:10]
        entry["alternates"] = alts
        # store under the right key (prefer xpath; resolve() already tries xpath then css)
        if is_xpath:
            entry["xpath"] = s
            entry.pop("css", None)
        else:
            entry["css"] = s
            entry.pop("xpath", None)

        healed[logical_name] = entry
        self._save_healed_page(self.page_name, healed)

    # ----------------- Candidate generation ----------------------------------

    def _class_has_tokens(self, el, needed: str) -> bool:
        if not needed: return True
        have = (el.get_attribute("class") or "")
        have_tokens = set(have.split())
        need_tokens = [t for t in needed.split() if t]
        return all(t in have_tokens for t in need_tokens)

    def _candidate_matches_entry(self, el, entry: dict) -> bool:
        """Hard-guard: ensure found element matches key JSON attributes."""
        # tag guard
        tag = (entry.get("tag") or "").lower().strip()
        if tag and (el.tag_name or "").lower().strip() != tag:
            return False
        # aria-colindex guard
        col = entry.get("aria-colindex")
        if col is not None:
            if (el.get_attribute("aria-colindex") or "").strip() != str(col):
                return False
        # class tokens guard (token-based, not substring)
        cls = entry.get("class") or ""
        if cls and not self._class_has_tokens(el, cls):
            return False
        return True

    def _selector_to_by(self, sel: str):
        from selenium.webdriver.common.by import By
        sel = sel.strip()
        if sel.startswith(("//", "(.", "(.//", ".//", "(")):
            return (By.XPATH, sel)
        if sel.startswith("/") or sel.startswith("("):
            return (By.XPATH, sel)
        if sel.startswith("#") or sel.startswith(".") or ":" in sel or "[" in sel:
            return (By.CSS_SELECTOR, sel)
        # default to XPATH
        return (By.XPATH, sel)

    def _try_selector(self, sel: str, entry: dict, timeout: int):
        """Return selector if it finds a matching element that passes attribute guard."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        by = self._selector_to_by(sel)
        try:
            el = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(by))
            # Attribute guard: ensure it’s the intended element (e.g., aria-colindex='2')
            if self._candidate_matches_entry(el, entry):
                return sel
        except Exception:
            pass
        return None

    def _candidates_for(self, entry: Dict[str, Any]) -> List[str]:
        tag = entry.get("tag") or "*"

        # 1) Explicit selectors first
        xs: List[str] = []
        if entry.get("xpath"):  xs.append(entry["xpath"])
        if entry.get("css"):    xs.append(self._css_to_xpath(entry["css"]))

        # 2) Strong attribute equals
        strong_attrs = ["id", "data-testid", "name"]
        for a in strong_attrs:
            v = entry.get(a)
            if v:
                xs.append(f"//{tag}[{_xpath_attr_equals(a, v)}]")

        # 3) Label-anchored (for inputs/buttons)
        label_text = entry.get("label") or entry.get("text")
        if label_text:
            # exact label then nearest control
            xs.append(f"//label[normalize-space()={_xpath_literal(label_text)}]"
                      f"/following::{'*' if tag == '*' else tag}[1]")
            # contains label text
            xs.append(f"//label[contains(normalize-space(), {_xpath_literal(label_text)})]"
                      f"/following::{'*' if tag == '*' else tag}[1]")

        # 4) Attribute combos (equals)
        # inside your candidate builder, add aria-colindex to equality attributes
        combo_attrs = [
            "id", "name", "type", "placeholder", "aria-label", "role",
            "data-testid", "data-id", "data-value", "aria-colindex"  # <--- add this
            ]

        # combo_attrs = ["placeholder", "aria-label", "type", "class", "data-icon", "aria-colindex"]
        equals_parts = [_xpath_attr_equals(a, entry[a]) for a in combo_attrs if entry.get(a)]
        if equals_parts:
            xs.append(f"//{tag}[{_and(equals_parts)}]")

        # 5) Fuzzy/dynamic variants (starts-with / contains)
        for a in ["id", "name", "class"]:
            v = entry.get(a)
            if not v:
                continue
            pref = _stable_prefix(v)
            if pref:
                xs.append(f"//{tag}[starts-with(@{a}, {_xpath_literal(pref)})]")
            xs.append(f"//{tag}[{_xpath_attr_contains(a, v)}]")  # soft match

        for a in ["placeholder", "aria-label"]:
            v = entry.get(a)
            if v:
                xs.append(f"//{tag}[contains(normalize-space(@{a}), {_xpath_literal(_norm(v))})]")

        # 6) Text-based (for buttons/labels): exact then contains
        txt = entry.get("text")
        if txt:
            xs.append(f"//{tag}[normalize-space()={_xpath_literal(_norm(txt))}]")
            xs.append(f"//{tag}[contains(normalize-space(), {_xpath_literal(_norm(txt))})]")

        # 7) Last-resort: tag + type
        if entry.get("type"):
            xs.append(f"//{tag}[@type={_xpath_literal(entry['type'])}]")
        # ultra last resort: the bare tag (filtered later by scoring/uniqueness)
        xs.append(f"//{tag}")

        # de-duplicate while preserving order
        seen, ordered = set(), []
        for q in xs:
            if q not in seen:
                seen.add(q)
                ordered.append(q)
        return ordered

    def _css_to_xpath(self, css: str) -> str:
        # Very light converter for simple [attr=value] selectors; for anything complex,
        # SeleniumBase accepts CSS directly; we prefer XPath for text/contains logic.
        # If CSS looks non-trivial, just return as-is and we'll let SeleniumBase use it.
        if re.search(r"[>+~:]", css):
            return css  # let sb handle CSS directly
        # naive: div#id.class[attr="v"] -> //div[@id='id' and contains(@class,'class') and @attr='v']
        tag = "*"
        m = re.match(r"^([a-zA-Z][\w-]*)", css)
        if m: tag = m.group(1)
        idm = re.search(r"#([\w-]+)", css)
        cls = re.findall(r"\.([\w-]+)", css)
        attrs = re.findall(r"\[([\w-]+)=['\"]?([^'\"]+)['\"]?\]", css)
        parts = []
        if idm: parts.append(_xpath_attr_equals("id", idm.group(1)))
        for c in cls: parts.append(f"contains(@class,{_xpath_literal(c)})")
        for k, v in attrs: parts.append(_xpath_attr_equals(k, v))
        return f"//{tag}[{_and(parts)}]" if parts else f"//{tag}"

    # ----------------- Resolution & scoring ----------------------------------

    def _score_element(self, el, entry: Dict[str, Any]) -> float:
        score = 0.0
        try:
            if VISIBLE_REQUIRED and not el.is_displayed():
                return 0.0
            tag = (el.tag_name or "").lower()
            if entry.get("tag") and tag == (entry["tag"] or "").lower():
                score += 0.35
            for a in ["type", "placeholder", "aria-label", "name", "id", "class"]:
                want = entry.get(a)
                if not want:
                    continue
                have = (el.get_attribute(a) or "")
                if not have:
                    continue
                # stronger credit for exact match, some credit for fuzzy
                if _norm(have) == _norm(want):
                    score += 0.25
                else:
                    score += 0.15 * _sim(have, want)
            # visible text heuristic for non-inputs
            if entry.get("text"):
                text_sim = _sim(el.text or "", entry["text"])
                if text_sim >= SIM_THRESHOLD:
                    score += 0.25 * text_sim
        except StaleElementReferenceException:
            return 0.0
        return score

    def _query(self, selector: str) -> List:
        # Accept both XPath and CSS
        is_xpath = selector.strip().startswith(("//", "(")) or "[contains(" in selector or "@" in selector
        try:
            if is_xpath:
                return self.driver.find_elements(By.XPATH, selector)
            return self.driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            return []

    def _get_webelement(self, selector: str, timeout: int = PRIMARY_TIMEOUT):
        """
        Robustly return a WebElement from a selector string.
        Uses SeleniumBase if available; otherwise falls back to raw Selenium.
        """
        # Try SeleniumBase API if present
        try:
            getter = getattr(self.sb, "get_webelement", None)
            if callable(getter):
                return getter(selector)
        except Exception:
            pass

        # Fallback: detect selector type and use driver directly
        s = (selector or "").strip()
        is_xpath = s.startswith(("//", "(", ".//")) or "@" in s
        by = By.XPATH if is_xpath else By.CSS_SELECTOR
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, s)))
        return self.driver.find_element(by, s)

    def resolve(self, logical_name: str, timeout: int = PRIMARY_TIMEOUT) -> str:
        key = (self.page_name or "", logical_name)
        if key in self._resolved_cache:
            return self._resolved_cache[key]

        entry = self.locators.get(logical_name)
        if not entry:
            raise KeyError(f"Locator '{logical_name}' not found in {self.page_name}")

        # 1) HARD preference for explicit selectors from JSON
        # 1) HARD preference for explicit selectors from JSON (attribute-guarded)
        explicit = entry.get("xpath") or entry.get("css")
        if explicit:
            quick = min(timeout, 8)
            ok = self._try_selector(explicit, entry, timeout=quick)
            if ok:
                self._resolved_cache[key] = explicit
                return explicit
            # else fall through to alternates / healing

        # 2) Alternates (if any) — also attribute-guarded
        for alt in entry.get("alternates", []):
            ok = self._try_selector(alt, entry, timeout=3)
            if ok:
                self._resolved_cache[key] = alt
                if PERSIST_HEALED:
                    self._persist_healed(logical_name, alt)
                return alt

        # 3) Self-healing
        healed = self._resolve_runtime(logical_name, entry)
        try:
            self.sb.wait_for_element(healed, timeout=timeout)
        except Exception:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, healed))
                )
        self._resolved_cache[key] = healed
        if PERSIST_HEALED:
            self._persist_healed(logical_name, healed)
        return healed

    # ----------------- Public actions (compatible API) -----------------------
    def convert_date(self, date_str: str) -> str:
        # Possible input formats
        formats = ["%b %d, %Y", "%b %-d, %Y", "%b %#d, %Y"]
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y/%m/%d")
            except ValueError:
                continue
        raise ValueError(f"Date format not recognized: {date_str}")

    def wait_for_element(self, logical_name: str, timeout: int = CLICK_TIMEOUT):
        sel = self.resolve(logical_name)
        self.sb.wait_for_element(sel, timeout=timeout)

    def find_elements(self, logical_name: str, timeout: int = CLICK_TIMEOUT):
        sel = self.resolve_strict(logical_name)
        print(sel)
        try:
            # Wait for at least one element to be present
            self.sb.wait_for_element_present(sel, timeout=timeout)
        except TimeoutException:
            return []

        # Return all currently matching elements
        return self.sb.find_elements(sel)

    def go_back(self):
        """Go back one page in browser history."""
        self.sb.go_back()
        time.sleep(5)

    def click(self, logical_name: str, timeout: int = CLICK_TIMEOUT, strict: bool = False):
        if strict == False:
            sel = self.resolve(logical_name)
        else:
            sel = self.resolve_strict(logical_name)
        self.sb.wait_for_element_clickable(sel, timeout=timeout)
        self.sb.highlight(sel)
        self.sb.click(sel)

    def refresh(self):
        self.sb.refresh_page()
        self.wait_for_page_to_load()

    def type(self, logical_name: str, value: str, timeout: int = CLICK_TIMEOUT):
        sel = self.resolve(logical_name)
        self.sb.wait_for_element(sel, timeout=timeout)
        # self.sb.highlight(sel)
        self.sb.type(sel, value)


    def type_and_trigger(self, logical_name: str, text: str, *,
                         timeout: int = 15, blur: bool = True, clear_first: bool = True):
        """Type into a text field/textarea and fire the events Kendo expects."""
        sel = self.resolve(logical_name)
        el = self._get_webelement(sel, timeout=timeout)

        # bring into view & focus
        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].focus();", el)
        el.click()

        # clear reliably
        if clear_first:
            try:
                el.clear()
            except Exception:
                el.send_keys(Keys.CONTROL, "a", Keys.DELETE)

        # native typing (helps some validators)
        el.send_keys(text)

        # explicitly fire the events many Kendo inputs listen to
        self.driver.execute_script("""
            const e = arguments[0], val = arguments[1];
            if (e.value !== val) { e.value = val; }     // ensure value is correct
            for (const t of ['input','keyup','change']) {
                e.dispatchEvent(new Event(t, {bubbles: true}));
            }
        """, el, text
                                   )

        # optional blur to finalize
        if blur:
            with contextlib.suppress(Exception):
                el.send_keys(Keys.TAB)
            with contextlib.suppress(Exception):
                self.driver.execute_script("arguments[0].blur();", el)
        time.sleep(0.05)  # tiny settle

    def clear(self, logical_name: str, timeout: int = CLICK_TIMEOUT):
        sel = self.resolve(logical_name)
        self.sb.wait_for_element(sel, timeout=timeout)
        self.sb.highlight(sel)
        self.sb.clear(sel)

    def get_text(self, logical_name: str, timeout: int = PRIMARY_TIMEOUT, strict: bool = False) -> str:
        if strict == False:
            sel = self.resolve(logical_name)
        else:
            sel = self.resolve_strict(logical_name)
        self.sb.wait_for_element(sel, timeout=timeout)
        self.sb.highlight(sel)
        return self.sb.get_text(sel)

    def is_element_present(self, logical_name: str, strict: bool = False, timeout: int = 0) -> bool:
        try:
            locator = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)

            if not locator:
                return False

            if timeout > 0:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, locator))
                    )
                return True
            else:
                return len(self.driver.find_elements(By.XPATH, locator)) > 0
        except Exception:
            return False

    def is_element_visible(self, logical_name: str, strict: bool = False) -> bool:
        try:
            sel = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)
            return self.sb.is_element_visible(sel)
        except Exception:
            return False

    def is_element_enabled(self, logical_name: str) -> bool:
        try:
            sel = self.resolve(logical_name)
            return self.sb.is_element_enabled(sel)
        except Exception:
            return False

    def select_option_by_text(self, logical_name: str, option_text: str):
        sel = self.resolve(logical_name)
        self.sb.select_option_by_text(sel, option_text)

    def element_exists(self, logical_name: str) -> bool:
        try:
            sel = self.resolve(logical_name)
            return self.sb.is_element_present(sel)
        except Exception:
            return False

    def launch_url(self, url: str):
        self.sb.open(url)
        self.sb.wait_for_ready_state_complete(timeout=CLICK_TIMEOUT)

    def wait_for_page_to_load(self, timeout=50):
        self.sb.wait_for_ready_state_complete(timeout=timeout)

    def verify_page_title(self, title, timeout=50):
        WebDriverWait(self.sb.driver, timeout).until(EC.title_contains(title))
        actual_title = self.sb.get_title()
        print(f"Page title: {actual_title}")
        self.sb.assert_title(title)  # Or use self.assert_title_contains()

    # inside class BasePage
    def kendo_select(
            self,
            input_logical_name: str,
            text: str | list | tuple | None = None,
            index: int = 0,
            match: str = "exact",  # "exact" | "contains" | "startswith"
            timeout: int = CLICK_TIMEOUT
            ):
        """
        Select an item from a Kendo dropdown/listbox without relying on stable IDs.

        Works even if the popup is rendered elsewhere (attached to <body>) and
        IDs change on every render. If 'text' is provided, selects by text
        (case-insensitive). Otherwise selects by zero-based 'index'.
        """
        sel = self.resolve(input_logical_name)
        wait = WebDriverWait(self.driver, timeout)

        # Open the dropdown
        self.sb.wait_for_element_clickable(sel, timeout=timeout)
        inp = self._get_webelement(sel, timeout=timeout)
        inp.click()
        if (inp.get_attribute("aria-expanded") or "").lower() != "true":
            try:
                inp.send_keys(Keys.ALT, Keys.ARROW_DOWN)
            except Exception:
                pass

        # Prefer the live listbox by aria-controls/aria-owns; otherwise the only visible Kendo popup
        list_id = inp.get_attribute("aria-controls") or inp.get_attribute("aria-owns")
        if list_id:
            base = f"//*[@id={_xpath_literal(list_id)}]"
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, base)))
            except TimeoutException:
                inp.click()
                wait.until(EC.presence_of_element_located((By.XPATH, base)))
        else:
            base = ("//div[contains(@class,'k-animation-container') and "
                    "not(contains(@style,'display: none'))]"
                    "//*[contains(@class,'k-list') or @role='listbox']")

        # Text selection (case-insensitive) or index selection
        if text is not None:
            if isinstance(text, (list, tuple)):
                text = next((t for t in text if t), "")
            needle = re.sub(r"\s+", " ", str(text).strip()).lower()
            lower_expr = ("translate(normalize-space(.), "
                          "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')")

            if match == "startswith":
                pred = f"starts-with({lower_expr}, {_xpath_literal(needle)})"
            elif match == "contains":
                pred = f"contains({lower_expr}, {_xpath_literal(needle)})"
            else:  # exact
                pred = f"{lower_expr}={_xpath_literal(needle)}"

            opt_xpath = (f"{base}//*[@role='option' and not(contains(@class,'k-disabled')) and {pred}]")
            try:
                option = wait.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
                self.sb.highlight(option)
                option.click()
                return
            except TimeoutException:
                # Keyboard fallback: type to filter, then ENTER the active item
                try:
                    inp.clear()
                except Exception:
                    pass
                inp.send_keys(text)
                wait.until(lambda d: (inp.get_attribute('aria-activedescendant') or '').strip() != "")
                inp.send_keys(Keys.ENTER)
                return

        # Select by index (0-based)
        one_based = max(1, index + 1)
        opt_xpath = (f"({base}//*[@role='option' and not(contains(@class,'k-disabled'))])[{one_based}]")
        option = wait.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
        self.sb.highlight(option)
        option.click()

    def kendo_select_first(self, input_logical_name: str, timeout: int = CLICK_TIMEOUT):
        """Convenience: select the first visible option."""
        return self.kendo_select(input_logical_name, text=None, index=0, timeout=timeout)

    def get_attribute(
            self,
            logical_name: str,
            attribute: str = "value",
            timeout: int = 10,
            wait_for_nonempty: bool = False,
            normalize: bool = True,
            retries: int = 2,
            strict: bool = False,
            ):
        """
        Return an attribute from an element resolved via your locator JSON.

        - Uses SeleniumBase's get_attribute() when available.
        - Falls back to WebElement.get_attribute() and a JS property read.
        - Optionally waits for a non-empty value and normalizes whitespace.
        """
        selector = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)

        # 1) Try SeleniumBase (if available on your test object)
        try:
            val = self.sb.get_attribute(selector, attribute)
            if wait_for_nonempty:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: (self.sb.get_attribute(selector, attribute) or "").strip() != ""
                    )
                val = self.sb.get_attribute(selector, attribute)
            if normalize and isinstance(val, str):
                val = re.sub(r"\s+", " ", val).strip()
            # Special-case fallback for Kendo/ARIA when asking for 'value'
            if attribute == "value" and (val is None or (isinstance(val, str) and val == "")):
                alt = self.sb.get_attribute(selector, "aria-valuetext")
                if alt:
                    return alt.strip() if normalize else alt
            return val
        except Exception:
            pass  # fall through to raw Selenium

        # 2) Raw Selenium with stale retries + JS property fallback
        last_exc = None
        for _ in range(max(1, retries + 1)):
            try:
                el = self._get_webelement(selector, timeout=timeout)

                if wait_for_nonempty:
                    WebDriverWait(self.driver, timeout).until(
                        lambda d: (el.get_attribute(attribute) or "").strip() != ""
                        )

                val = el.get_attribute(attribute)

                # If still None (or empty when we care), try JS property and ARIA alt
                if val is None:
                    try:
                        val = self.driver.execute_script(
                            "return arguments[0][arguments[1]] ?? arguments[0].getAttribute(arguments[1]);",
                            el, attribute
                            )
                    except Exception:
                        pass

                if attribute == "value" and (val is None or val == ""):
                    alt = el.get_attribute("aria-valuetext")
                    if alt:
                        val = alt

                if normalize and isinstance(val, str):
                    val = re.sub(r"\s+", " ", val).strip()

                return val
            except StaleElementReferenceException as e:
                last_exc = e
                time.sleep(0.15)  # brief retry backoff
                continue

        raise last_exc or TimeoutException(f"Could not get attribute '{attribute}' for '{logical_name}'")

    def get_value(self, logical_name: str, **kwargs):
        """Convenience: get the 'value' of an input."""
        return self.get_attribute(logical_name, "value", **kwargs)

    def is_checked(self, logical_name: str) -> bool:
        """Convenience: returns True if a checkbox/radio is checked."""
        val = self.get_attribute(logical_name, "checked", normalize=False)  # bool or "true"/None
        # Selenium returns "true"/None for boolean attrs; some drivers return True/False
        return bool(val) and str(val).lower() != "false"

    # --- Gone / absent waits -------------------------------------------------
    def _by_tuple(self, selector):
        # Already a (By, value) pair
        if isinstance(selector, tuple) and len(selector) == 2:
            return selector

        s = (selector or "").strip()

        # Explicit prefixes (opt-in)
        for prefix, by in [
            ("xpath=", By.XPATH),
            ("css=", By.CSS_SELECTOR),
            ("id=", By.ID),
            ("name=", By.NAME),
            ("class=", By.CLASS_NAME),
            ("link=", By.LINK_TEXT),
            ("plink=", By.PARTIAL_LINK_TEXT),
            ("tag=", By.TAG_NAME),
            ]:
            if s.lower().startswith(prefix):
                return (by, s[len(prefix):])

        # Heuristic: XPath vs CSS
        is_xpath = s.startswith(("//", "(", ".//")) or "@" in s
        return (By.XPATH, s) if is_xpath else (By.CSS_SELECTOR, s)

    def wait_for_gone(
        self,
        logical_name: str,
        timeout: int = CLICK_TIMEOUT,
        mode: str = "auto",           # "auto" | "invisible" | "stale" | "detached"
        poll_frequency: float = 0.2,
    ) -> bool:
        """
        Wait until the element is considered "gone".

        mode:
          - "invisible":  not visible (may still be in DOM)
          - "stale":      previously located node becomes stale (detached/re-rendered)
          - "detached":   no matching nodes remain in DOM
          - "auto":       try invisible -> stale -> detached (in that order)

        Returns True on success; raises TimeoutException otherwise.
        """
        selector = self.resolve(logical_name)
        by = self._by_tuple(selector)
        wait = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency)

        if mode == "invisible":
            return wait.until(EC.invisibility_of_element_located(by))

        if mode == "stale":
            try:
                el = self._get_webelement(selector, timeout=2)
            except Exception:
                return True  # already gone
            return wait.until(EC.staleness_of(el))

        if mode in ("detached", "absent", "removed"):
            return wait.until(lambda d: len(self._query(selector)) == 0)

        # auto: invisible -> stale -> detached
        try:
            if wait.until(EC.invisibility_of_element_located(by)):
                return True
        except TimeoutException:
            pass

        try:
            el = self._get_webelement(selector, timeout=1)
            if wait.until(EC.staleness_of(el)):
                return True
        except Exception:
            return True  # element not present already

        return wait.until(lambda d: len(self._query(selector)) == 0)

    # Convenience aliases
    def wait_for_absent(self, logical_name: str, timeout: int = CLICK_TIMEOUT) -> bool:
        """Strictly 'removed from DOM' (no matching nodes remain)."""
        return self.wait_for_gone(logical_name, timeout=timeout, mode="detached")

    def wait_for_invisible(self, logical_name: str, timeout: int = CLICK_TIMEOUT) -> bool:
        """Element may remain in DOM but must not be visible."""
        return self.wait_for_gone(logical_name, timeout=timeout, mode="invisible")

    def wait_for_field_value_contains(self, logical_name, substring, timeout=15):
        sel = self.resolve(logical_name)
        self.sb.wait_for_attribute(sel, "value", substring, timeout=timeout)  # contains
        return True
    # ---------- internals for Kendo Angular DropDownList ------------------------
    def _dd_is_open(self, root):
        try:
            return (root.get_attribute("aria-expanded") or "").lower() == "true"
        except Exception:
            return False

    def _dd_open(self, root, timeout):
        if self._dd_is_open(root): return
        btn = None
        for css in ("button[aria-label]", ".k-input-button", ".k-select", "button.k-button-icon"):
            f = root.find_elements(By.CSS_SELECTOR, css)
            if f: btn = f[0]; break
        (btn or root).click()
        WebDriverWait(self.driver, timeout).until(lambda d: self._dd_is_open(root))

    def _dd_get_display_text(self, root) -> str:
        return (self.driver.execute_script("""
            const r = arguments[0];
            const n = r.querySelector('.k-input-value-text, .k-input-inner, .k-input, .k-input-text');
            return n && n.textContent ? n.textContent.trim() : '';
        """, root
                                           ) or "").strip()

    def _dd_combobox_input(self, root):
        """Return the inner input element that controls the popup (if any)."""
        for css in (
                "input[role='combobox']",
                "input.k-input-inner",
                "input.k-input",
                "input[aria-haspopup='listbox']",
                ):
            els = root.find_elements(By.CSS_SELECTOR, css)
            if els:
                return els[0]
        return None

    def _dd_close(self, root, timeout):
        if not self._dd_is_open(root): return
        try:
            f = root.find_elements(By.CSS_SELECTOR, ".k-input-button, .k-select")
            (f[0] if f else root).click()
        except Exception:
            try:
                root.send_keys(Keys.ESCAPE)
            except Exception:
                pass
        WebDriverWait(self.driver, timeout).until(lambda d: not self._dd_is_open(root))

    # ── New: find filter input if popup is filterable ───────────────────────────

    def _dd_try_filter(self, popup, text: str) -> bool:
        # common filter inputs inside popup across Kendo Angular skins
        for css in [
            "input.k-input-inner",  # new
            "input.k-textbox",  # older
            "input[role='textbox']",
            ".k-filter input",  # filter container
            ".k-searchbar input"  # search bar
            ]:
            els = popup.find_elements(By.CSS_SELECTOR, css)
            if els:
                box = els[0]
                box.clear()
                box.send_keys(text)
                # small debounce for filtering to apply
                time.sleep(0.25)
                return True
        return False

    # ── New: scroll virtualized list until option appears ───────────────────────

    def _dd_scroll_until_option(self, popup, opt_xpath: str, timeout: int) -> bool:
        """
        Scrolls the list container in steps until an element matching opt_xpath appears.
        Returns True if found, False otherwise.
        """
        # find a scrollable container
        scroll = None
        for css in [
            ".k-virtual-scrollable-wrap",
            ".k-virtual-content",
            ".k-list-scroller",
            ".k-list-content",
            ".k-list",
            ".k-popup-content"
            ]:
            els = popup.find_elements(By.CSS_SELECTOR, css)
            if els:
                scroll = els[0];
                break
        if not scroll:
            # try the popup itself
            scroll = popup

        end = time.monotonic() + timeout
        last_top = -1
        step = 400  # px per scroll step; adjust if your rows are large

        while time.monotonic() < end:
            # present?
            if self.driver.find_elements(By.XPATH, opt_xpath):
                return True

            # scroll down
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];", scroll, step)
            time.sleep(0.15)
            cur_top = self.driver.execute_script("return arguments[0].scrollTop;", scroll)

            # reached bottom or not moving?
            max_top = self.driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;",
                                                 scroll
                                                 )
            if cur_top == last_top or cur_top >= max_top:
                break
            last_top = cur_top

        # one last check
        return bool(self.driver.find_elements(By.XPATH, opt_xpath))

    # ── Upgraded: select by VISIBLE TEXT with filter/scroll support ─────────────

    def auto_scope_root(self, logical_name: str, *, strict: bool = True):
        el = self._lookup(logical_name, strict=strict)
        cur = el
        candidates = []
        while True:
            try:
                cur = cur.find_element(By.XPATH, "..")
            except Exception:
                break
            if not hasattr(cur, "tag_name"): break
            tag = (cur.tag_name or "").lower()
            cls = (cur.get_attribute("class") or "")
            rid = cur.get_attribute("id") or ""
            role = (cur.get_attribute("role") or "").lower()
            dataqa = cur.get_attribute("data-testid") or cur.get_attribute("data-qa") or cur.get_attribute("data-test")

            if tag in ("form", "fieldset", "section") or role in ("form", "dialog", "group", "region") \
                    or any(tok in cls for tok in
                           ("card", "dialog", "modal", "k-dialog", "k-window", "k-form", "panel", "drawer", "mat-card",
                            "ant-card")
                           ) \
                    or rid or dataqa:
                # ensure this ancestor is unique in DOM to avoid too-broad scopes
                by, val = By.XPATH, self._unique_xpath(cur)
                try:
                    _ = self._find_unique_in(self.driver, by, val, logical_name="auto-scope-check", timeout=1)
                    candidates.append(cur)
                    # keep going to prefer higher-level but still unique containers
                except Exception:
                    pass
        return candidates[-1] if candidates else self.driver

    def _unique_xpath(self, el):
        # rough unique XPath builder for scoping
        node = el
        parts = []
        while node and getattr(node, "tag_name", None):
            tag = node.tag_name.lower()
            rid = node.get_attribute("id")
            if rid:
                parts.append(f"//*[@id='{rid}']")
                break
            # 1-based index among same-tag siblings
            sibs = node.find_elements(By.XPATH, f"../{tag}")
            idx = 1
            for s in sibs:
                if s == node: break
                idx += 1
            parts.append(f"/{tag}[{idx}]")
            node = node.find_element(By.XPATH, "..")
        return "".join(reversed(parts)) or "/*"

    def kendo_dd_get_selected_text(self, logical_name: str, *, timeout: int = 10) -> str:
        sel = self.resolve(logical_name)
        el = self._get_webelement(sel, timeout=timeout)
        root = self._dd_root(el)
        txt = self._dd_get_display_text(root)
        if txt:
            return txt
        # last resort: input value if it’s a combobox-like control
        try:
            inp = root.find_element(By.CSS_SELECTOR, "input[role='combobox'], input.k-input-inner, input.k-input")
            return (inp.get_attribute("value") or "").strip()
        except Exception:
            return ""

    def kendo_dd_get_selected_text_scoped(self, logical_name: str, *, within=None, strict: bool = True,
                                          timeout: int = 10) -> str:
        el = self._lookup(logical_name, within=within, strict=strict, timeout=timeout)
        root = self._dd_root(el)  # your existing helper
        txt = self._dd_get_display_text(root)  # your existing helper
        if txt:
            return txt
        # last resort: combobox input value inside same root
        try:
            inp = root.find_element(By.CSS_SELECTOR, "input[role='combobox'], input.k-input-inner, input.k-input")
            return (inp.get_attribute("value") or "").strip()
        except Exception:
            return ""

    # --- Kendo Dialog (Angular) helpers -----------------------------------------

    def _kendo_dialog_xpaths(self, title: str | None):
        # If a title/message is given, match EITHER a titlebar OR the content text.
        if title:
            lit = self._xp_lit(title)
            t = (
                "["
                # titlebar text
                ".//*[contains(@class,'k-dialog-titlebar') or @class='k-window-title']"
                f"//*[normalize-space()={lit}]"
                " or "
                # content text (your 'Profile saved' case)
                ".//*[contains(@class,'k-dialog-content') or contains(@class,'k-window-content')]"
                f"[normalize-space()={lit}]"
                "]"
            )
        else:
            t = ""

        return [
            # Visible dialog hosted under animation container
            ("//div[contains(@class,'k-animation-container') and "
             "not(contains(@style,'display: none'))]"
             f"//div[contains(@class,'k-dialog') and not(contains(@style,'display: none'))]{t}"),
            # Role-based
            f"//*[@role='dialog' and not(contains(@style,'display: none'))]{t}",
            # Fallbacks (rare skins / direct component)
            f"//kendo-dialog//div[contains(@class,'k-dialog')]{t}",
            f"//div[contains(@class,'k-window') and not(contains(@style,'display: none'))]{t}",
            ]

    def _kendo_find_visible_dialog(self, title: str | None, timeout: int):
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)

        def _locate(_):
            for xp in self._kendo_dialog_xpaths(title):
                els = self.driver.find_elements(By.XPATH, xp)
                vis = [e for e in els if e.is_displayed()]
                if vis:
                    return vis[0]
            return False

        return wait.until(_locate)

    def _kendo_no_visible_dialog(self, title: str | None):
        for xp in self._kendo_dialog_xpaths(title):
            els = self.driver.find_elements(By.XPATH, xp)
            if any(e.is_displayed() for e in els):
                return False
        return True

    def kendo_dialog_wait_open(self, title: str | None = None, *, timeout: int = 15):
        """Wait until a visible Kendo dialog (optionally with a specific title) is open; returns the dialog root WebElement."""
        dlg = self._kendo_find_visible_dialog(title, timeout)
        try:
            self.sb.highlight(dlg)
        except Exception:
            pass
        return dlg

    def kendo_dialog_wait_close(self, title: str | None = None, *, timeout: int = 15) -> bool:
        """Wait until no visible dialog (optionally with that title) remains."""
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)
        return wait.until(lambda d: self._kendo_no_visible_dialog(title))

    def kendo_dialog_get_text(self, title: str | None = None, *, timeout: int = 10) -> str:
        """Return the visible text inside the dialog content area."""
        dlg = self.kendo_dialog_wait_open(title, timeout=timeout)
        xp = (".//*[contains(@class,'k-dialog-content') or contains(@class,'k-content') "
              "or contains(@class,'k-window-content')]")
        try:
            node = dlg.find_element(By.XPATH, xp)
            return (node.text or "").strip()
        except Exception:
            return (dlg.text or "").strip()

    def kendo_dialog_click_button(self, button_text: str, *, title: str | None = None,
                                  match: str = "exact", timeout: int = 15) -> None:
        """
        Click a button in the dialog by its visible text.
        match: 'exact' | 'contains' | 'startswith'
        """
        dlg = self.kendo_dialog_wait_open(title, timeout=timeout)

        if match == "exact":
            btn_xp = (".//button[contains(@class,'k-button')]"
                      f"[normalize-space(.)={self._xp_lit(button_text)} or "
                      f".//span[normalize-space(.)={self._xp_lit(button_text)}]]")
        elif match == "startswith":
            btn_xp = (".//button[contains(@class,'k-button')]"
                      f"[starts-with(normalize-space(.), {self._xp_lit(button_text)}) or "
                      f" starts-with(normalize-space(.//span), {self._xp_lit(button_text)})]")
        else:  # contains
            btn_xp = (".//button[contains(@class,'k-button')]"
                      f"[contains(normalize-space(.), {self._xp_lit(button_text)}) or "
                      f" contains(normalize-space(.//span), {self._xp_lit(button_text)})]")

        btn = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, btn_xp))
            )
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, btn_xp)))
            try:
                self.sb.highlight(btn)
            except Exception:
                pass
            btn.click()
        except Exception:
            # animation/overlay fallback
            self.driver.execute_script("arguments[0].click();", btn)

    def kendo_dialog_close(self, *, title: str | None = None, timeout: int = 10) -> None:
        """Click the dialog's ✕ close button (or send ESC) and wait for it to close."""
        dlg = self.kendo_dialog_wait_open(title, timeout=timeout)
        close_xp = ".//button[contains(@class,'k-dialog-close') or @aria-label='Close']"
        try:
            btn = dlg.find_element(By.XPATH, close_xp)
            try:
                self.sb.highlight(btn)
            except Exception:
                pass
            btn.click()
        except Exception:
            try:
                dlg.send_keys(Keys.ESCAPE)
            except Exception:
                # last resort: click overlay behind the dialog
                self.driver.execute_script("""
                    const overlay = document.querySelector('.k-overlay, .k-dialog-wrapper + .k-overlay');
                    if (overlay) overlay.click();
                """
                                           )
        self.kendo_dialog_wait_close(title, timeout=timeout)

    def kendo_dialog_find(self, xpath_inside_dialog: str, *, title: str | None = None,
                          timeout: int = 10):
        """Find an element *inside* the dialog by relative XPath and return it."""
        dlg = self.kendo_dialog_wait_open(title, timeout=timeout)
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f".{xpath_inside_dialog}"))
            )

    # ----- Safe literal & predicate builders ------------------------------------
    def _xp_lit(self, s: str) -> str:
        if s is None: return "''"
        s = str(s)
        if "'" not in s: return f"'{s}'"
        if '"' not in s: return f'"{s}"'
        parts = s.split("'")
        return "concat(" + ", \"'\", ".join([f"'{p}'" for p in parts]) + ")"

    def _class_tokens_pred(self, cls: str | None) -> str:
        if not cls: return "1=1"
        toks = [t for t in re.split(r"\s+", cls.strip()) if t]
        return " and ".join([f"contains(concat(' ', normalize-space(@class), ' '), ' {t} ')" for t in toks]) or "1=1"

    def _text_pred(self, text: str | None, match: str, ctx: str = "normalize-space(.)") -> str:
        if not text: return "1=1"
        lit = self._xp_lit(text)
        return {
            "exact": f"{ctx}={lit}",
            "contains": f"contains({ctx}, {lit})",
            "startswith": f"starts-with({ctx}, {lit})",
            }.get(match, f"{ctx}={lit}")

    def _attrs_pred(self, attrs: dict | None) -> str:
        if not attrs: return "1=1"
        preds = []
        for k, v in attrs.items():
            if v in (None, "", False): continue
            if k == "class":  # classes handled via _class_tokens_pred
                continue
            preds.append(f"@{k}={self._xp_lit(v)}")
        return " and ".join(preds) if preds else "1=1"

    # ----- Generic template renderer --------------------------------------------
    def render_xpath(self, logical_name: str, **params) -> str:
        """
        Render a JSON 'xpath_template' using:
          - tag/class/other attrs from entry + runtime params
          - match='exact|contains|startswith' to control text predicates
          - text_ctx='self|desc' to match on element text or descendant spans
          - attrs={} extra attribute constraints (e.g., {'role':'button'})
          - index=int to select the nth match (wraps the whole XPath)
        Placeholders available inside template:
          {tag} {class_pred} {attrs_pred} {text_pred} {desc_text_pred}
          {text}  (quoted literal of 'text' param)
        """
        entry = self.locators.get(logical_name) or {}
        tmpl = entry.get("xpath_template")
        if not tmpl:
            raise ValueError(f"{logical_name}: missing 'xpath_template' in {self.page_name}")

        # merge defaults from JSON
        defaults = entry.get("defaults", {})
        p = {**defaults, **params}

        tag = (entry.get("tag") or p.get("tag") or "*").strip()
        cls = entry.get("class") or p.get("class")
        match = (p.get("match") or "exact").lower()
        text = p.get("text")
        index = p.get("index")
        extra_attrs = p.get("attrs", {})

        # build macros
        class_pred = self._class_tokens_pred(cls)
        attrs_pred = self._attrs_pred(extra_attrs)
        text_pred_self = self._text_pred(text, match, "normalize-space(.)")
        text_pred_desc = self._text_pred(text, match, "normalize-space()")  # for descendant text nodes

        # fill template
        filled = tmpl.format(
            tag=tag,
            class_pred=class_pred,
            attrs_pred=attrs_pred,
            text_pred=text_pred_self,
            desc_text_pred=text_pred_desc,
            text=self._xp_lit(text)  # if template wants raw literal
            ).strip()

        # optional nth
        if index:
            filled = f"({filled})[{int(index)}]"
        return filled

    # ----- Convenience actions using the rendered XPath --------------------------
    def click_rendered(self, logical_name: str, timeout: int = 15, **params):
        xp = self.render_xpath(logical_name, **params)
        self.sb.wait_for_element_clickable(xp, timeout=timeout)
        self.sb.highlight(xp)
        self.sb.click(xp)

    def get_text_rendered(self, logical_name: str, timeout: int = 10, **params) -> str:
        xp = self.render_xpath(logical_name, **params)
        self.sb.wait_for_element_visible(xp, timeout=timeout)
        return self.sb.get_text(xp)

    def get_element_rendered(self, logical_name: str, timeout: int = 10, **params):
        xp = self.render_xpath(logical_name, **params)
        self.sb.wait_for_element(xp, timeout=timeout)
        return self._get_webelement(xp, timeout=timeout)

    def _dd_listbox(self, root, timeout=15, flexible=False):
        """Return the element that contains the list items for a Kendo DropDownList/MultiSelect."""
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)

        # ensure it's open (MultiSelects may not toggle aria-expanded)
        if not flexible:
            wait.until(lambda d: (root.get_attribute("aria-expanded") or "").lower() == "true")

        list_id = (root.get_attribute("aria-controls") or root.get_attribute("aria-owns") or "").strip()

        # 1) JS-based fast path: exact element by id (anywhere), then descend if needed
        if list_id:
            node = self.driver.execute_script("""
                const id = arguments[0];
                const el = document.getElementById(id);
                if (!el) return null;

                // If this is not the actual list, descend to a likely list container
                const isList = (el.getAttribute('role') === 'listbox') ||
                               el.classList.contains('k-list') ||
                               el.classList.contains('k-popup-content');
                if (isList) return el;

                return el.querySelector('[role="listbox"], .k-list, .k-popup-content') || el;
            """, list_id
                                              )
            if node:
                return node  # Selenium wraps DOM node as WebElement

        # 2) Visible list under any visible animation container
        xp_vis_popup = (
            "//div[contains(@class,'k-animation-container') "
            "and not(contains(translate(@style,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'display: none'))]"
            "//*[(@role='listbox') or contains(@class,'k-list') or contains(@class,'k-popup-content')]"
        )
        try:
            return wait.until(
                lambda d: next((e for e in d.find_elements(By.XPATH, xp_vis_popup) if e.is_displayed()), False)
                )
        except TimeoutException:
            # 3) last resort: any visible role=listbox anywhere
            return wait.until(
                lambda d: next((e for e in d.find_elements(By.XPATH, '//*[@role=\"listbox\"]') if e.is_displayed()),
                               False
                               )
                )

    def _listbox_scroll_one_page(self, listbox):
        """Scroll one viewport in the popup (keyboard first, JS fallback)."""
        with contextlib.suppress(Exception):
            listbox.send_keys(Keys.PAGE_DOWN)
            return True
        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollTop += arguments[0].clientHeight;", listbox)
            return True
        return False

    def _dd_items_rel_xpath(self) -> str:
        return ".//*[(self::li) or (@role='option') or contains(@class,'k-list-item') or contains(@class,'k-item')]"

    def _dd_option_rel_for_text(self, text: str, match: str = "exact") -> str:
        def ci(expr: str) -> str:
            return f"translate({expr}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"

        lit = self._xp_lit(text.lower())
        ctxs = [
            "normalize-space(.)",  # text on LI
            "normalize-space(.//span[contains(@class,'k-list-item-text')])",  # common span
            "normalize-space(.//span)"  # any span
            ]
        if match == "startswith":
            tp = " or ".join([f"starts-with({ci(c)}, {lit})" for c in ctxs])
        elif match == "contains":
            tp = " or ".join([f"contains({ci(c)}, {lit})" for c in ctxs])
        else:  # exact
            tp = " or ".join([f"{ci(c)}={lit}" for c in ctxs])

        # items cover: <li>, role='option', and kendo item classes
        return (
            ".//*[(self::li) or (@role='option') or contains(@class,'k-list-item') or contains(@class,'k-item')]"
            f"[({tp})]"
        )

    def _dd_page_until(self, listbox, opt_rel_xpath: str, timeout: int) -> bool:

        end = time.monotonic() + timeout
        last_sig = None

        # focus so PAGE_DOWN goes to the listbox
        try:
            self.driver.execute_script("arguments[0].focus();", listbox)
        except Exception:
            pass

        def items():
            xp_items = ".//*[(self::li) or (@role='option') or contains(@class,'k-list-item') or contains(@class,'k-item')]"
            return [e for e in listbox.find_elements(By.XPATH, xp_items) if e.is_displayed()]

        while time.monotonic() < end:
            # found?
            if listbox.find_elements(By.XPATH, opt_rel_xpath):
                return True

            vis = items()
            if not vis:
                time.sleep(0.12)
                continue

            tail = vis[-1]
            sig = (tail.get_attribute("data-offset-index") or "", (tail.text or "").strip())

            # move viewport down
            try:
                listbox.send_keys(Keys.PAGE_DOWN)
            except Exception:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'end'});", tail)
            time.sleep(0.15)

            # no progress? jump a full viewport on the nearest scrollable ancestor
            if sig == last_sig:
                try:
                    self.driver.execute_script("""
                        const n = arguments[0];
                        let s = n;
                        while (s && !(s.scrollHeight > s.clientHeight)) { s = s.parentElement; }
                        if (s) s.scrollTop = s.scrollTop + s.clientHeight;
                    """, listbox
                                               )
                except Exception:
                    pass
                time.sleep(0.15)

            last_sig = sig

        return bool(listbox.find_elements(By.XPATH, opt_rel_xpath))

    def kendo_dd_select_text_old(self, logical_name: str, text: str, *, match: str = "exact", timeout: int = 30) -> bool:

        sel = self.resolve(logical_name)
        el = self._get_webelement(sel, timeout=timeout)
        root = self._dd_root(el)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)

        before = self._dd_get_display_text(root)
        if match == "exact" and before == text:
            return True

        self._dd_open(root, timeout)
        listbox = self._open_kendo_and_get_listbox(root, None, timeout=timeout)

        opt_rel = self._dd_option_rel_for_text(text, match)

        # Fast path: try a filter box if present
        used_filter = False
        for css in ("input.k-input-inner", "input.k-textbox", "input[role='textbox']", ".k-filter input",
                    ".k-searchbar input"):
            boxes = listbox.find_elements(By.CSS_SELECTOR, css)
            if boxes:
                boxes[0].clear();
                boxes[0].send_keys(text);
                used_filter = True;
                time.sleep(0.25);
                break

        # If not found yet, try built-in type-to-search on the control input
        if not listbox.find_elements(By.XPATH, opt_rel):
            try:
                el.click();
                el.clear();
                el.send_keys(text);
                time.sleep(0.25)
            except Exception:
                pass

        # Still not in DOM? page/scroll until it appears
        if not listbox.find_elements(By.XPATH, opt_rel):
            self._dd_page_until(listbox, opt_rel, timeout=timeout)

        # Click the now-present option (JS fallback avoids animation issues)
        option = WebDriverWait(listbox, timeout).until(EC.presence_of_element_located((By.XPATH, opt_rel)))
        try:
            WebDriverWait(listbox, timeout).until(EC.element_to_be_clickable((By.XPATH, opt_rel)))
            self.sb.highlight(option)
            option.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", option)

        self._dd_close(root, timeout)
        WebDriverWait(self.driver, timeout).until(lambda d: self._dd_get_display_text(root) != before)
        if match == "exact":
            WebDriverWait(self.driver, timeout).until(lambda d: self._dd_get_display_text(root) == text)
        return True

    def wait_for_overlays_to_clear(self, timeout: int = 4) -> bool:
        """Wait until common Kendo/Angular/Bootstrap overlays are gone."""
        import time
        from selenium.webdriver.common.by import By

        css_list = [
            ".k-overlay",  # Kendo overlay
            ".k-dialog-wrapper + .k-overlay",  # variant
            ".cdk-overlay-backdrop",  # Angular CDK
            ".modal-backdrop.show",  # Bootstrap
            ".k-animation-container[style*='display: block'] .k-dialog",  # visible dialogs
            ]
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            any_visible = False
            for css in css_list:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, css)
                    if any(e.is_displayed() for e in els):
                        any_visible = True
                        break
                except Exception:
                    pass
            if not any_visible:
                return True
            time.sleep(0.12)
        return False


    def click_robust(self, selector_or_logical, *, by: str | None = None, timeout: int = 12):
        """Reliable click: scroll → normal click → (if intercepted) wait overlays → JS click."""
        # resolve your logical names or accept raw xpath/css
        if by is None:
            sel = self.resolve(selector_or_logical) if selector_or_logical in self.locators else selector_or_logical
            by_tuple = self._by_tuple(sel)
        else:
            sel = selector_or_logical
            by_tuple = (By.XPATH, sel) if by.lower() in ("xpath", "x") else (By.CSS_SELECTOR, sel)

        el = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(by_tuple))
        # center it
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(by_tuple))
            el.click()
            return
        except ElementClickInterceptedException:
            # something is on top; give it a moment to vanish
            self.wait_for_overlays_to_clear(3)
            try:
                WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable(by_tuple))
                el = self.driver.find_element(*by_tuple)
                el.click()
                return
            except Exception:
                pass
        except Exception:
            # fall through to JS click
            pass

        # Last resort: JS click the element itself (no CSS conversion needed)
        try:
            self.driver.execute_script("arguments[0].click();", el)
        except Exception:
            # re-find and try again once
            el = self.driver.find_element(*by_tuple)
            self.driver.execute_script("arguments[0].click();", el)

    # ------- Date helpers --------------------------------------------------------

    def _coerce_date(self, value, fmt: str | None = None) -> date:
        """Parse many date inputs into a datetime.date."""
        if isinstance(value, date):
            return value
        s = str(value).strip()
        if fmt:
            return datetime.strptime(s, fmt).date()
        for f in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%b-%Y", "%b %d, %Y"):
            try:
                return datetime.strptime(s, f).date()
            except Exception:
                pass
        raise ValueError(f"Unrecognized date: {value!r}")

    def calendar_expected_dates(self, start, *, weeks: int = 1, mode: str = "daily") -> List[date]:
        """
        Compute the list of dates to expect dots for.
        mode: 'daily' -> every day; 'weekdays' -> Mon..Fri only
        """
        start_d = self._coerce_date(start)
        last = start_d + timedelta(weeks=weeks)  # exclusive end
        out: List[date] = []
        d = start_d
        while d < last:
            if mode.lower() == "weekdays":
                if d.weekday() < 5:  # 0=Mon .. 4=Fri
                    out.append(d)
            else:
                out.append(d)
            d += timedelta(days=1)
        return out

    # ------- DOM helpers for the month view -------------------------------------
    def _month_cell_for_day(self, day: int, timeout: int = 6):
        """
        Return the <mwl-calendar-month-cell> for the DAY NUMBER that is
        'in-month' (not the out-of-month overflow cells).
        """
        xp = ("//mwl-calendar-month-cell"
              "[contains(@class,'cal-in-month')]"
              f"[.//span[contains(@class,'cal-day-number') and normalize-space()='{day}']]")
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xp))
            )

    def _dot_styles_in_cell(self, cell) -> List[str]:
        """
        Return all style strings for 'drug-dot' elements inside a calendar cell.
        Multiple dots are supported.
        """
        dots = cell.find_elements(By.CSS_SELECTOR, ".drug-dots-preview .drug-dot, .drug-dot")
        return [(d.get_attribute("style") or "").strip() for d in dots]

    # ------- Public API ----------------------------------------------------------
    def calendar_collect_dot_styles(
            self,
            start,
            *,
            weeks: int = 1,
            mode: str = "daily",
            timeout_per_cell: int = 6,
            ) -> Dict[date, List[str]]:
        """
        For all expected dates (based on start/weeks/mode), collect the 'style'
        attributes from '.drug-dot' inside each visible month cell.
        Returns { date: [style, ...], ... }  (empty list if no dots found).
        """
        result: Dict[date, List[str]] = {}
        for d in self.calendar_expected_dates(start, weeks=weeks, mode=mode):
            try:
                cell = self._month_cell_for_day(d.day, timeout=timeout_per_cell)
                styles = self._dot_styles_in_cell(cell)
            except Exception:
                styles = []  # cell not visible or structure changed
            result[d] = styles
        return result

    def calendar_verify_dots(
            self,
            start,
            *,
            weeks: int = 1,
            mode: str = "daily",
            expect_color_substring: str | None = None,  # e.g. "rgb(195, 34, 150)"
            timeout_per_cell: int = 6,
            ) -> Tuple[List[date], Dict[date, List[str]]]:
        """
        Assert that all expected dates have at least one dot.
        Optionally also require that each dot's style contains a specific color substring.
        Returns (missing_dates, styles_map) without raising if you want to assert yourself.
        """
        styles_map = self.calendar_collect_dot_styles(
            start, weeks=weeks, mode=mode, timeout_per_cell=timeout_per_cell
            )
        missing: List[date] = []
        for d, styles in styles_map.items():
            if not styles:
                missing.append(d)
                continue
            if expect_color_substring:
                if not any(expect_color_substring in s for s in styles):
                    missing.append(d)
        return missing, styles_map



    # --- Parse "August 2025" from the calendar header ----------------------------
    def calendar_visible_year_month(self, header_logical: str, *, timeout: int = 6) -> tuple[int, int]:
        hdr = self._get_webelement(self.resolve(header_logical), timeout=timeout)
        text = (hdr.text or "").strip()
        # expect "August 2025" or similar
        parts = text.split()
        if len(parts) < 2:
            raise RuntimeError(f"Cannot parse month+year from header: {text!r}")
        month_name, year_s = parts[0], parts[-1]
        months = {m: i for i, m in enumerate(calendar.month_name) if m}  # {"January":1,...}
        return int(year_s), months[month_name]

    from selenium.webdriver.support.ui import WebDriverWait

    def calendar_goto_year_month(
            self,
            header_logical: str,
            next_btn_logical: str,
            prev_btn_logical: str,
            target_year: int,
            target_month: int,
            *,
            timeout: int = 10,
            ) -> None:
        """Click prev/next until header shows (target_year, target_month).
        Debounces every click by waiting for the header text to change first.
        """
        for _ in range(30):  # safety bound (~2.5 years of moves)
            # current y,m + current header text (used for debounce)
            y, m = self.calendar_visible_year_month(header_logical, timeout=timeout)
            if (y, m) == (target_year, target_month):
                return

            header_sel = self.resolve(header_logical)
            hdr = self._get_webelement(header_sel, timeout=timeout)
            before = (hdr.text or "").strip()

            # choose direction and click ONCE
            if (y, m) < (target_year, target_month):
                self.click_robust(next_btn_logical)  # logical name
            else:
                self.click_robust(prev_btn_logical)

            # wait for header to actually change (prevents double-stepping)
            WebDriverWait(self.driver, timeout).until(
                lambda d: (self._get_webelement(header_sel, timeout=timeout).text or "").strip() != before
                )
            # optional: give Angular/Kendo a beat to settle
            self.wait_for_overlays_to_clear(2)

        raise RuntimeError(f"Could not reach {target_year}-{target_month:02d} using calendar navigation")

    # --- Find a cell for a day number within the visible month -------------------
    def _month_cell_for_day(self, day: int, *, timeout: int = 6, in_month_only: bool = True):
        pred_month = " and contains(@class,'cal-in-month')" if in_month_only else ""
        xp = ("//mwl-calendar-month-cell"
              f"[contains(@class,'cal-day-cell'){pred_month}]"
              f"[.//span[contains(@class,'cal-day-number') and normalize-space()='{day}']]")
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xp))
            )

    def _dot_styles_in_cell(self, cell) -> list[str]:
        dots = cell.find_elements(By.CSS_SELECTOR, ".drug-dots-preview .drug-dot, .drug-dot")
        return [(d.get_attribute("style") or "").strip() for d in dots]

    # --- Multi-month collector ----------------------------------------------------
    def calendar_collect_dot_styles_multi_month(
            self,
            start, *,
            weeks: int,
            mode: str,  # "daily" or "weekdays"
            header_logical: str,
            next_btn_logical: str,
            prev_btn_logical: str,
            timeout_per_cell: int = 6,
            ) -> dict[date, list[str]]:
        """Navigate across months and collect styles for all expected dates."""
        expected = self.calendar_expected_dates(start, weeks=weeks, mode=mode)
        groups = defaultdict(list)
        for d in expected:
            groups[(d.year, d.month)].append(d)

        styles_map: dict[date, list[str]] = {}
        for (yy, mm), dates in sorted(groups.items()):
            self.calendar_goto_year_month(header_logical, next_btn_logical, prev_btn_logical, yy, mm)
            for d in dates:
                try:
                    cell = self._month_cell_for_day(d.day, timeout=timeout_per_cell, in_month_only=True)
                    styles_map[d] = self._dot_styles_in_cell(cell)
                except Exception:
                    styles_map[d] = []
        return styles_map

    def calendar_verify_dots_multi_month(
            self,
            start,
            *,
            weeks: int = 1,
            mode: str = "daily",  # "daily" | "weekdays"
            header_logical: str,  # eg "calendar-header"
            next_btn_logical: str,  # eg "cal_next_btn"
            prev_btn_logical: str,  # eg "cal_prev_btn"
            expect_color_substring: str | None = None,  # eg "rgb(195, 34, 150)"
            timeout_per_cell: int = 6,
            ):
        """Verify dot styles across month boundaries by grouping expected dates
        per (year, month), navigating once per group, then checking those days.
        Returns (missing_dates, styles_map).
        """
        # 1) build expected dates
        exp = self.calendar_expected_dates(start, weeks=weeks, mode=mode)

        # 2) group by (year, month)
        groups = {}
        for d in exp:
            groups.setdefault((d.year, d.month), []).append(d)

        styles_map = {}
        missing = []

        # 3) visit each month once, verify days in that month
        for (y, m) in sorted(groups.keys()):
            self.calendar_goto_year_month(
                header_logical, next_btn_logical, prev_btn_logical, y, m, timeout=8
                )

            for d in groups[(y, m)]:
                try:
                    cell = self._month_cell_for_day(d.day, timeout=timeout_per_cell)
                    styles = self._dot_styles_in_cell(cell)
                except Exception:
                    styles = []

                styles_map[d] = styles
                if not styles:
                    missing.append(d)
                elif expect_color_substring and not any(expect_color_substring in s for s in styles):
                    missing.append(d)

        return missing, styles_map

    def clear_heal_cache(self, logical_name: str | None = None):
        # Adjust to your framework’s actual cache fields
        for attr in ("_heal_cache", "_selector_cache", "_resolve_cache"):
            cache = getattr(self, attr, None)
            if isinstance(cache, dict):
                if logical_name:
                    cache.pop(logical_name, None)
                else:
                    cache.clear()

    def format_mdY(self, dt):
        try:
            return dt.strftime("%b %-d, %Y")  # Unix
        except ValueError:
            return dt.strftime("%b %#d, %Y")

    def format_full_mdY(self, dt):
        try:
            return dt.strftime("%B %-d, %Y")  # Unix
        except ValueError:
            return dt.strftime("%B %#d, %Y")


#================================
    # ===== Kendo popup & listbox helpers (shared) =====


    # --- roots / popup finders ---
    def _dd_root(self, el):
        return self.driver.execute_script(
            "return arguments[0].closest("
            "'kendo-dropdownlist,.k-dropdownlist,[role=\"combobox\"],"
            ".k-picker,.k-multiselect'"
            ") || arguments[0];", el
            )

    def _kendo_wrapped_bits(self, root):
        """Return (wrapper, input, list_id) for a Kendo Angular dropdown-like control."""
        wrapper = root
        try:
            # Prefer the element that actually carries combobox ARIA
            w = root.find_element(By.CSS_SELECTOR, "[role='combobox']")
            wrapper = w or wrapper
        except Exception:
            # Try common Kendo Angular wrappers
            for css in (".k-input", ".k-picker", ".k-dropdownlist", ".k-picker-wrap", ".k-picker-solid",
                        ".k-picker-md"):
                try:
                    wrapper = root.find_element(By.CSS_SELECTOR, css)
                    break
                except Exception:
                    pass

        # Find a focusable/text input if one exists
        inp = None
        for css in ("input[role='combobox']",
                    "input.k-input-inner",
                    ".k-input-inner input",
                    "input.k-input",
                    "input[role='textbox']"):
            try:
                inp = wrapper.find_element(By.CSS_SELECTOR, css)
                break
            except Exception:
                pass

        # Popup id may live on wrapper (preferred) or root
        list_id = (wrapper.get_attribute("aria-controls") or
                   wrapper.get_attribute("aria-owns") or
                   root.get_attribute("aria-controls") or
                   root.get_attribute("aria-owns") or
                   "").strip() or None
        return wrapper, inp, list_id


    # --- option matching & utilities ---
    def _kendo_is_disabled_item(self, item) -> bool:
        try:
            cls = item.get_attribute("class") or ""
            aria = (item.get_attribute("aria-disabled") or "").lower() == "true"
            return ("k-disabled" in cls) or aria
        except Exception:
            return False

    def _kendo_list_label(self, item) -> str:
        for xp in [
            ".//span[contains(@class,'k-list-item-text')]",
            ".//span",
            ".",
            ]:
            with contextlib.suppress(Exception):
                t = item.find_element(By.XPATH, xp).text or ""
                t = re.sub(r"\s+", " ", t).strip()
                if t:
                    return t
        return ""

    def _xp_lit(self, s: str) -> str:
        # safe XPath literal
        if "'" not in s:
            return f"'{s}'"
        if '"' not in s:
            return f'"{s}"'
        parts = s.split("'")
        return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

    def _option_rel_for_text(self, text: str, match: str = "exact") -> str:
        def ci(expr):  # case-insensitive
            return f"translate({expr}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"

        lit = self._xp_lit(text.lower())
        ctxs = [
            "normalize-space(.)",
            "normalize-space(.//span[contains(@class,'k-list-item-text')])",
            "normalize-space(.//span)"
            ]
        if match == "startswith":
            pred = " or ".join([f"starts-with({ci(c)}, {lit})" for c in ctxs])
        elif match == "contains":
            pred = " or ".join([f"contains({ci(c)}, {lit})" for c in ctxs])
        else:
            pred = " or ".join([f"{ci(c)}={lit}" for c in ctxs])
        return (
            ".//*[(self::li) or (@role='option') or contains(@class,'k-list-item') or contains(@class,'k-item')]"
            f"[({pred}) and not(contains(@class,'k-disabled'))]"
        )

    def _page_down_list(self, listbox):
        with contextlib.suppress(Exception):
            listbox.send_keys(Keys.PAGE_DOWN)
        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollTop += arguments[0].clientHeight;", listbox)
        time.sleep(0.12)

    def _dd_try_filter(self, listbox, text) -> bool:
        inp = None
        for css in ("input.k-input-inner", ".k-searchbar input", "input[role='textbox']"):
            els = listbox.find_elements(By.CSS_SELECTOR, css)
            if els:
                inp = els[0];
                break
            with contextlib.suppress(Exception):
                cont = listbox.find_element(By.XPATH, "./ancestor::div[contains(@class,'k-animation-container')]")
                tmp = cont.find_elements(By.CSS_SELECTOR, css)
                if tmp: inp = tmp[0]; break
        if not inp:
            return False
        inp.click()
        inp.send_keys(Keys.CONTROL, "a");
        inp.send_keys(Keys.BACKSPACE)
        inp.send_keys(text)
        time.sleep(0.25)
        return True

    # def _dd_close(self, root):
    #     with contextlib.suppress(Exception):
    #         root.send_keys(Keys.ESCAPE)

    # ===== DropDownList =====
    # --- Kendo DropDownList: get ALL option labels ---
    def kendo_dd_get_all_texts(self, logical_name: str, *, timeout: int = 20) -> list[str]:
        """
        Return ALL option texts from a Kendo DropDownList.
        Uses the same reliable pattern as kendo_ms_get_all_texts().
        Works for short lists and virtualized long lists.
        """
        sel = self.resolve(logical_name)
        el = self._get_webelement(sel, timeout=timeout)
        root = self._dd_root(el)

        # Ensure popup is open
        self._dd_open(root, timeout)
        listbox = self._dd_listbox(root, timeout=timeout, flexible=True)

        seen = set()
        texts = []
        end = time.monotonic() + timeout
        last_count = -1

        while time.monotonic() < end:
            # fetch all visible items
            items = listbox.find_elements(By.XPATH, self._dd_items_rel_xpath())
            fresh = []
            for i in items:
                if not i.is_displayed():
                    continue
                t = (i.text or "").strip()
                if t and t not in seen:
                    seen.add(t)
                    texts.append(t)
                    fresh.append(t)

            # break if no new items after scrolling
            if len(seen) == last_count:
                break
            last_count = len(seen)

            # scroll one viewport down
            if not self._listbox_scroll_one_page(listbox):
                break
            time.sleep(0.15)

        # close the popup for cleanliness
        try:
            self._dd_close(root, 3)
        except Exception:
            pass

        return texts

    def kendo_dd_select_text(self, logical_name: str, text: str, *, match: str = "exact", timeout: int = 25) -> bool:
        sel = self.resolve(logical_name)
        host = self._get_webelement(sel, timeout=timeout)
        root = self._dd_root(host)
        inp = self._dd_combobox_input(root)
        listbox = self._open_kendo_and_get_listbox(root, inp, timeout=timeout)
        opt_rel = self._option_rel_for_text(text, match)

        # If virtualized, page until found (with reopen if popup closes)
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                opts = listbox.find_elements(By.XPATH, opt_rel)
            except StaleElementReferenceException:
                with contextlib.suppress(Exception):
                    listbox = self._kendo_listbox_for(root, None, timeout=2)
                if not listbox or not listbox.is_displayed():
                    listbox = self._open_kendo_and_get_listbox(root, None, timeout=3)
                continue

            if opts:
                target = opts[0]
                try:
                    WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, opt_rel)))
                    target.click()
                except Exception:
                    with contextlib.suppress(Exception):
                        self.driver.execute_script("arguments[0].click();", target)
                return True

            self._page_down_list( listbox)

        raise TimeoutException(f"Option not found: {text!r} (match={match})")

    # ===== MultiSelect =====
    def _ms_root(self, el):
        return self.driver.execute_script(
            "return arguments[0].closest('kendo-multiselect,k-multiselect') || arguments[0];", el
            )

    def _ms_input(self, root):
        for css in ("input.k-input-inner", "input.k-input", "input[role='textbox']", ".k-searchbar input"):
            els = root.find_elements(By.CSS_SELECTOR, css)
            if els:
                return els[0]
        raise RuntimeError("Kendo MultiSelect input not found")


    def _kendo_items_rel(self) -> str:
        # All the ways Kendo renders options across skins
        return (".//*[(self::li) or (@role='option') "
                "or contains(@class,'k-list-item') or contains(@class,'k-item')]")

    def _kendo_item_text(self, li) -> str:
        txt = (li.text or "").strip()
        if not txt:
            with contextlib.suppress(Exception):
                txt = (li.find_element(By.CSS_SELECTOR,
                                       ".k-list-item-text, span"
                                       ).text or "").strip()
        return re.sub(r"\s+", " ", txt)

    def _kendo_scroll_container(self, listbox):
        # Find the element that actually scrolls (varies by theme/version)
        for css in (".k-virtual-scrollable-wrap", ".k-virtual-content",
                    ".k-list-scroller", ".k-list-content", ".k-popup-content", ".k-list"):
            els = listbox.find_elements(By.CSS_SELECTOR, css)
            if els:
                return els[0]
        return listbox  # fallback

    def _kendo_scroll_step(self, scroller):
        # Try keyboard paging first so Kendo loads more rows
        with contextlib.suppress(Exception):
            scroller.send_keys(Keys.PAGE_DOWN)
            return
        # JS fallback if keyboard didn’t work
        self.driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;",
            scroller
            )

    def kendo_ms_select_text(self, logical_name: str, text: str, *, match: str = "exact", timeout: int = 25) -> bool:
        sel = self.resolve(logical_name)
        host = self._get_webelement(sel, timeout=timeout)
        root = self._ms_root(host)
        inp = self._ms_input(root)

        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)
        with contextlib.suppress(Exception):
            root.click()
        with contextlib.suppress(Exception):
            inp.click()

        # pre-filter by typing to help virtualization
        with contextlib.suppress(Exception):
            inp.send_keys(Keys.CONTROL, "a")
            inp.send_keys(Keys.BACKSPACE)
        inp.send_keys(text)
        time.sleep(0.2)

        listbox = self._open_kendo_and_get_listbox( root, inp, timeout=timeout)
        opt_rel = self._option_rel_for_text( text, match)

        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                opts = listbox.find_elements(By.XPATH, opt_rel)
            except StaleElementReferenceException:
                with contextlib.suppress(Exception):
                    listbox = self._kendo_listbox_for(root, inp, timeout=2)
                if not listbox or not listbox.is_displayed():
                    listbox = self._open_kendo_and_get_listbox( root, inp, timeout=3)
                continue

            if opts:
                target = opts[0]
                try:
                    WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, opt_rel)))
                    target.click()
                except Exception:
                    with contextlib.suppress(Exception):
                        self.driver.execute_script("arguments[0].click();", target)
                # verify chip added
                WebDriverWait(self.driver, 5).until(
                    lambda d: any(
                        (text or "").lower() in (c.text or "").lower().strip()
                        for c in root.find_elements(By.CSS_SELECTOR, ".k-chip-list .k-chip .k-chip-content")
                        )
                    )
                return True

            self._page_down_list(listbox)

        raise TimeoutException(f"MultiSelect option not found: {text!r} (match={match})")

    # --- Popup discovery that tolerates quick open/close animations -------------
    # def _visible_kendo_listbox(self, timeout: int = 8):
    #     wait = WebDriverWait(self.driver, timeout, poll_frequency=0.15)
    #
    #     def find():
    #         # Prefer visible animation containers
    #         pops = self.driver.find_elements(By.CSS_SELECTOR, ".k-animation-container")
    #         vis_pops = []
    #         for p in pops:
    #             try:
    #                 st = (p.get_attribute("style") or "").lower()
    #                 if p.is_displayed() and "display: none" not in st:
    #                     vis_pops.append(p)
    #             except Exception:
    #                 pass
    #         # search common listbox containers inside
    #         for p in vis_pops:
    #             for css in ("[role='listbox']", ".k-list", ".k-list-ul", ".k-list-content", ".k-popup-content"):
    #                 els = [e for e in p.find_elements(By.CSS_SELECTOR, css) if e.is_displayed()]
    #                 if els:
    #                     return els[0]
    #
    #         # Fallback: any visible role=listbox anywhere
    #         any_vis = [e for e in self.driver.find_elements(By.CSS_SELECTOR, "[role='listbox']") if e.is_displayed()]
    #         return any_vis[0] if any_vis else False
    #
    #     return wait.until(lambda d: find())

    def _kendo_listbox_for(self, root_or_wrapper, inp=None, list_id=None, timeout=2):
        """Return the visible Kendo listbox for a given host/wrapper."""
        # Prefer a provided/derived id
        if not list_id:
            w, _, list_id = self._kendo_wrapped_bits(root_or_wrapper)

        lb = self._visible_kendo_listbox(list_id=list_id, timeout=timeout)
        if lb:
            return lb
        # Fallback: if the first attempt failed, try again once without list_id
        return self._visible_kendo_listbox(list_id=None, timeout=timeout)

    def _visible_kendo_listbox(self, list_id=None, timeout=2):
        """Find a visible Kendo popup list container."""
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)

        def by_id(id_):
            try:
                node = self.driver.execute_script("""
                    const id = arguments[0];
                    const el = document.getElementById(id);
                    if (!el) return null;

                    // If it's the list itself or a known popup container, return it
                    const isList = (el.getAttribute('role') === 'listbox') ||
                                   el.classList.contains('k-list') ||
                                   el.classList.contains('k-popup-content') ||
                                   el.classList.contains('k-virtual-content');
                    if (isList) return el;

                    // Otherwise descend to likely containers
                    return el.querySelector('[role="listbox"], .k-list, .k-popup-content, .k-virtual-content') || el;
                """, id_
                                                  )
                if node and node.is_displayed():
                    return node
            except Exception:
                return None
            return None

        if list_id:
            lb = wait.until(lambda d: by_id(list_id) or False)
            if lb:
                return lb

        # Visible popup anywhere (Kendo appends to body within an animation container)
        xp_vis = (
            "//div[contains(@class,'k-animation-container') "
            "and not(contains(translate(@style,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'display: none'))]"
            "//*[(@role='listbox') or contains(@class,'k-list') or contains(@class,'k-popup-content') or contains(@class,'k-virtual-content')]"
        )
        try:
            return wait.until(lambda d: next((e for e in d.find_elements(By.XPATH, xp_vis) if e.is_displayed()), False))
        except Exception:
            return None

    # def _open_kendo_and_get_listbox(self, root, inp=None, timeout: int = 8):
    #     """Open the popup and immediately resolve a *visible* listbox; keep focus inside to prevent auto-close."""
    #     end = time.monotonic() + timeout
    #     last_exc = None
    #     while time.monotonic() < end:
    #         with contextlib.suppress(Exception):
    #             self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)
    #             self.driver.execute_script("arguments[0].focus();", root)
    #
    #         # Try the standard toggle button first
    #         for css in ('button[aria-label*="open" i]', '.k-input-button', '.k-select', '.k-picker-wrap .k-select'):
    #             btns = root.find_elements(By.CSS_SELECTOR, css)
    #             if btns:
    #                 try:
    #                     btns[0].click()
    #                 except Exception as e:
    #                     last_exc = e
    #
    #         # Generic open gestures
    #         with contextlib.suppress(Exception):
    #             root.click()
    #         if inp:
    #             with contextlib.suppress(Exception): inp.click()
    #             with contextlib.suppress(Exception): inp.send_keys(Keys.ALT, Keys.ARROW_DOWN)
    #
    #         # If it opened, grab the visible listbox
    #         try:
    #             lb = self._kendo_listbox_for(root, inp, timeout=1)
    #             if lb and lb.is_displayed():
    #                 # Move mouse into popup to keep it “pinned” (avoids blur-closing)
    #                 try:
    #                     from selenium.webdriver import ActionChains
    #                     ActionChains(self.driver).move_to_element(lb).perform()
    #                 except Exception:
    #                     pass
    #                 # If there’s a filter box, click it to keep focus inside the popup
    #                 for css in ("input.k-input-inner", "input.k-textbox", "input[role='textbox']", ".k-filter input",
    #                             ".k-searchbar input"):
    #                     boxes = lb.find_elements(By.CSS_SELECTOR, css)
    #                     if boxes:
    #                         with contextlib.suppress(Exception):
    #                             boxes[0].click()
    #                         break
    #                 return lb
    #         except Exception as e:
    #             last_exc = e
    #
    #         time.sleep(0.15)
    #
    #     raise TimeoutException(f"Could not open Kendo popup (last error: {last_exc!r})")

    def _open_kendo_and_get_listbox(self, root, inp=None, timeout: int = 10):
        """Open the popup and immediately return a *visible* listbox element."""
        end = time.monotonic() + timeout
        last_exc = None

        wrapper, inp_auto, list_id = self._kendo_wrapped_bits(root)
        if inp is None:
            inp = inp_auto

        while time.monotonic() < end:
            # Bring into view & focus the correct wrapper
            with contextlib.suppress(Exception):
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", wrapper)
                self.driver.execute_script("arguments[0].focus();", wrapper)

            # If it's already open, try to grab the visible listbox right away
            try:
                if (wrapper.get_attribute("aria-expanded") or "").lower() == "true":
                    lb = self._kendo_listbox_for(wrapper, inp, list_id=list_id, timeout=1.5)
                    if lb and lb.is_displayed():
                        try:
                            from selenium.webdriver import ActionChains
                            ActionChains(self.driver).move_to_element(lb).perform()
                        except Exception:
                            pass
                        # Click filter/search box inside popup if present to keep focus inside
                        for css in ("input.k-input-inner", "input.k-textbox", "input[role='textbox']",
                                    ".k-filter input", ".k-searchbar input"):
                            boxes = lb.find_elements(By.CSS_SELECTOR, css)
                            if boxes:
                                with contextlib.suppress(Exception):
                                    boxes[0].click()
                                break
                        return lb
            except Exception:
                pass

            # 1) Try clicking the dropdown arrow / input button
            for css in ('button[aria-label*="open" i]',
                        '.k-input-button',
                        '.k-select',
                        '.k-picker-wrap .k-select',
                        '.k-button[aria-haspopup="listbox"]'):
                btns = wrapper.find_elements(By.CSS_SELECTOR, css)
                if btns:
                    try:
                        btns[0].click()
                        time.sleep(0.05)
                    except Exception as e:
                        last_exc = e

            # 2) Click wrapper & try key combos that open dropdowns
            with contextlib.suppress(Exception):
                wrapper.click()
            if inp:
                with contextlib.suppress(Exception):
                    inp.click()
                with contextlib.suppress(Exception):
                    inp.send_keys(Keys.ALT, Keys.ARROW_DOWN)
                with contextlib.suppress(Exception):
                    inp.send_keys(Keys.ENTER)
                with contextlib.suppress(Exception):
                    inp.send_keys(Keys.SPACE)
            else:
                # No input? Try keyboard on wrapper element.
                with contextlib.suppress(Exception):
                    wrapper.send_keys(Keys.ALT, Keys.ARROW_DOWN)
                with contextlib.suppress(Exception):
                    wrapper.send_keys(Keys.ENTER)

            # 3) If list_id is known, wait specifically for that popup to show up
            try:
                lb = self._kendo_listbox_for(wrapper, inp, list_id=list_id, timeout=1.2)
                if lb and lb.is_displayed():
                    try:
                        from selenium.webdriver import ActionChains
                        ActionChains(self.driver).move_to_element(lb).perform()
                    except Exception:
                        pass
                    for css in ("input.k-input-inner", "input.k-textbox", "input[role='textbox']", ".k-filter input",
                                ".k-searchbar input"):
                        boxes = lb.find_elements(By.CSS_SELECTOR, css)
                        if boxes:
                            with contextlib.suppress(Exception):
                                boxes[0].click()
                            break
                    return lb
            except Exception as e:
                last_exc = e

            time.sleep(0.15)

        raise TimeoutException(f"Could not open Kendo popup (last error: {last_exc!r})")

    def _ensure_open_listbox(self, root, inp, current, *, timeout: int = 2):
        """Return a fresh, visible listbox; re-open if stale/hidden/closed."""
        try:
            _ = current.tag_name  # poke for staleness
            if current.is_displayed():
                return current
        except Exception:
            pass
        try:
            lb = self._kendo_listbox_for(root, inp, timeout=timeout)
            if lb and lb.is_displayed():
                return lb
        except Exception:
            pass
        return self._open_kendo_and_get_listbox(root, inp, timeout=timeout + 2)

    def _fresh_listbox_and_scroller(self, root, inp, listbox, *, timeout: int = 2):
        """Re-acquire listbox & its scrollable viewport (handles virt lists)."""
        lb = self._ensure_open_listbox(root, inp, listbox, timeout=timeout)
        # find a scrollable element close to the list
        scroller = None
        for css in (".k-virtual-scrollable-wrap", ".k-virtual-content", ".k-list-scroller",
                    ".k-list-content", ".k-popup-content", ".k-list"):
            els = lb.find_elements(By.CSS_SELECTOR, css)
            if els:
                scroller = els[0];
                break
        if not scroller:
            scroller = lb
        return lb, scroller

    def _safe_scroll_once(self, root, inp, listbox, *, pause: float = 0.12):
        """Scroll the popup once, with stale protection & auto-reacquire."""
        listbox, scroller = self._fresh_listbox_and_scroller(root, inp, listbox, timeout=2)
        try:
            with contextlib.suppress(Exception):
                scroller.send_keys(Keys.PAGE_DOWN)
                time.sleep(pause)
                return listbox
            # JS fallback
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", scroller
                )
            time.sleep(pause)
            return listbox
        except StaleElementReferenceException:
            # re-open if it died mid-scroll
            return self._open_kendo_and_get_listbox(root, inp, timeout=3)

    # --- MultiSelect: get all option texts (handles virtualization) ---------------
    def kendo_ms_get_all_texts(
            self,
            logical_name: str,
            *,
            filter_text: str | None = None,
            include_disabled: bool = False,
            timeout: int = 24,
            scroll_pause: float = 0.12,
            ) -> list[str]:

        sel = self.resolve(logical_name)
        host = self._get_webelement(sel, timeout=timeout)
        # root & input
        try:
            root = self._dd_root(host)
        except Exception:
            root = host
        inp = None
        for css in ("input[role='combobox']", "input.k-input-inner", "input.k-input"):
            cand = root.find_elements(By.CSS_SELECTOR, css)
            if cand:
                inp = cand[0];
                break
        if inp is None:
            inp = root  # fallback

        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)
            self.driver.execute_script("arguments[0].focus();", root)
        with contextlib.suppress(Exception):
            root.click()
        with contextlib.suppress(Exception):
            inp.click()

        listbox = self._open_kendo_and_get_listbox(root, inp, timeout=max(6, timeout // 3))

        if filter_text:
            if not self._dd_try_filter(listbox, filter_text):
                with contextlib.suppress(Exception):
                    inp.clear();
                    inp.send_keys(filter_text)
            time.sleep(0.25)

        items_rel = self._dd_items_rel_xpath()
        seen, out = set(), []
        stable_cycles = 0
        end = time.monotonic() + timeout

        while time.monotonic() < end:
            # keep mouse inside so popup doesn’t auto-close
            try:
                from selenium.webdriver import ActionChains
                ActionChains(self.driver).move_to_element(listbox).perform()
            except Exception:
                pass

            # current visible batch
            try:
                items = [e for e in listbox.find_elements(By.XPATH, items_rel) if e.is_displayed()]
            except StaleElementReferenceException:
                listbox = self._ensure_open_listbox(root, inp, listbox, timeout=2)
                continue

            added_this_round = 0
            for it in items:
                try:
                    disabled = "k-disabled" in (it.get_attribute("class") or "")
                    if (not include_disabled) and disabled:
                        continue
                    txt = (it.text or "").strip()
                    if txt and txt not in seen:
                        seen.add(txt)
                        out.append(txt)
                        added_this_round += 1
                except StaleElementReferenceException:
                    continue

            if added_this_round == 0:
                stable_cycles += 1
            else:
                stable_cycles = 0

            if stable_cycles >= 2:
                break

            listbox = self._safe_scroll_once(root, inp, listbox, pause=scroll_pause)

        with contextlib.suppress(Exception):
            inp.send_keys(Keys.ESCAPE)
        return out

    # =========================
    # Kendo Switch helpers
    # =========================
    def _ks_root(self, host) -> "WebElement":
        """Resolve the element that is the actual Kendo switch root from the host."""
        from selenium.webdriver.common.by import By
        # If the host itself is the switch
        try:
            cls = (host.get_attribute("class") or "").lower()
            role = (host.get_attribute("role") or "").lower()
            tag = (host.tag_name or "").lower()
            if "k-switch" in cls or role == "switch" or (tag == "input" and host.get_attribute("type") == "checkbox"):
                return host
        except Exception:
            pass
        # Common containers/roots
        for sel in [
            ".k-switch",  # Kendo root
            "[role='switch']",  # ARIA role switch
            "input[type='checkbox'].k-checkbox, input[type='checkbox'][class*='k-'], input.k-switch-input",
            ".k-switch-container, .k-switch-wrapper",
            ]:
            try:
                el = host.find_element(By.CSS_SELECTOR, sel)
                return el
            except Exception:
                continue
        # Fallback: parent might be the root
        try:
            return host.find_element(By.XPATH,
                                     "./ancestor-or-self::*[contains(@class,'k-switch') or @role='switch'][1]"
                                     )
        except Exception:
            return host  # last resort

    def _ks_input(self, root) -> "WebElement|None":
        """Return the underlying input checkbox/role=switch if present."""
        from selenium.webdriver.common.by import By
        for sel in [
            "input.k-switch-input",
            "input[type='checkbox']",
            "[role='switch']",
            ]:
            try:
                return root.find_element(By.CSS_SELECTOR, sel)
            except Exception:
                continue
        # sometimes input is sibling (wraps inside label)
        try:
            return root.find_element(By.XPATH, ".//following::*[self::input[@type='checkbox'] or @role='switch'][1]")
        except Exception:
            return None

    def _ks_click_target(self, root) -> "WebElement":
        """Pick the safest clickable target (handle > track > root > label)."""
        from selenium.webdriver.common.by import By
        # Prefer the thumb/handle to avoid label overlays
        for sel in [
            ".k-switch-handle, .k-switch-thumb",
            ".k-switch-track",
            ".k-switch, [role='switch']",
            ]:
            try:
                return root.find_element(By.CSS_SELECTOR, sel)
            except Exception:
                continue
        # label[for] fallback if input has id
        inp = self._ks_input(root)
        if inp:
            try:
                inp_id = inp.get_attribute("id") or ""
                if inp_id:
                    return root.find_element(By.XPATH, f"//label[@for={self._xp_lit(inp_id)}]")
            except Exception:
                pass
        return root

    def _xp_lit(self, s: str) -> str:
        """Safe XPath literal (reuse across helpers)."""
        if "'" not in s:
            return f"'{s}'"
        parts = s.split("'")
        return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

    def kendo_switch_is_enabled(self, logical_name: str, *, timeout: int = 10) -> bool:
        """Return False if switch is disabled via class/aria/disabled."""
        from selenium.common.exceptions import StaleElementReferenceException
        sel = self.resolve(logical_name)
        for _ in range(3):
            try:
                host = self._get_webelement(sel, timeout=timeout)
                root = self._ks_root(host)
                cls = (root.get_attribute("class") or "").lower()
                aria = (root.get_attribute("aria-disabled") or "").lower()
                dis = (root.get_attribute("disabled") or "").lower()
                if "k-disabled" in cls or aria in ("true", "1") or dis in ("true", "disabled", "1"):
                    return False
                inp = self._ks_input(root)
                if inp and (inp.get_attribute("disabled") or "").lower() in ("true", "disabled", "1"):
                    return False
                return True
            except StaleElementReferenceException:
                continue
        return True  # if unsure, treat as enabled

    def kendo_switch_is_on(self, logical_name: str, *, timeout: int = 10, strict: bool = False) -> bool:
        """Read current ON/OFF state robustly."""
        from selenium.common.exceptions import StaleElementReferenceException
        sel = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)
        for _ in range(4):
            try:
                host = self._get_webelement(sel, timeout=timeout)
                root = self._ks_root(host)
                # 1) aria-checked (most reliable across variants)
                aria_checked = (root.get_attribute("aria-checked") or "").lower()
                if aria_checked in ("true", "false"):
                    return aria_checked == "true"
                # 2) input.checked
                inp = self._ks_input(root)
                if inp is not None:
                    # Use JS property for correctness
                    try:
                        return bool(self.driver.execute_script("return !!arguments[0].checked;", inp))
                    except Exception:
                        chk = (inp.get_attribute("checked") or "").lower()
                        if chk in ("true", "checked", "1"):
                            return True
                # 3) class markers
                cls = (root.get_attribute("class") or "").lower()
                if "k-switch-label-on" in cls or "k-checked" in cls or "k-switch-on" in cls:
                    return True
                if "k-switch-label-off" in cls or "k-switch-off" in cls:
                    return False
                # 4) final fallback: data-checked on input/root
                for el in filter(None, [inp, root]):
                    val = (el.get_attribute("data-checked") or "").lower()
                    if val in ("true", "false"):
                        return val == "true"
                # unknown → try re-read after a micro-sleep
            except StaleElementReferenceException:
                pass
            try:
                import time;
                time.sleep(0.05)
            except Exception:
                pass
        # default safe fallback
        return False

    def kendo_switch_toggle(self, logical_name: str, *, timeout: int = 10, strict: bool = False) -> None:
        """Toggle the switch once (JS click fallback if needed)."""
        import contextlib, time
        from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
        sel = self.resolve_strict(logical_name) if strict else self.resolve(logical_name)
        for _ in range(4):
            try:
                host = self._get_webelement(sel, timeout=timeout)
                root = self._ks_root(host)
                with contextlib.suppress(Exception):
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)
                target = self._ks_click_target(root)
                try:
                    target.click()
                except (ElementClickInterceptedException, Exception):
                    self.driver.execute_script("arguments[0].click();", target)
                time.sleep(0.05)
                return
            except StaleElementReferenceException:
                time.sleep(0.05)
                continue

    def kendo_switch_set(self, logical_name: str, on: bool, *, timeout: int = 10, strict: bool = False) -> None:
        """Idempotently set the switch to ON/OFF (retries & stale-safe)."""
        import time
        # quick disabled guard
        if not self.kendo_switch_is_enabled(logical_name, timeout=timeout):
            raise AssertionError(f"Kendo switch '{logical_name}' is disabled.")
        # fast path
        if self.kendo_switch_is_on(logical_name, timeout=timeout, strict=strict) == on:
            return
        # try up to 6 toggles (handles animations/re-renders)
        for _ in range(6):
            self.kendo_switch_toggle(logical_name, timeout=timeout, strict=strict)
            time.sleep(0.08)
            state = self.kendo_switch_is_on(logical_name, timeout=timeout, strict=strict)
            if state == on:
                return
        raise AssertionError(f"Failed to set Kendo switch '{logical_name}' to {on}")

    def kendo_switch_wait(self, logical_name: str, expected: bool, *, timeout: int = 8, poll: float = 0.1, strict: bool=False) -> None:
        """Wait until switch reaches expected state (True/False) or timeout."""
        import time
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self.kendo_switch_is_on(logical_name, timeout=max(1, int(poll * 10)), strict=strict) == expected:
                return
            time.sleep(poll)
        raise TimeoutError(f"Kendo switch '{logical_name}' did not reach state {expected} in {timeout}s")

    # =========================
    # Kendo Expander / ExpansionPanel helpers
    # =========================
    # ---------- small utilities ----------
    def _xp_lit(self, s: str) -> str:
        if "'" not in s: return f"'{s}'"
        parts = s.split("'")
        return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

    def _dom_ready(self, timeout=10):
        import time
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                if self.driver.execute_script("return document.readyState") == "complete":
                    return
            except Exception:
                pass
            time.sleep(0.05)

    # ---------- expander locators ----------
    def _kx_root(self, host):
        from selenium.webdriver.common.by import By
        try:
            cls = (host.get_attribute("class") or "").lower()
            if "k-expander" in cls or "k-expansionpanel" in cls:
                return host
        except Exception:
            pass
        try:
            return host.find_element(
                By.XPATH,
                "./ancestor-or-self::*[contains(@class,'k-expander') or contains(@class,'k-expansionpanel')][1]"
                )
        except Exception:
            return host

    def _kx_header(self, root):
        from selenium.webdriver.common.by import By
        for css in ("div.k-expander-header[role='button']", "div.k-expander-header", "[role='button']"):
            try:
                return root.find_element(By.CSS_SELECTOR, css)
            except Exception:
                pass
        try:
            return root.find_element(By.XPATH, ".//div[contains(@class,'k-expander-header') or @role='button'][1]")
        except Exception:
            return root

    def _kx_content(self, root):
        from selenium.webdriver.common.by import By
        try:
            hdr = self._kx_header(root)
            cid = (hdr.get_attribute("aria-controls") or "").strip()
            if cid:
                try:
                    return root.find_element(By.XPATH, f".//*[@id={self._xp_lit(cid)}]")
                except Exception:
                    return self.driver.find_element(By.XPATH, f"//*[@id={self._xp_lit(cid)}]")
        except Exception:
            pass
        for css in (".k-expander-content-wrapper", ".k-expander-content", ".k-expansionpanel-content"):
            try:
                return root.find_element(By.CSS_SELECTOR, css)
            except Exception:
                pass
        return None

    # ---------- robust presence (by locator OR by label text) ----------
    def _kx_label_from_logical(self, logical_name: str) -> str | None:
        # expects names like: kendo-expansionpanel_Diseases  or  kendo-expander_Diseases
        if "_" in logical_name:
            tail = logical_name.split("_", 1)[1].strip()
            return tail or None
        return None

    def _kx_find_by_label(self, label: str):
        from selenium.webdriver.common.by import By
        xp = (
            "//div[(contains(@class,'k-expander') or contains(@class,'k-expansionpanel'))"
            f" and .//span[normalize-space()={self._xp_lit(label)}]]"
        )
        els = self.driver.find_elements(By.XPATH, xp)
        return els[0] if els else None

    def kendo_expander_ensure_present(self, logical_name: str, *, timeout: int = 10):
        """Return (root, header); wait for DOM ready; resolve by locator or by label text."""
        import time, contextlib
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self._dom_ready(min(timeout, 5))

        sel = self.resolve(logical_name)
        root = None
        try:
            # try your mapped locator first
            host = self._get_webelement(sel, timeout=max(1, int(timeout * 0.6)))
            root = self._kx_root(host)
        except TimeoutException:
            # fallback: derive label from name and find by text
            label = self._kx_label_from_logical(logical_name)
            if label:
                end = time.monotonic() + timeout
                while time.monotonic() < end and root is None:
                    cand = self._kx_find_by_label(label)
                    if cand:
                        root = cand
                        break
                    time.sleep(0.15)

        if root is None:
            raise TimeoutException(f"Expander '{logical_name}' not present")

        hdr = self._kx_header(root)
        with contextlib.suppress(Exception):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", hdr)

        # ensure it's interactable (visible/clickable-ish)
        try:
            WebDriverWait(self.driver, max(1, int(timeout * 0.4))).until(EC.presence_of_element_located(sel))
        except Exception:
            pass  # if we found by label, 'sel' might not match; that's fine

        return root, hdr

    # ---------- state & actions (updated) ----------
    def kendo_expander_is_expanded(self, logical_name: str, *, timeout: int = 10) -> bool:
        from selenium.common.exceptions import StaleElementReferenceException
        for _ in range(4):
            try:
                root, hdr = self.kendo_expander_ensure_present(logical_name, timeout=timeout)
                aria = (hdr.get_attribute("aria-expanded") or "").lower()
                if aria in ("true", "false"):
                    return aria == "true"
                content = self._kx_content(root)
                if content is not None:
                    cls = (content.get_attribute("class") or "").lower()
                    if "k-hidden" in cls: return False
                    try:
                        visible = self.driver.execute_script(
                            "const e=arguments[0];const s=getComputedStyle(e);"
                            "return !(s.display==='none'||s.visibility==='hidden'||s.opacity==='0');", content
                            )
                        return bool(visible)
                    except Exception:
                        pass
                hcls = (hdr.get_attribute("class") or "").lower()
                return "k-expanded" in hcls
            except StaleElementReferenceException:
                continue
            except Exception:
                break
        return False

    def kendo_expander_toggle(self, logical_name: str, *, timeout: int = 10) -> None:
        import time, contextlib
        from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
        for _ in range(4):
            try:
                _, hdr = self.kendo_expander_ensure_present(logical_name, timeout=timeout)
                with contextlib.suppress(Exception):
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", hdr)
                try:
                    hdr.click()
                except (ElementClickInterceptedException, Exception):
                    self.driver.execute_script("arguments[0].click();", hdr)
                time.sleep(0.1)  # let animation run
                return
            except StaleElementReferenceException:
                time.sleep(0.05)
                continue

    def kendo_expander_set(self, logical_name: str, expanded: bool, *, timeout: int = 10) -> None:
        import time
        if self.kendo_expander_is_expanded(logical_name, timeout=timeout) == expanded:
            return
        for _ in range(6):
            self.kendo_expander_toggle(logical_name, timeout=timeout)
            time.sleep(0.12)
            if self.kendo_expander_is_expanded(logical_name, timeout=timeout) == expanded:
                return
        raise AssertionError(f"Failed to set expander '{logical_name}' to expanded={expanded}")

    def kendo_expander_wait(self, logical_name: str, expected: bool, *, timeout: int = 8, poll: float = 0.1) -> None:
        import time
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self.kendo_expander_is_expanded(logical_name, timeout=max(1, int(poll * 10))) == expected:
                return
            time.sleep(poll)
        raise TimeoutError(f"Expander '{logical_name}' did not reach state {expected} in {timeout}s")

    # --- Small utilities ---------------------------------------------------------

    def _bubble_text(self, bubble):
        """Return the text shown inside the bubble, without the username line."""
        try:
            # If there's a username line, drop it from the final text
            u = bubble.find_elements(By.CSS_SELECTOR, "p.username-display")
            uname = u[0].text.strip() if u else None
        except Exception:
            uname = None

        t = bubble.text.strip()
        if uname:
            # only strip the first occurrence at the start
            if t.startswith(uname):
                t = t[len(uname):].strip()
        return t

    def _wait_for_any_message(self, timeout=15):
        # Wait until at least one chat message exists
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "kendo-chat-message"))
            )

    # --- Public helpers ----------------------------------------------------------

    def get_last_received_message(self, timeout=15):
        """
        Last message that came from the other side (left bubble).
        Uses the absence of .k-alt on the nearest message-group.
        """
        self._wait_for_any_message(timeout)

        # last <kendo-chat-message> whose ancestor .k-message-group does NOT have .k-alt
        xp = ("(//kendo-chat-message[ancestor::div[contains(@class,'k-message-group') "
              "and not(contains(@class,'k-alt'))]])[last()]"
              "//div[contains(@class,'k-chat-bubble')]")
        bubbles = self.driver.find_elements(By.XPATH, xp)
        if not bubbles:
            return None
        return self._bubble_text(bubbles[-1])

    def get_last_sent_message(self, timeout=15):
        """
        Last message we sent (right bubble).
        Uses the presence of .k-alt on the nearest message-group.
        """
        self._wait_for_any_message(timeout)

        xp = ("(//kendo-chat-message[ancestor::div[contains(@class,'k-message-group') "
              "and contains(@class,'k-alt')]])[last()]"
              "//div[contains(@class,'k-chat-bubble')]")
        bubbles = self.driver.find_elements(By.XPATH, xp)
        if not bubbles:
            return None
        return self._bubble_text(bubbles[-1])

    # Optional: fetch both at once
    def get_last_messages(self, timeout=15):
        """Return (last_incoming, last_outgoing). Either may be None."""
        return (self.get_last_received_message(timeout),
                self.get_last_sent_message(timeout))

    # def kendo_autocomplete_select(self, input_locator: str, text: str, option_text: str = None):
    #     """Type into a Kendo autocomplete and select a dropdown option."""
    #
    #     # Resolve input field (JSON locator or raw XPath)
    #     sel = self.resolve_strict(input_locator) if input_locator in self.locators else input_locator
    #
    #     # Type into the input
    #     self.sb.type(sel, text)
    #
    #     # Wait until the Kendo listbox is visible
    #     listbox = "//ul[@role='listbox' and contains(@id, 'list')]"
    #     self.wait_for_element_visible(listbox, timeout=10)
    #
    #     # Select matching option or first option
    #     if option_text:
    #         option_sel = f"//ul[@role='listbox']//li[contains(normalize-space(.), '{option_text}')]"
    #     else:
    #         option_sel = "//ul[@role='listbox']//li[1]"
    #
    #     self.sb.wait_for_element_visible(option_sel, timeout=5)
    #     self.sb.click(option_sel)


    def kendo_autocomplete_select(self, input_locator: str, text: str, option_text: str | None = None,
                                  timeout: int = 12, click_plus: bool = True, select_first: bool = False) -> str:
        """Type into a Kendo autocomplete and select a dropdown option."""
        # Resolve the input element (logical name or raw selector/xpath)
        sel = self.resolve_strict(input_locator) if input_locator in getattr(self, "locators", {}) else input_locator
        self.sb.wait_for_element_visible(sel, timeout=timeout)
        inp = self._get_webelement(sel, timeout=timeout)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        inp.click()
        try:
            inp.clear()
        except Exception:
            pass
        inp.send_keys(text)
        time.sleep(0.15)

        # Find the visible Kendo popup listbox
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)

        def _visible_ul(driver):
            uls = driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'k-animation-container') and "
                "not(contains(translate(@style,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'display: none'))]"
                "//ul[@role='listbox']"
                )
            for ul in uls:
                if ul.is_displayed():
                    return ul
            return False

        ul = None
        try:
            ul = wait.until(_visible_ul)
        except Exception:
            pass

        chosen = option_text or text

        if ul:
            options = ul.find_elements(By.XPATH, ".//li[not(contains(@class,'k-disabled'))]")

            # 🔹 New section: Always click the first visible option if select_first=True
            if select_first and options:
                first = options[0]
                first.click()
                chosen = first.text.strip()
            else:
                # Original behavior
                clicked = False
                for li in options:
                    label = li.text.strip()
                    if chosen.lower() in label.lower():
                        li.click()
                        clicked = True
                        chosen = label
                        break
                if not clicked:
                    inp.send_keys(Keys.DOWN, Keys.ENTER)
        else:
            # popup didn’t render – use keyboard fallback
            inp.send_keys(Keys.DOWN, Keys.ENTER)

        # Optional: click the little "+" button next to the input (if your UI uses it)
        if click_plus:
            try:
                plus = inp.find_element(By.XPATH, "ancestor::*[contains(@class,'k-input')]"
                                                  "//*[self::button or self::span][contains(@class,'k-i-plus') or @aria-label='Add']"
                                        )
                if plus.is_displayed():
                    plus.click()
            except Exception:
                pass

        return chosen

    # --- internals ---------------------------------------------------------------

    def _visible_month_view(self, timeout=10):
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)
        # pick the visible month view
        views = wait.until(
            lambda d: [v for v in d.find_elements(By.CSS_SELECTOR, "mwl-calendar-month-view") if v.is_displayed()]
            )
        return views[0]

    def _today_cell(self, month_view, timeout=5):
        """Return the cell element for today's date (robust to class variations)."""
        # 1) Fast path: a cell explicitly marked as 'cal-today'
        cells = month_view.find_elements(By.CSS_SELECTOR, "mwl-calendar-month-cell.cal-day-cell.cal-today")
        for c in cells:
            if c.is_displayed():
                return c

        # 2) Fallback: find cell by day number within the current month
        day_str = str(date.today().day)
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)
        # in-month cells only
        in_month = month_view.find_elements(By.CSS_SELECTOR, "mwl-calendar-month-cell.cal-day-cell.cal-in-month")
        # prefer a cell whose visible number matches today
        for cell in in_month:
            try:
                num = cell.find_element(By.XPATH,
                                        ".//*[contains(@class,'cal-day-number') or contains(@class,'day-number') or self::span]"
                                        ).text.strip()
                if num == day_str and cell.is_displayed():
                    return cell
            except Exception:
                pass
        # last resort: wait for any selected cell
        return wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "mwl-calendar-month-cell.cal-day-cell.cal-in-month")
            )
            )

    # --- public API --------------------------------------------------------------

    def calendar_today_has_icons(self, *icon_classes: str, timeout: int = 10) -> dict:
        """
        Check that today's cell contains all given icon classes.
        Returns a dict: {"found": set, "missing": set}
        Example: calendar_today_has_icons("taken-dose-icon", "comments-icon", "video-icon")
        """
        mv = _visible_month_view(self, timeout=timeout)
        cell = _today_cell(self, mv, timeout=timeout)

        result_found, result_missing = set(), set()
        for cls in icon_classes:
            # accept either a full CSS or just a class name
            selector = cls if any(ch in cls for ch in " .#[]>:") else f".{cls}"
            els = cell.find_elements(By.CSS_SELECTOR, selector)
            if els and any(e.is_displayed() for e in els):
                result_found.add(cls)
            else:
                result_missing.add(cls)

        return {"found": result_found, "missing": result_missing}

    def assert_calendar_today_icons(self, *icon_classes: str, timeout: int = 10):
        """Assert variant that raises if any icon is missing."""
        res = self.calendar_today_has_icons(*icon_classes, timeout=timeout)
        if res["missing"]:
            raise AssertionError(
                f"Today's calendar cell is missing icons: {sorted(res['missing'])}. Found: {sorted(res['found'])}"
                )

    def is_text_in_tbody(self, tbody_locator: str, text: str) -> bool:
        # Resolve locator if it's in JSON
        sel = self.resolve_strict(tbody_locator) if tbody_locator in self.locators else tbody_locator

        # Get full text (not truncated) from DOM
        tbody_element = self.sb.find_element(sel)
        tbody_text = tbody_element.get_attribute("textContent")

        # Normalize text (remove newlines, trim spaces, case-insensitive)
        tbody_text = " ".join(tbody_text.split())
        return text.lower() in tbody_text.lower()

    # ---------- Frame helpers ----------
    def switch_to_frame(self, target, *, timeout: int = 15, strict: bool = False):
        """
        Switch into an <iframe>.
        target can be:
          - logical name from your locators JSON (preferred)
          - raw XPath/CSS string
          - frame id/name (string)
          - index (int)
          - WebElement (already located <iframe>)
        """
        drv = self.driver

        # Index
        if isinstance(target, int):
            drv.switch_to.frame(target)
            return

        # WebElement
        if hasattr(target, "tag_name"):
            WebDriverWait(drv, timeout).until(lambda d: target.is_displayed())
            drv.switch_to.frame(target)
            return

        # Resolve selector string
        sel = None
        if isinstance(target, str):
            if target in getattr(self, "locators", {}
                                 ) or ":" not in target and "@" not in target and "//" not in target:
                # Try logical name first (resolve/resolve_strict),
                # but also allow simple id/name via direct switch
                if target in getattr(self, "locators", {}):
                    sel = self.resolve_strict(target) if strict else self.resolve(target)
                else:
                    # Could be id or name
                    try:
                        drv.switch_to.frame(target)  # id or name
                        return
                    except NoSuchFrameException:
                        # fall through to treat as selector
                        sel = target
            else:
                sel = target

        if not sel:
            raise ValueError(f"Unsupported frame target: {target!r}")

        # Try waiting for the frame and switch (XPath vs CSS)
        sel_str = sel.strip()
        locator = (By.XPATH, sel_str) if sel_str.startswith("/") or sel_str.startswith("(") else (By.CSS_SELECTOR,
                                                                                                  sel_str)

        try:
            WebDriverWait(drv, timeout).until(EC.frame_to_be_available_and_switch_to_it(locator))
            return
        except Exception:
            # Fallback: locate the element, then switch
            frame_el = WebDriverWait(drv, timeout).until(
                EC.presence_of_element_located(locator)
                )
            drv.switch_to.frame(frame_el)

    def switch_to_parent_frame(self):
        """Go up one frame."""
        self.driver.switch_to.parent_frame()

    def switch_to_default_content(self):
        """Exit all frames back to the top document."""
        self.driver.switch_to.default_content()

    @contextlib.contextmanager
    def within_frame(self, target, *, timeout: int = 15, strict: bool = False):
        """
        Usage:
            with self.within_frame("iframe-chat"):
                self.click("send_button")
        Automatically returns to default content.
        """
        self.switch_to_frame(target, timeout=timeout, strict=strict)
        try:
            yield
        finally:
            self.switch_to_default_content()

    def parse_report_time(self, time_str: str) -> datetime:
        """Parse a report time that may be %H:%M or %H:%M:%S."""
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported time format: {time_str}")


