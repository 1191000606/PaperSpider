import json
import os
import threading
import time
import timeit

import requests
from bs4 import BeautifulSoup

from BasicSpider import BasicSpider, headers


class ACLSpider(BasicSpider):
    first_level_url = "https://dblp.uni-trier.de/db/conf/acl/index.html"
    drop_box_access_name = "electronic edition @ aclanthology.org (open access)"
    buffer_result = []

    @staticmethod
    def get_paper_kind(id: str) -> str:
        index = id.split("/")
        year = index[2][:4]

        paper_kind = {"-1": "Long Papers", "-2": "Short Papers", "s": "Student Research Workshop", "-s": "Student Research Workshop", "f": "Findings", "d": "System Demonstrations", "-d": "System Demonstrations", "t": "Tutorial Abstracts", "-t": "Tutorial Abstracts", "": "Long Papers"}
        if year == "2019":
            paper_kind = {"-1": "Long Papers", "-2": "Student Research Workshop", "-3": "System Demonstrations", "-4": "Tutorial Abstracts"}
        elif year == "2018":
            paper_kind = {"-1": "Long Papers", "-2": "Short Papers", "-3": "Student Research Workshop", "-4": "System Demonstrations", "-5": "Tutorial Abstracts"}
        elif int(year) <= 2011 & int(year) >= 2005:
            paper_kind = {"": "Long Papers", "s": "Short Papers", "r": "Student Research Workshop", "d": "System Demonstrations", "t": "Tutorial Abstracts"}
        elif int(year) <= 2004:
            paper_kind = {"": "Long Papers", "-sr": "Student Research Workshop", "-p": "System Demonstrations", "c": "额外处理"}

        if index[1] != "acl":
            category = index[2][:4] + " ACL Workshop on " + index[1]
        else:
            if index[2][4:] in paper_kind.keys():
                category = index[2][:4] + " ACL " + paper_kind[index[2][4:]]
            else:
                category = index[2][:4] + " ACL Workshop on " + index[2][4:]

        return category

    @staticmethod
    def get_paper_info(url):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding

        page = response.text
        soup = BeautifulSoup(page, 'lxml')

        temp1 = soup.find("div", class_="row acl-paper-details")

        if temp1.div.dl.find_all("dd")[10] == "":
            print(url + "无页码，认为非论文")
        try:
            abstract = temp1.find("div", class_="card-body acl-abstract").span.text
        except:
            print(url + "无摘要")
            abstract = ""

        temp2 = soup.find(id="main-container").section.div
        title = temp2.h2.a.text
        authors = []
        for i in temp2.p.find_all("a"):
            authors.append(i.text)
        author = ",".join(authors)
        keyword = ""

        return title, abstract, keyword, author, url

    @staticmethod
    def single_crawler(urls, year, paper_type):
        ret = []
        for url in urls:
            if url[:16] == "https://doi.org/":
                print("doi链接暂时未找到爬取方法，因此" + url + "无法访问")
                continue
            try:
                paper_info = ACLSpider.get_paper_info(url)
            except:
                print("获取" + url + "页面出错")
            else:
                ret.append({"title": paper_info[0], "abstract": paper_info[1], "keywords": paper_info[2], "author": paper_info[3], "year": year, "type": paper_type, "url": paper_info[4]})
        ACLSpider.buffer_result += ret

    @staticmethod
    def crawler():
        second_level_url = ACLSpider.get_second_level_url(ACLSpider.first_level_url, ACLSpider.get_paper_kind)
        second_level_url.pop("2003 ACL 额外处理")
        second_level_url.pop("2001 ACL 额外处理")

        for i in second_level_url.items():
            category = i[0]
            year = category[:4]
            paper_type = category[9:]

            if paper_type == "Tutorial Abstracts":
                continue

            url = i[1]

            third_level_url = ACLSpider.get_third_level_url(url, ACLSpider.drop_box_access_name)

            index = 0
            while True:
                t_list = []

                filename = year + paper_type + str(index) + "-" + str(min(index + 200, third_level_url.__len__() - 1)) + ".json"
                if os.path.exists("./result/" + filename):
                    print(filename + "已经存在")
                    if index + 200 < third_level_url.__len__():
                        index += 200
                        continue
                    else:
                        break

                for j in range(40):
                    if index + 5 < third_level_url.__len__():
                        t = threading.Thread(target=ACLSpider.single_crawler, args=(third_level_url[index:index + 5], year, paper_type))
                        index += 5
                        t_list.append(t)
                    else:
                        t = threading.Thread(target=ACLSpider.single_crawler, args=(third_level_url[index:], year, paper_type))
                        index = third_level_url.__len__() - 1
                        t_list.append(t)
                        break

                print("40个线程开始了")
                a = time.time()
                for t in t_list:
                    t.start()

                for t in t_list:
                    t.join()

                print("40个线程跑完了:" + str(time.time() - a))

                f = open("./result/" + filename, "x")
                json.dump(ACLSpider.buffer_result, f)
                f.close()
                ACLSpider.buffer_result = []

                if index == third_level_url.__len__() - 1:
                    break
