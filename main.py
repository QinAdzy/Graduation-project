import os
from concurrent.futures import ThreadPoolExecutor
import sys

sys.path.append('../extract')
import Spider as spd
import Extract as ext
import time
import re

multiflag = 1  # 1多线程执行，0单线程执行
item_name = ''  # 获取用户输入关键词
search_flag = '' #用户选择的搜索引擎


# 网页正文提取
def fun(url_name, url):
    try:
        ex = ext.Extractor(url=url, blockSize=3, image=False, keywords=item_name)
        content = ex.getContext()
        if content == "NOT FOUND!" or content == "":
            content = "NOT FOUND!"
            print(f"网页  {url_name} --- {url}  NOT FOUND!")
        # 提取正文后处理
        # 去除网页中html实体字符
        content = re.sub(r'&#[\w]+;', '', content)
        content = re.sub(r'&[\w]+;', '', content)
        ex.WriteFile(name=url_name, content=content, search_flag=search_flag)
    except Exception as e:
        raise e


# 多线程执行
def multhid(urls_dict):
    print(f"提取到的链接有{len(urls_dict)}个\n{urls_dict}")
    start = time.time()
    with ThreadPoolExecutor() as pool:
        pool.map(fun, urls_dict.keys(), urls_dict.values())
    print('算法提取完成！')
    end = time.time()
    print('算法多线程耗时：', end - start, ' second')

    # start = time.time()
    # with ThreadPoolExecutor() as pool:
    #     pool.map(extt.extract, urls_dict.keys(), urls_dict.values())
    # print('Url2article提取完成！')
    # end = time.time()
    # print('Url2article多线程耗时：', end - start, ' second')
    #     contents = list(zip(urls_dict.values(), contents))
    #     for url, content in contents:
    #         print(url, len(content))


# 单线程执行
def sigle(URL):
    title_list= list(URL.keys())
    print(f"提取到的链接有{len(title_list)}个\n{title_list}")
    start = time.time()
    for key in title_list:
        ex = ext.Extractor(url=URL[key], blockSize=3, image=False)
        content = ex.getContext()
        # print(f'网页--{key}--的内容为{content}' + '\n' * 3)
        if content == "NOT FOUND!" or content == '':
            print(f'网页-- {key} + {URL[key]} --的内容为NOT FOUND!')
            continue
        content = re.sub(r'&#[\w]+;', '', content)
        content = re.sub(r'&[\w]+;', '', content)
        ex.WriteFile(name=key, content=content)
    end = time.time()
    print('单线程耗时：', end - start)


def main(keywords, flag):
    global item_name
    item_name = keywords
    global search_flag
    search_flag = flag
    spider = spd.Spider(item_name, flag)

    if flag is 'baidu':
        real_urls_dict = spider.run_baidu()
    else:
        real_urls_dict = spider.run_bing()

    # 创建关键词文件夹存放网页正文提取的文档
    folder_name = f"C:\\Users\\13182\\Desktop\\Work\\extract\\{flag}\\{keywords}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # 多线程提取网页主要内容
    if multiflag:
        multhid(real_urls_dict)
    else:
        sigle(real_urls_dict)
    return real_urls_dict


if __name__ == '__main__':
    main('应届毕业生如何找工作')
