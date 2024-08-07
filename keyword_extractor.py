# -*- coding: utf-8 -*-
import csv
import time
import os
import sys
from selenium import webdriver
from urllib.parse import urlparse

chromedriver_path = os.environ["CONDA_PREFIX"] + r"\chromedriver.exe"

cur_dir = os.getcwd()
download_dir = f"{cur_dir}" + r"\link_list"
# URLリストの指定
url_list = download_dir + "\\_url_list.csv"
matched_urls_file = download_dir + "\\matched_urls.csv"

chrome_Options = webdriver.ChromeOptions()
prefs = {"download.default_directory": download_dir}
chrome_Options.add_argument("--headless")
chrome_Options.add_experimental_option("prefs", prefs)
chrome_Options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_Options.use_chromium = True

driver = webdriver.Chrome(
    executable_path=chromedriver_path,
    options=chrome_Options,
)
driver.set_page_load_timeout(600)  # ページロード最大600秒

CRAWL_RANGE = ""
NG_CHARS = "#?"
KEYWORDS = []  # 検索語を格納するリスト


def my_index(s, x, default=False):
    """
    my_index returns x's position in s, otherwise default.
    from: https://github.com/nkmk/python-snippets/blob/ac750e7abd072f1beb0c2507d75d2007bff7db04/notebook/list_index.py#L14-L27
    """
    return s.index(x) if x in s else default


def is_url_within_range(url):
    """
    Checks if the URL is within the defined CRAWL_RANGE.
    """
    if url == "" or urlparse(url).netloc != CRAWL_RANGE:
        print(f"URL is empty or out of range: {url}")
        return False
    return True


def read_visited_urls():
    """
    Reads the list of visited URLs from url_list file.
    """
    if not os.path.exists(url_list):
        return []

    with open(url_list, mode="r") as f:
        return f.read().split("\n")


def add_url_to_visited(url):
    """
    Adds a URL to the url_list file.
    """
    with open(url_list, mode="a", newline="") as f:
        f.write(url + "\n")


def save_links_to_csv(url, links):
    """
    Saves the links from a page to a CSV file.
    """
    url_f = url.replace(CRAWL_RANGE, "")
    forbidden = '"<>|:*?¥/'
    for forb in forbidden:
        url_f = url_f.replace(forb, "_")

    with open(
        download_dir + "\\" + url_f + ".csv",
        mode="w",
        newline="",
        encoding="cp932",
        errors="ignore",
    ) as c:
        f = csv.writer(c)
        f.writerow([url])
        f.writerow(["リンクテキスト", "URL"])
        f.writerows(links)


def save_matched_url(url):
    """
    Saves the URL to the matched_urls file.
    """
    with open(matched_urls_file, mode="a", newline="") as f:
        f.write(url + "\n")


def extract_links():
    """
    Extracts all the links from the current page.
    """
    elements = driver.find_elements("xpath", "//a[@href]")
    print(f"The number of elements: {len(elements)}")
    links = []
    for element in elements:
        link_text = element.get_attribute("textContent")
        if link_text:
            links.append([link_text, element.get_attribute("href")])
        else:
            img_elements = element.find_elements("xpath", ".//img")
            if img_elements:
                links.append(
                    [
                        "[画像]" + img_elements[0].get_attribute("alt"),
                        element.get_attribute("href"),
                    ]
                )
            else:
                links.append([link_text, element.get_attribute("href")])
    return links


def contains_keywords():
    """
    Check if the page contains specific keywords.
    """
    page_source = driver.page_source
    return any(keyword in page_source for keyword in KEYWORDS)


def crawl(url):
    """
    Main function to perform crawling.
    """
    if not is_url_within_range(url):
        return

    visited_urls = read_visited_urls()
    if url in visited_urls:
        return

    add_url_to_visited(url)

    try:
        driver.get(url)
        print(f"WebDriver start: {url}")
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return
    time.sleep(1)

    if contains_keywords():
        save_matched_url(url)

    links = extract_links()
    save_links_to_csv(url, links)

    crawl_urls = [link[1] for link in links]

    for u in crawl_urls:
        for ng in NG_CHARS:
            idx = my_index(u, ng, -1)
            if idx != -1:
                u = u[:idx]
        crawl(u)


if __name__ == "__main__":
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    with open(url_list, mode="w") as f:
        f.truncate(0)

    with open(matched_urls_file, mode="w") as f:
        f.truncate(0)

    if len(sys.argv) < 3:
        print("Usage: python script_name.py <URL> <keyword1> [<keyword2> ...]")
        sys.exit(1)

    CRAWL_RANGE = urlparse(sys.argv[1]).netloc
    KEYWORDS = sys.argv[2:]
    crawl(sys.argv[1])

    driver.quit()
