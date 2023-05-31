import json
import time

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',

}


class BasicSpider:
    @staticmethod
    def get_second_level_url(first_level_url, get_paper_kind):
        response = requests.get(first_level_url, headers=headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding

        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        index_set = soup.find_all("li", class_="entry editor toc")

        second_level_url = {}

        for i in index_set:
            url = i.nav.ul.li.div.a["href"]
            category = get_paper_kind(i["id"])
            second_level_url[category] = url

        return second_level_url

    @staticmethod
    def get_third_level_url(url, drop_box_access_name):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding

        page = response.text

        soup = BeautifulSoup(page, 'lxml')

        entry_set = soup.body.find_all("li", class_="entry inproceedings")

        ret = []
        for entry in entry_set:
            ee_list = entry.nav.ul.li.find_all("li", class_="ee")
            temp = ""
            for ee in ee_list:
                temp = ee.a["href"]
                if ee.a.text == drop_box_access_name:
                    break
            ret.append(temp)

        return ret


ret = BasicSpider.get_third_level_url("https://dblp.uni-trier.de/db/conf/acl/acl2022-1.html", "electronic edition @ aclanthology.org (open access)")
