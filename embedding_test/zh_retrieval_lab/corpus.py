"""
小规模中文检索实验语料：每条文档有稳定 id，查询带「相关文档 id」便于算 MRR / Recall@k。
内容偏科普与日常用语，便于观察关键词匹配（BM25）与语义匹配（向量）的差异。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Doc:
    doc_id: int
    text: str


@dataclass(frozen=True)
class QueryItem:
    qid: str
    text: str
    relevant_doc_ids: frozenset[int]


# 约 18 条短文：主题分散，部分词面重合、语义需推理
DOCS: list[Doc] = [
    Doc(0, "机器学习是人工智能的一个分支，通过数据训练模型来完成预测或分类任务。"),
    Doc(1, "深度学习使用多层神经网络，在图像识别和自然语言处理中应用广泛。"),
    Doc(2, "支持向量机是一种经典监督学习算法，常用于文本分类。"),
    Doc(3, "Python 适合数据处理与快速原型，生态中有 NumPy、pandas 等库。"),
    Doc(4, "Java 常用于企业级后端服务，强调类型系统与并发工具。"),
    Doc(5, "北京故宫是明清两代的皇家宫殿，现为世界文化遗产。"),
    Doc(6, "西安兵马俑展示了秦代的军事阵列，是中国重要的考古发现。"),
    Doc(7, "四川火锅以麻辣鲜香著称，是川渝地区的代表性饮食。"),
    Doc(8, "高血压患者在饮食上应控制钠盐摄入，并保持规律运动。"),
    Doc(9, "糖尿病管理需要监测血糖，合理用药并配合饮食控制。"),
    Doc(10, "量子计算利用量子比特进行运算，在特定问题上可能超越经典计算机。"),
    Doc(11, "区块链是一种分布式账本技术，强调不可篡改与多方共识。"),
    Doc(12, "太阳系中体积最大的是木星，地球是已知存在生命的行星。"),
    Doc(13, "光合作用使植物利用光能将二氧化碳和水转化为有机物。"),
    Doc(14, "Redis 是内存键值数据库，常用作缓存与消息队列中间件。"),
    Doc(15, "MySQL 是关系型数据库，通过 SQL 进行增删改查。"),
    Doc(16, "台风是热带气旋的一种，登陆前需关注气象预警与避险。"),
    Doc(17, "马拉松长跑对心肺耐力要求高，赛前应循序渐进训练。"),
]

# 8 条查询：部分更依赖「词命中」，部分更依赖「同义/上下位」理解
QUERIES: list[QueryItem] = [
    QueryItem("q1", "神经网络图片识别", frozenset({1})),
    QueryItem("q2", "用数据训练模型做预测", frozenset({0})),
    QueryItem("q3", "皇宫博物院在北京", frozenset({5})),
    QueryItem("q4", "秦陵陪葬坑里的陶俑", frozenset({6})),
    QueryItem("q5", "吃得很辣的那种锅子", frozenset({7})),
    QueryItem("q6", "血糖偏高怎么日常注意", frozenset({9})),
    QueryItem("q7", "内存里很快的键值存储", frozenset({14})),
    QueryItem("q8", "长跑比赛前如何练耐力", frozenset({17})),
]


def doc_by_id() -> dict[int, Doc]:
    return {d.doc_id: d for d in DOCS}
