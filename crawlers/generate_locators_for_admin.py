import time


def build_resilient_xpath(el):
    tag = el.tag_name
    attrs = {
        "id": el.get_attribute("id"),
        "name": el.get_attribute("name"),
        "placeholder": el.get_attribute("placeholder"),
        "aria-label": el.get_attribute("aria-label"),
        "class": el.get_attribute("class"),
        "type": el.get_attribute("type"),
        "data-icon": el.get_attribute("data-icon"),
        }
    text = el.text.strip()

    if attrs["id"]:
        return f"//{tag}[@id='{attrs['id']}']"
    for attr in ["aria-label", "placeholder", "name"]:
        if attrs[attr]:
            return f"//{tag}[@{attr}='{attrs[attr]}']"
    if text:
        return f"//{tag}[contains(normalize-space(text()), '{text}')]"
    if attrs["class"] and attrs["type"]:
        return f"//{tag}[@class='{attrs['class']}' and @type='{attrs['type']}']"
    if attrs["class"]:
        return f"//{tag}[@class='{attrs['class']}']"
    return f"//{tag}"


import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common_utilities.load_settings import load_settings
from selenium.webdriver.remote.webelement import WebElement


def wait_for_page_to_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
        )


def clean_text_for_xpath(text):
    text = text.replace("\u00a0", " ").strip()
    text = " ".join(text.split())
    return text.replace("'", "")


def extract_locators(driver, page_name, out_dir):
    # Tags you want to skip entirely
    skip_tags = {
        "script", "noscript", "meta", "style", "link",
        "router-outlet", "head", "title", "base", "viewport"
    }

    elements = driver.find_elements(By.XPATH, "//*")
    locators = {}

    for i, el in enumerate(elements):
        try:
            tag = el.tag_name.lower()
            if tag in skip_tags:
                continue

            text = clean_text_for_xpath(el.text)
            attrs = {
                "id": el.get_attribute("id"),
                "name": el.get_attribute("name"),
                "placeholder": el.get_attribute("placeholder"),
                "aria-label": el.get_attribute("aria-label"),
                "class": el.get_attribute("class"),
                "type": el.get_attribute("type"),
                "data-icon": el.get_attribute("data-icon"),
            }

            key = attrs["id"] or attrs["name"] or f"{tag}_{text[:10]}_{i}"
            if not key or key in locators:
                continue

            locator_entry = {k: v for k, v in attrs.items() if v}
            locator_entry["tag"] = tag
            if text:
                locator_entry["text"] = text

            # Build resilient xpath
            locator_entry["xpath"] = build_resilient_xpath(el)

            locators[key] = locator_entry

        except Exception:
            continue

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_file = Path(out_dir) / f"{page_name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(locators, f, indent=2)
    print(f"✅ Scraped locator info saved to {out_file}")


def get_element_xpath(driver, element: WebElement) -> str:
    return driver.execute_script("""
        function absoluteXPath(element) {
            var comp, comps = [];
            var parent = null;
            var xpath = '';
            var getPos = function(element) {
                var position = 1, curNode;
                if (element.nodeType == Node.ATTRIBUTE_NODE) {
                    return null;
                }
                for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){
                    if (curNode.nodeName == element.nodeName)
                        ++position;
                }
                return position;
            }

            if (element instanceof Document)
                return '/';

            for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                comp = comps[comps.length] = {};
                switch (element.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + element.nodeName;
                        break;
                    case Node.PROCESSING_INSTRUCTION_NODE:
                        comp.name = 'processing-instruction()';
                        break;
                    case Node.COMMENT_NODE:
                        comp.name = 'comment()';
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = element.nodeName;
                        break;
                }
                comp.position = getPos(element);
            }

            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name.toLowerCase();
                if (comp.position !== null && comp.position > 1) {
                    xpath += '[' + comp.position + ']';
                }
            }

            return xpath;
        }
        return absoluteXPath(arguments[0]);
    """, element)


