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

def find_neighbors(entry_id, depth=2):
    visited = set()
    nodes_dict = {}

    nodes = []
    links = []
    def dfs_down(current_id, current_depth):
        if current_id in visited:
            return
        visited.add(current_id)

        # 找到当前论文
        current_paper = collection.find_one({'entry_id': current_id},{"entry_id":1,"title":1,"published":1,"refer_ids":1,"refered_ids":1})
        if not current_paper:
            return
        current_paper.pop('_id')
        current_paper['depth']=-current_depth
        # 添加到节点列表
        # if {**{'id': current_id}, **current_paper}not in nodes:
        #     nodes.append({**{'id': current_id}, **current_paper})
        nodes_dict[current_id] = {**{'id': current_id}, **current_paper}
        if len(nodes)>2000:
            return None
        if current_depth+1 > depth:
            return
        # 找出引用的论文
        for neighbor_id in current_paper.get('refer_ids', []):
            if neighbor_id not in visited:
                links.append({'source': current_id, 'target': neighbor_id, 'id': len(links)})
                dfs_down(neighbor_id, current_depth + 1)

    def dfs_up(current_id, current_depth):
        if current_id in visited:
            return
        visited.add(current_id)

        # 找到当前论文
        current_paper = collection.find_one({'entry_id': current_id},{"entry_id":1,"title":1,"published":1,"refer_ids":1,"refered_ids":1})
        if not current_paper:
            return
        current_paper.pop('_id')
        current_paper['depth']=current_depth
        nodes_dict[current_id] = {**{'id': current_id}, **current_paper}
        # 添加到节点列表
        # if {**{'id': current_id}, **current_paper}not in nodes:
        #     nodes.append({**{'id': current_id}, **current_paper})
        if len(nodes)>2000:
            return None
        if current_depth+1 > depth:
            return
        # 找出引用了当前论文的论文
        for neighbor_id in current_paper.get('refered_ids', []):
            if neighbor_id not in visited:
                links.append({'source': neighbor_id, 'target': current_id, 'id': len(links)})
                dfs_up(neighbor_id, current_depth + 1)

    # 开始查找
    dfs_down(entry_id, 0)
    visited.clear()  # 清除访问记录以便重新查找
    dfs_up(entry_id, 0)

    return {'nodes': list(nodes_dict.values()), 'links': links}

def find_neighbors_aggregation(entry_id, depth=2):
    pipeline = [
        # 从给定的entry_id开始
        {"$match": {"entry_id": entry_id}},
        
        # 递归查找引用和被引用
        {"$graphLookup": {
            "from": collection.name,
            "startWith": "$entry_id",
            "connectFromField": "refer_ids",
            "connectToField": "entry_id",
            "as": "down_neighbors",
            "maxDepth": depth,
            "depthField": "depth"
        }},
        {"$graphLookup": {
            "from": collection.name,
            "startWith": "$entry_id",
            "connectFromField": "entry_id",
            "connectToField": "refer_ids",
            "as": "up_neighbors",
            "maxDepth": depth,
            "depthField": "depth"
        }},
        
        # 合并所有结果
        {"$project": {
            "all_neighbors": {
                "$concatArrays": [
                    [{"$mergeObjects": ["$$ROOT", {"depth": 0}]}],
                    "$down_neighbors",
                    "$up_neighbors"
                ]
            }
        }},
        {"$unwind": "$all_neighbors"},
        {"$replaceRoot": {"newRoot": "$all_neighbors"}},
        
        # 去重
        {"$group": {
            "_id": "$entry_id",
            "doc": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$doc"}},
        
        # 生成节点和链接
        {"$group": {
            "_id": None,
            "nodes": {"$push": {
                "entry_id": "$entry_id",
                "title": "$title",
                "published": "$published",
                "depth": "$depth",
                "refered_ids": "$refered_ids"
            }},
            "links": {"$push": {
                "$map": {
                    "input": "$refer_ids",
                    "as": "ref",
                    "in": {
                        "source": "$entry_id",
                        "target": "$$ref"
                    }
                }
            }}
        }},
        
        # 展平链接数组
        {"$project": {
            "nodes": 1,
            "links": {"$reduce": {
                "input": "$links",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", "$$this"]}
            }}
        }}
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if result:
        return result[0]
    else:
        return {"nodes": [], "links": []}
if __name__=="__main__":
    # # 替换为你要查询的起始论文的entry_id
    entry_id = 'http://arxiv.org/abs/2405.06211v3'
    # print(find_neighbors_aggregation(entry_id=entry_id))
    #
    # # 获取三度之内的邻居
    def has_duplicate_ids(list_of_lists):
        seen_ids = set()  # 用于存储已见的 ID
        for sublist in list_of_lists:
            if sublist:  # 确保子列表不为空
                item_id = sublist['id']  # 假设 ID 在每个子列表的第一个位置
                if item_id in seen_ids:
                    return True  # 找到重复 ID
                seen_ids.add(item_id)  # 添加到集合中
        return False  # 没有重复 ID
    result = find_neighbors(entry_id)
    print(has_duplicate_ids(result['nodes']))
    open('result.txt','w').write('\n'.join([i["id"] for i in result['nodes']]))
    #
    # # # 保存为JSON文件
    # with open('result.json', 'w') as f:
    #     json.dump(result, f, indent=4,default=datetime_converter)
    #
    # print("结果已保存为result.json")
