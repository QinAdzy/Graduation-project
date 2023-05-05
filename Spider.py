from selenium import webdriver
from selenium.webdriver.common.by import By  # By是selenium中内置的一个class，在这个class中有各种方法来定位元素
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re
import requests
from pyquery import PyQuery as pq
from selenium.webdriver.support.wait import WebDriverWait

DEBUG = 0
real_URL = {}  # {文章标题：文章链接}


class Spider:
    def __init__(self, item_name, flag):
        self.num_pages = 3
        self.item_name = item_name
        # 用户选择百度搜索引擎
        if flag is "baidu":
            self.url = 'https://www.baidu.com/'  # 登录网址
            options = webdriver.ChromeOptions()  # 谷歌选项
            # 设置为开发者模式，避免被识别
            options.add_experimental_option('excludeSwitches',
                                            ['enable-automation'])
            options.add_argument("--disable-infobars")  # 禁用浏览器正在被自动化程序控制的提示
            self.browser = webdriver.Chrome(executable_path="F:/PythonCharm/chromedriver_win32/chromedriver.exe", options=options)
            self.wait = WebDriverWait(self.browser, 2)
        # 用户使用bing搜索引擎
        else:
            # 启动Edge浏览器
            self.browser = webdriver.Edge(executable_path="F:/PythonCharm/chromedriver_win32/msedgedriver.exe")

    def run_baidu(self):
        """登陆接口"""
        self.browser.get(self.url)
        # 这里设置等待：等待输入框
        # login_element = self.wait.until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, 'div.input-plain-wrap > .fm-text')))

        """
            模拟用户cookie登录,需要经常更换cookie信息
                目的：防止百度反爬机制，增加爬虫稳定性
        """
        cookie_1 = {"name": "BAIDUID", "value": "8C01DF45AEF14DFADDFDF74093890CA9:SL=0:NR=10:FG=1"}
        cookie_2 = {"name": "BDUSS", "value": "9Va0VpNGt1S29QenhKNTVpZ0c2UnlWTWVvdnA1WGxnUFJpam0yczhQekE1RGhqSVFBQUFBJCQAAAAAAQAAAAEAAABOj8cGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBXEWPAVxFjam"}
        time.sleep(1)
        self.browser.add_cookie(cookie_1)
        self.browser.add_cookie(cookie_2)
        self.browser.get(self.url)

        input_edit = self.browser.find_element(By.CSS_SELECTOR, '#kw')  # 等待搜索框加载出来
        input_edit.clear()  # 清空搜索框
        input_edit.send_keys(self.item_name)  # 输入搜索内容

        search_button = self.browser.find_element(By.CSS_SELECTOR, '#form > span > #su')  # 等待搜索按钮可以被点击
        search_button.click()  # 点击

        current_url = self.browser.current_url  # 获取当前页面 url
        time.sleep(random.uniform(1, 2))  # 加入时间间隔，速度太快可能会抓不到数据

        # 获取搜索到每一页的Html
        for i in range(1, self.num_pages+1):
            try:
                initial_url = str(current_url).split('&pvid')[0]
                url = initial_url + '&pn=' + str((i - 1) * 10)
                # print(data_url)
                time.sleep(random.uniform(2, 3))  # 加入时间间隔，速度太快可能会抓不到数据
                self.browser.get(url)
                html = self.browser.page_source  # 获取 html

                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#container > #content_left > div')))

                self.parse_html(html)  # 对 html 网址进行解析
                time.sleep(random.uniform(2, 3))  # 设置频率
            except Exception as e:
                print('Error Next page', e)
                exit()
                # self.txt_file.close()
        real_URL.pop('None', 'None')  # 去除空连接
        if DEBUG:
            print(real_URL, '\n一共抓取链接个数：', len(real_URL))
        return real_URL

    # 解析每一页的Html --> 获取所有链接
    def parse_html(self, html):
        doc = pq(html)
        items = doc('#content_left > div.new-pmd > div').items()
        for item in items:
            try:
                if item.find('div.c-row> div.c-span12 > div.c-border > div.title-contanier_RY4Rg > '
                             'div.title-row_2ymNF > a').text():
                    product = {
                        'name': item.find('div > div > div > div > div > a > span').text().replace('\n', '\t')
                        if item.find('div > div > div > div > div > a > span').text() else 'None',
                        'data_url': item.find('div > div > div > div > div > a').attr('href')
                        if item.find('div > div > div > div > div > a').text() else 'None'
                    }
                else:
                    product = {
                        'name': item.find('div > h3 > a').text().replace('\n', '\t')
                        if item.find('div > h3 > a').text() else (item.find('div > div > div > div > div > div > a').text().replace('\n', '\t') if item.find('div > div > div > div > div > div > a').text() else 'None'),
                        'data_url': item.find('div > h3 > a').attr('href')
                        if item.find('div > h3 > a').attr('href') else (item.find('div > div > div > div > div > div > a').attr('href') if item.find('div > div > div > div > div > div > a').attr('href') else 'None')
                    }
                # print(product)
                global real_URL
                real_URL[self.Replace(product['name'])] = self.get_realURL(product['data_url'].strip())
            except Exception as e:
                print('Error {}'.format(e))

    def get_realURL(self, v_url):
        '''
        获取百度链接真实地址
        '''
        headers = {  # 模拟浏览器头部信息
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        r = requests.get(v_url, headers=headers, allow_redirects=False)  # 不允许重定向
        if r.status_code == 302:  # 如果状态码为302，就从响应头中获取真实地址
            real_url = r.headers.get('location')
        else:
            real_url = re.findall("URL='(.*?)'", r.text)[0]
        return real_url

    # 去除windos下包含非法文件命名规则的字符
    def Replace(self, name):
        s = re.sub(r'[\/:*>?"<>|]*', '', name)
        return s

    def run_bing(self):
        wait = WebDriverWait(self.browser, 10)
        # 防止出现相同标题但不同链接的情况出现
        chars = []
        for i in range(65, 91):
            chars.append(chr(i))
        # 循环遍历每一页的搜索结果
        for page in range(self.num_pages):
            # 构造搜索结果页面的URL
            url = "https://www.bing.com/search?q=" + self.item_name + "&first=" + str(page * 10)
            # 加载搜索结果页面
            self.browser.get(url)
            time.sleep(2)
            # 显式等待搜索结果加载完成
            search_results = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@class='b_algo']")))
            # 遍历每个搜索结果并输出标题和链接
            for result in search_results:
                title = result.find_element_by_xpath(".//h2").text
                link = result.find_element_by_xpath(".//a").get_attribute("href")
                global real_URL
                if real_URL.get(title) is None:
                    real_URL[self.Replace(title)] = link
                elif real_URL[title] != link:
                    random_char = random.choice(chars)
                    chars.remove(random_char)
                    title = title + random_char
                    real_URL[self.Replace(title)] = link
                else:
                    continue
            time.sleep(random.uniform(1, 2))  # 设置频率
        return real_URL


if __name__ == '__main__':
    item_name = '健康生活习惯'
    flag = 'bing'
    spider = Spider(item_name, flag)
    if flag is 'baidu':
        real_urls_dict = spider.run_baidu()
    else:
        real_urls_dict = spider.run_bing()
    print(real_urls_dict.keys())
    print(len(real_urls_dict))