def login_to_app(driver, settings):
    driver.get(settings["url"])
    driver.maximize_window()
    wait = WebDriverWait(driver, 20)

    wait.until(EC.presence_of_element_located((By.ID, "email")))

    elements = driver.find_elements(By.XPATH, "//*")
    # login_json = "common_utilities/self_healing_locators/login.json"
    # scraped_data = {}

    # 👉 Add skip tags here
    # skip_tags = {
    #     "script", "noscript", "meta", "style", "link",
    #     "router-outlet", "head", "title", "base", "viewport", "html"
    # }
    #
    # for i, el in enumerate(elements):
    #     try:
    #         tag = el.tag_name.lower()
    #         if tag in skip_tags:
    #             continue  # ❌ Skip irrelevant tags
    #
    #         text = clean_text_for_xpath(el.text)
    #         attrs = {
    #             "id": el.get_attribute("id"),
    #             "name": el.get_attribute("name"),
    #             "placeholder": el.get_attribute("placeholder"),
    #             "aria-label": el.get_attribute("aria-label"),
    #             "class": el.get_attribute("class"),
    #             "type": el.get_attribute("type"),
    #             "data-icon": el.get_attribute("data-icon"),
    #         }
    #
    #         identifier = {k: v for k, v in attrs.items() if v}
    #         identifier["tag"] = tag
    #         if text:
    #             identifier["text"] = text
    #
    #         identifier["xpath"] = build_resilient_xpath(el)
    #         key = identifier.get("id") or identifier.get("name") or f"{tag}_{text[:10]}_{i}"
    #         if key not in scraped_data:
    #             scraped_data[key] = identifier
    #     except Exception:
    #         continue

    # with open(login_json, "w", encoding="utf-8") as f:
    #     json.dump(scraped_data, f, indent=2)
    #
    # print(f"✅ Scraped locator info saved to {login_json}")

    wait.until(EC.presence_of_element_located((By.ID, "password")))
    wait.until(EC.element_to_be_clickable((By.ID, "next")))
    driver.find_element(By.ID, "email").send_keys("demouser2@demo.sureadhere.com")
    driver.find_element(By.ID, "password").send_keys("heyHEYhey!")
    driver.find_element(By.ID, "next").click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//p[.='Dashboard']")))


def cancel_page(driver):
    wait = WebDriverWait(driver, 20)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button//span[.='Cancel']")))
    driver.find_element(By.XPATH, "//button//span[.='Cancel']").click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//p[.='Dashboard']")))


def add_user(driver):
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.XPATH, "//button//*[contains(@class,'user-plus')]")))
    driver.find_element(By.XPATH, "//button//*[contains(@class,'user-plus')]").click()


def crawl_pages(driver, pages_to_visit, out_dir):
    for name, path in pages_to_visit.items():
        try:
            if path.startswith("http"):
                driver.get(path)
            elif path == None:
                time.sleep(2)
            else:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, path))).click()
            wait_for_page_to_load(driver)
            time.sleep(15)

            extract_locators(driver, name, out_dir)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, path))).click()

        except Exception:
            print(f"❌ Couldn't open {name}")
            continue


def main():
    settings = load_settings()
    chrome_options = Options()
    input_dir = "../common_utilities/self_healing_locators"
    out_dir = "../common_utilities"
    if settings.get("CI", "false") == "true":
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        login_to_app(driver, settings)
        time.sleep(5)
        driver.find_element(By.XPATH, "//p[text()='Admin']").click()
        time.sleep(5)



        pages_to_visit = {
            # "admin_countries": "//div[@role='button'][contains(.,'Countries')]",
            # "admin_diseases": "//div[@role='button'][contains(.,'Diseases')]",
            # "admin_drugs": "//div[@role='button'][contains(.,'Drugs')]",
            # "admin_languages": "//div[@role='button'][contains(.,'Languages')]",
            # "admin_site_languages": "//div[@role='button'][contains(.,'Site Languages')]",
            "admin_observation_types": "//div[@role='button'][contains(.,'Observation Types')]",
            # "admin_side_effects": "//div[@role='button'][contains(.,'Side Effects')]",

            # Add more
            }

        crawl_pages(driver, pages_to_visit, input_dir)
    finally:
        driver.quit()


def merge_and_deduplicate_locators(input_dir, output_file):
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    json_files = list(input_dir.glob("*.json"))
    merged = {}

    for path in json_files:
        with open(path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
            for k, v in data.items():
                if v not in merged.values():
                    merged[k] = v

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"✅ Deduplicated JSON saved at {output_file}")


if __name__ == "__main__":
    main()
