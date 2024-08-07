from pymongo import MongoClient
import json
from config import config
from datetime import datetime

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
# 连接到MongoDB
client = MongoClient(config.mongo_client_url)
db = client['paper_connect']
collection = db['data']

def find_neighbors(entry_id, depth=3):
    visited = set()
    nodes = []
    links = []
    def dfs_down(current_id, current_depth):
        if current_depth > depth:
            return
        if current_id in visited:
            return
        visited.add(current_id)

        # 找到当前论文
        current_paper = collection.find_one({'entry_id': current_id})
        if not current_paper:
            return
        current_paper.pop('_id')
        # 添加到节点列表
        nodes.append({**{'id': current_id}, **current_paper})

        # 找出引用的论文
        for neighbor_id in current_paper.get('refer_ids', []):
            if neighbor_id not in visited:
                links.append({'source': current_id, 'target': neighbor_id, 'id': len(links)})
                dfs_down(neighbor_id, current_depth + 1)

    def dfs_up(current_id, current_depth):
        if current_depth > depth:
            return
        if current_id in visited:
            return
        visited.add(current_id)

        # 找到当前论文
        current_paper = collection.find_one({'entry_id': current_id})
        if not current_paper:
            return
        current_paper.pop('_id')
        # 添加到节点列表
        if {**{'id': current_id}, **current_paper}not in nodes:
            nodes.append({**{'id': current_id}, **current_paper})

        # 找出引用了当前论文的论文
        cursor = collection.find({'refer_ids': current_id})
        for citing_paper in cursor:
            citing_id = citing_paper['entry_id']
            if citing_id not in visited:
                links.append({'source': citing_id, 'target': current_id, 'id': len(links)})
                dfs_up(citing_id, current_depth + 1)

    # 开始查找
    dfs_down(entry_id, 0)
    visited.clear()  # 清除访问记录以便重新查找
    dfs_up(entry_id, 0)

    return {'nodes': nodes, 'links': links}


# # 替换为你要查询的起始论文的entry_id
# entry_id = 'http://arxiv.org/abs/2106.13008v5'
#
# # 获取三度之内的邻居
# result = find_neighbors(entry_id)
#
# # 保存为JSON文件
# with open('result.json', 'w') as f:
#     json.dump(result, f, indent=4,default=datetime_converter)
#
# print("结果已保存为result.json")
