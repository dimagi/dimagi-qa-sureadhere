
import os
import json
from seleniumbase import Driver
from bs4 import BeautifulSoup
from collections import defaultdict
from time import sleep
from common_utilities.load_settings import load_settings

DISALLOWED_TAGS = {
    "script", "noscript", "path", "meta", "style", "link", "router-outlet",
    "base", "title", "svg", "head", "g", "use"
}

ALLOWED_TAG_PREFIXES = ("ng-", "kendo-", "svg")
ALLOWED_TAGS = {"div", "span", "input", "select", "button", "a", "label", "p", "h1", "h2", "h3", "h4", "h5", "h6", "i", "textarea", "form"}

def is_valid_tag(tag):
    return (
        tag.name in ALLOWED_TAGS
        or tag.name.startswith(ALLOWED_TAG_PREFIXES)
    ) and tag.name not in DISALLOWED_TAGS

def extract_attributes(el):
    attr = el.attrs
    locator_data = {}
    for key in ["id", "name", "placeholder", "aria-label", "type", "class"]:
        if key in attr:
            locator_data[key.replace("-", "_")] = attr[key]
    if el.text and el.text.strip():
        locator_data["text"] = el.text.strip()
    locator_data["tag"] = el.name
    return locator_data

def build_xpath(el):
    tag = el.name
    if el.has_attr("id"):
        return f"//{tag}[@id='{el['id']}']"
    if el.has_attr("name"):
        return f"//{tag}[@name='{el['name']}']"
    if el.has_attr("placeholder"):
        return f"//{tag}[@placeholder='{el['placeholder']}']"
    if el.text and el.text.strip():
        return f"//{tag}[normalize-space(text())='{el.text.strip()}']"
    return None

def generate_locators_from_html(page_name, html_source):
    soup = BeautifulSoup(html_source, "html.parser")
    elements = soup.find_all(is_valid_tag)
    locators = {}
    used_names = defaultdict(int)
    for el in elements:
        locator = extract_attributes(el)
        logical_name = locator.get("id") or locator.get("name") or locator.get("placeholder") or locator.get("aria_label") or locator.get("text")
        if not logical_name:
            continue
        logical_name = logical_name.lower().strip().replace(" ", "_").replace("-", "_")
        used_names[logical_name] += 1
        if used_names[logical_name] > 1:
            logical_name = f"{logical_name}_{used_names[logical_name]}"
        xpath = build_xpath(el)
        if not xpath:
            continue
        locator["xpath"] = xpath
        locators[logical_name] = locator
    return locators

def login_to_app(driver, url, username, password):
    driver.get(url)
    sleep(2)
    try:
        driver.find_element("id", "email").send_keys(username)
        driver.find_element("id", "password").send_keys(password)
        driver.find_element("xpath", "//button[@id='next']").click()
        sleep(3)
    except Exception as e:
        print("Login error:", e)

def click_through_dashboard(driver):
    try:
        driver.find_element("xpath", "//a[contains(text(),'Dashboard')]").click()
        sleep(2)
        links = driver.find_elements("xpath", "//a")
        for link in links[:5]:
            try:
                link.click()
                sleep(1)
                driver.back()
                sleep(1)
            except:
                continue
    except Exception as e:
        print("Navigation error:", e)

def main():
    settings = load_settings()
    driver = Driver(uc=True)
    url = settings["url"]
    username = settings["login_username"]
    password = settings["login_password"]
    output_dir = "../POC_files/self_healing_locators_ml"
    os.makedirs(output_dir, exist_ok=True)

    login_to_app(driver, url, username, password)
    html = driver.page_source
    locators = generate_locators_from_html("login", html)
    with open(f"{output_dir}/login.json", "w", encoding="utf-8") as f:
        json.dump(locators, f, indent=2)

    click_through_dashboard(driver)
    html = driver.page_source
    dashboard_locators = generate_locators_from_html("dashboard", html)
    with open(f"{output_dir}/dashboard.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_locators, f, indent=2)

    driver.quit()

if __name__ == "__main__":
    main()
