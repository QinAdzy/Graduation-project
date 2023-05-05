import multiprocessing
import string
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

from bert_test import sim
import time
import re
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

flag = 1


class Doc_Sim:
    def __init__(self, keywords, flag):
        self.keywords = keywords
        self.flag = flag
        self.cur_key = ''
        # 进程池之间共享变量是不能使用上文方式的，因为进程池内进程关系并非父子进程，想要共享，必须使用Manager模块来定义。
        # 建立所有文档文件名与句vec的对应关系
        self.docs_vec = multiprocessing.Manager().dict()
        # 建立所有文档文件名与文档内容的对应关系
        self.docs_txt = {}
        # 已经打开过的文件
        self.open_doc = {}
        # tfidf特征向量
        self.tfidf_dict = {}
        # 当前文档与每个文档对应的相似度
        self.sim_docs = {}

    def cut(self, obj, sec):
        return [obj[i:i + sec] for i in range(0, len(obj), sec)]

    # 获取单个文档的句向量编码
    def get_sen_embedding(self, doc):
        bert = sim.BertModel()
        # 对文档中的每个句子做embedding
        doc_vec = bert.sentence_embedding(doc)
        return doc_vec

    # 读取文档
    def read_doc(self, name):
        print("正在读取文档---" + name)

        # 使用指定的编码方式打开文件并读取内容
        with open((f"../extract/{self.flag}/{self.keywords}/" + name), 'r', encoding=self.doc_encoding[name.replace('.txt', '')]) as f2:
            content = f2.read()  # 文档内容
            self.docs_txt[name.replace('.txt', '')] = content

    # 句向量编码sentence_embedding
    def sen_emb(self, name):
        name = name.replace('.txt', '')
        content = self.docs_txt[name]
        doc = re.split('[，！。；？]', content)  # 分割句子,获得该文档的句子列表
        while '' in doc:
            doc.remove('')
        # print(doc)
        print(f"正在获取---{name}---句向量编码")
        doc_vec = self.get_sen_embedding(doc)  # 获取每个句子的embedding
        # 建立文件名与句vec的字典
        self.docs_vec[name] = doc_vec
        print(f"已获取---{name}---句向量编码")

    def tf_idf(self):
        # 定义标点符号列表
        punctuations = string.punctuation
        # 停用词表
        stop_words = []
        with open("../bert_test/cn_stopwords.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                stop_words.append(line.strip())
        # 分词和预处理
        processed_docs = []
        for key in self.docs_txt.keys():
            words = [word for word in jieba.lcut(self.docs_txt[key]) if
                     word not in stop_words and word not in punctuations]
            doc_processed = " ".join(words)
            processed_docs.append(doc_processed)
        # 计算tf-idf特征向量
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(processed_docs)
        # 将稀疏矩阵转换为二维矩阵
        tfidf_array = tfidf_matrix.toarray()

        # 建立字典{文档名：文档特征向量}
        keys = list(self.docs_txt.keys())
        self.tfidf_dict = dict(zip(keys, tfidf_array))

    def caculate_similarity(self, vec_1, vec_2):
        """根据两个语句的vector，计算它们的相似性
          Args:
            vec_1: float, 语句1的vector
            vec_2: float, 语句2的vector
          Returns:
            sim_value: float, 返回相似性的计算值
        """
        # 根据cosine的计算公式
        v1 = np.mat(vec_1)
        v2 = np.mat(vec_2)
        a = float(v1 * v2.T)
        b = np.linalg.norm(v1) * np.linalg.norm(v2)
        cosine = a / b
        return cosine

    # 计算当前打开的网页内容与已经打开过的页面内容进行相似度计算
    def main(self, name, doc):
        cur_doc = self.docs_vec[self.cur_key]
        # print(f'正在计算文档{self.cur_key}和{name}之间的相似度')
        '''
            计算bert文本相似度
        '''
        # 计算相似度得分
        similarity_score = 0
        for s1_vec in cur_doc:
            max_similarity = -1
            for s2_vec in doc:
                simlarity = self.caculate_similarity(s1_vec, s2_vec)
                if simlarity > max_similarity:
                    max_similarity = simlarity
            similarity_score += max_similarity
        similarity_score /= len(cur_doc)

        '''
            获得基于tf-idf的相似度值
        '''
        arrayx = np.array([self.tfidf_dict[self.cur_key], self.tfidf_dict[name]])
        cosine_similarities = cosine_similarity(arrayx)

        # 将两个相似度进行加权融合
        similarity = 0.7 * cosine_similarities[0][1] + 0.3 * similarity_score
        similarity = '{:.4f}'.format(similarity)
        self.sim_docs[name] = similarity
        # print("当前文档为：", self.cur_key, "与文档", name, "的相似度为:", similarity)
        # print(f"其中bert相似度为：{avg_cosin} ， tf-idf相似度为{cosine_similarities[0][1]}")
        # for item1_vec in self.cur_doc:
        #     for doc in self.open_doc.values():
        #         similar = []
        #         for item2_vec in doc:
        #             similar.append(bert.caculate_similarity(item1_vec, item2_vec))
        #         cosin = max(similar)   # 获取最大相似度值

    def embedding(self):
        names = os.listdir(f'../extract/{self.flag}/{self.keywords}')

        # 获取每个文档的编码方式
        self.doc_encoding = {}
        with open(f"../extract/{self.flag}/doc_encoding.txt", 'r', encoding='UTF-8') as f1:
            text = f1.read()
        with open(f"../extract/{self.flag}/doc_encoding.txt", 'a+', encoding='UTF-8') as f2:
            f2.truncate(0)
        temp = text.split('\n')
        for item in temp:
            if item is '':
                continue
            temp2 = item.split('\t')
            self.doc_encoding[temp2[0]] = temp2[1]

        # 多线程加快读取文件
        with ThreadPoolExecutor() as pool_read:
            pool_read.map(self.read_doc, names)
        print("读文件完成！")

        # 多进程为文档做embedding
        if flag:
            start = time.time()
            with ProcessPoolExecutor() as pool_emb:
                pool_emb.map(self.sen_emb, names)
            end = time.time()
            print(f"多进程耗时 {end - start} seconds")
        else:
            start = time.time()
            for name in names:
                self.sen_emb(name)
            end = time.time()
            print(f"单进程耗时 {end - start} seconds")
        print("句embedding完成！")
        self.open_doc = self.docs_vec
        # print(len(obj.docs_vec))
        # exit()

    def calculate(self, cur_key):
        self.cur_key = cur_key
        if len(self.open_doc) != 0:
            with ThreadPoolExecutor() as pool_cal:
                pool_cal.map(self.main, self.open_doc.keys(), self.open_doc.values())
            return self.sim_docs
        else:
            print('暂未打开过任何文档')

    def filter(self):
        import_list = list(self.docs_vec.keys())
        del_doc = []    # 记录已经删除的网页
        for name in self.open_doc.keys():
            if name not in del_doc:
                sim_docs = self.calculate(name)
                for key, sim in sim_docs.items():
                    if key != name and float(sim) > 0.8:
                        try:
                            import_list.remove(key)   # 若存在该网页则删除
                            del_doc.append(key)
                        except:                       # 若不存在则说明该网页已经和其他网页重复被删掉了
                            continue
            else:
                continue
        print(f'筛选的重要网页有 {len(list(import_list))} 个：')
        print('\n'.join(list(import_list)))
        return list(import_list)


if __name__ == '__main__':
    docsim = Doc_Sim('应届毕业生如何找工作')
    docsim.embedding()
    docsim.tf_idf()
    # docsim.calculate('给应届毕业生找工作的几点建议')
    filter_list = docsim.filter()
