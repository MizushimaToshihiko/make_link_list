# -*- coding: utf-8 -*-
import csv
import time
import os
import sys
from selenium import webdriver

chromedriver_path = os.environ["CONDA_PREFIX"]+r"\chromedriver.exe"

cur_dir = os.getcwd()
download_dir = f'{cur_dir}' + r"\link_list"
# URLリストの指定
url_list = download_dir + "\\_url_list.csv"

chrome_Options = webdriver.ChromeOptions()
driver = webdriver.Chrome()
# set the distination of download
prefs = {'download.default_directory' : download_dir}
chrome_Options.add_argument('--headless')
chrome_Options.add_experimental_option('prefs', prefs)
chrome_Options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_Options.use_chromium = True
# ブラウザの起動
driver = webdriver.Chrome(
    executable_path= chromedriver_path,
    chrome_options=chrome_Options,
)  # chromedriver.exe読み込み
driver.set_page_load_timeout(600) # ページロード最大600秒

crawl_range = ""
ng_chars = "#?"

def my_index(s, x, default=False):
    """
    my_index returns x's position in s, otherwise default.
    from: https://github.com/nkmk/python-snippets/blob/ac750e7abd072f1beb0c2507d75d2007bff7db04/notebook/list_index.py#L14-L27
    """
    return s.index(x) if x in s else default

def crawl(url):
    """
    crawl
    """
    # In the case that url is empty or out of 'crawl_range'.
    if url == "" or url[:34] != crawl_range:
        return
    # read url_list
    with open(url_list, mode="r") as f:
        urls = f.read().split("\n")
        if url in urls :
            return
    # write url to url_list
    with open(url_list, mode="a", newline="") as f:
        f.write(url+"\n")

    driver.get(url)
    time.sleep(1)

    url_f = url.replace(crawl_range, "")
    forbidden = '"<>|:*?¥/'
    for forb in forbidden:
        url_f = url_f.replace(forb, "_")
    print(url, url_f)

    with open(download_dir + "\\" + url_f + ".csv",
        mode="w", newline="", encoding="cp932", errors="ignore") as c:
        f = csv.writer(c)
        f.writerow([url])
        f.writerow(["リンクテキスト", "URL"])

        # aタグのhrefをelementでリスト化
        elements = driver.find_elements_by_xpath("//a[@href]")
        l = []
        crawl_urls = []
        for element in elements:
            if element.get_attribute("textContent") != "":
                l = [element.get_attribute("textContent"), element.get_attribute("href")]
            else:
                elem = element.find_elements_by_xpath(".//img")
                if len(elem) > 0:
                    l = ["[画像]"+elem[0].get_attribute("alt"), element.get_attribute("href")]
                else:
                    l = [element.get_attribute("textContent"), element.get_attribute("href")]
            f.writerow(l)
            crawl_urls.append(element.get_attribute("href"))

    for u in crawl_urls:
        for ng in ng_chars:
            idx = my_index(u, ng, -1)
            if idx != -1:
                u = u[:idx]
        crawl(u)


if __name__ == "__main__":
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    with open(url_list, mode = "w") as f:
        f.truncate(0)

    crawl_range = sys.argv[1][:sys.argv[1].rindex("/")+1]
    crawl(sys.argv[1])

    driver.quit()
