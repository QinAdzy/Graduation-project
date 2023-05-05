# -*- coding:utf-8 -*-
# 导入依赖包

from bert_serving.client import BertClient
import numpy as np
import jieba
from collections import Counter
import math


# 定义类
class BertModel:
    def __init__(self):
        try:
            self.bert_client = BertClient(ip='127.0.0.1', port=5555, port_out=5556)  # 创建客户端对象
            # 127.0.0.1 表示本机IP，或使用localhost
        except:
            raise Exception("cannot create BertClient")

    def close_bert(self):
        self.bert_client.close()  # 关闭服务

    def sentence_embedding(self, texts):
        """对输入文本进行embedding
          Args:
            texts: str, 输入文本列表
          Returns:
            texts_vector: float, 返回一个列表，包含text的embedding编码值
        """
        texts = [text[0:50] for text in texts]
        texts_vectors = self.bert_client.encode(texts)
        return texts_vectors  # 获取输出结果

    # 定义一个函数，用于将文本分词
    def segment(self, text):
        seg_list = jieba.cut(text)
        return [seg for seg in seg_list if seg.strip()]

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

    def main(self, input_a, input_b):
        # 创建bert对象
        bert = BertModel()

        #防止超过bert模型tokens的最大输入长度
        input_a = input_a[0:50]
        input_b = input_b[0:50]

        # --- 对输入语句进行embedding ---
        a_vec = bert.sentence_embedding(input_a)
        print('a_vec shape : ', a_vec.shape)

        b_vec = bert.sentence_embedding(input_b)
        print('b_vec shape : ', b_vec.shape)

        # 计算两个语句的相似性
        similarity = bert.caculate_similarity(a_vec, b_vec)
        return similarity

if __name__ == '__main__':
    be = BertModel()
    be.main('阿松大是的','权威人士地方')