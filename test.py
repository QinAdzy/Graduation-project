# -*- coding: utf-8 -*-
import random

import chardet
import requests
import requests_html
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import re
import matplotlib.pyplot as plt

DBUG = 0

reBODY = re.compile(r'<body.*?>([\s\S]*?)<\/body>', re.I)
reCOMM = r'<!--.*?-->'
reTRIM = r'<{0}.*?>([\s\S]*?)<\/{0}>'
reTAG = r'<[\s\S]*?>|[ \t\r\f\v]'

reIMG = re.compile(r'<img[\s\S]*?src=[\'|"]([\s\S]*?)[\'|"][\s\S]*?>')


class Extractor():
    def __init__(self, url="", blockSize=3, timeout=10, image=False):
        self.url = url
        self.blockSize = blockSize
        self.timeout = timeout
        self.saveImage = image
        self.rawPage = ""
        self.ctexts = []
        self.cblocks = []
        self.encoding = "UTF-8"
        self.threshold = 86

    def get_encoding(self, html):
        encoding = re.findall('<meta.*?charset="?([\w-]*).*>', html, re.I)
        if encoding:
            return encoding[0]
        return 'UTF-8'

    def getRawPage(self):
        user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
            "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15"
        ]

        headers = {'User-Agent': random.choice(user_agent_list),
                   'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
        try:
            session = requests_html.HTMLSession()
            resp = session.get(self.url, timeout=None, headers=headers)
        except:
            return 404, "NOT FOUND!"
        if DBUG: print(resp.encoding)
        self.encoding = self.get_encoding(resp.text)
        if resp.encoding == "ISO-8859-1":
            try:
                content = resp.text.encode("ISO-8859-1").decode('utf-8')
            except:
                content = resp.text.encode("ISO-8859-1").decode('gbk')
        else:
            content = resp.text
        return resp.status_code, content

    def processTags(self):
        self.body = re.sub(reCOMM, "", str(self.body))
        self.body = re.sub(reTRIM.format("script"), "", re.sub(reTRIM.format("style"), "", self.body))
        # self.body = re.sub(r"[\n]+","\n", re.sub(reTAG, "", self.body))
        self.body = re.sub(reTAG, "", self.body)

    def processBlocks(self):
        self.ctexts = self.body.split("\n")
        self.textLens = [len(text) for text in self.ctexts]
        self.charLens = self.character_Density()

        if len(self.ctexts) < self.blockSize:
            return ''.join(self.ctexts)

        self.char_blocks = self.cblocks = [0] * (len(self.ctexts) - self.blockSize + 1)
        lines = len(self.ctexts)
        for i in range(self.blockSize):
            self.cblocks = list(
                map(lambda x, y: (x + y) / self.blockSize, self.textLens[i: lines - 1 - self.blockSize + i],self.cblocks))
            self.char_blocks = list(
                map(lambda x, y: x + y, self.charLens[i: lines - 1 - self.blockSize + i], self.char_blocks))
        self.weight = list(map(lambda x, y: x * (y + 1), self.cblocks, self.char_blocks))
        # '''数据可视化
        # 解决中文显示问题
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 文本密度统计图
        plt.subplot(1, 3, 1)
        y1 = self.cblocks
        x1 = [i for i in range(1, len(self.cblocks) + 1)]
        plt.title("文本块密度图")
        plt.bar(x1, y1)
        # 符号密度统计图
        plt.subplot(1, 3, 2)
        y2 = self.char_blocks
        x2 = [i for i in range(1, len(self.cblocks) + 1)]
        plt.title("标点符号密度图")
        plt.bar(x2, y2)
        # 融合符号密度特征统计图
        plt.subplot(1, 3, 3)
        y3 = self.weight
        x3 = [i for i in range(1, len(self.cblocks) + 1)]
        plt.title("总密度图")
        plt.bar(x3, y3)

        plt.show()
        # '''
        try:
            max_weight = max(self.weight)
        except Exception as e:
            print(self.ctexts, len(self.ctexts))
            raise e

        if DBUG: print(max_weight)

        # 文本密度筛选范围
        self.start = self.end = self.weight.index(max_weight)
        while self.start > 0 and self.weight[self.start] > min(self.cblocks):
            self.start -= 1
        while self.end < lines - self.blockSize - 1 and self.weight[self.end] > min(self.cblocks):
            self.end += 1

        return "".join(self.ctexts[self.start:self.end])

    def character_Density(self):
        self.char_text = [0] * len(self.ctexts)
        char = [',', '.', '?', '!', '，', '。', '？', '"', '“', ';', ':', '：', '、', '‘']
        for index, item in enumerate(self.ctexts):
            for i in char:
                if i in item:
                    self.char_text[index] += 1
        return self.char_text

    def processImages(self):
        self.body = reIMG.sub(r'{{\1}}', self.body)

    def getContext(self):
        code, self.rawPage = self.getRawPage()
        print(f"请求状态码为：{code}")
        if code is not 200:
            print("网页", self.url, 'NOT FOUND！')
        try:
            self.body = re.findall(reBODY, self.rawPage)[0]
        except:
            self.body = self.rawPage
        if DBUG: print(code, self.rawPage)
        if self.saveImage:
            self.processImages()
        self.processTags()
        return self.processBlocks()

    # 根据网页编码写文件
    def WriteFile(self, name='', content=''):
        try:
            with open('C:\\Users\\13182\\Desktop\\' + name + '.txt', 'w',
                      encoding=self.encoding) as f:
                f.write(content)
        except Exception as e:
            raise e


if __name__ == '__main__':
    # item_name = '网页正文提取'
    # spider = spd.URL_Spider(item_name)
    # URL = spider.run()
    ex = Extractor(url='https://www.runoob.com/python3/python3-tutorial.html',
                   blockSize=3, image=False)
    content = ex.getContext()
    # 提取正文后处理
    # 去除网页中html实体字符
    content = re.sub(r'&#[\w]+;', '', content)
    content = re.sub(r'&[\w]+;', '', content)
    # ex.WriteFile(name='111', content=content)
    print(content)
