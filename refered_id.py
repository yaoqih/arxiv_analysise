from query import collection
from tqdm import tqdm
# 清空所有文档的refered_ids字段
collection.update_many({}, {'$set': {'refered_ids': []}})

# 遍历所有文档
for doc in tqdm(collection.find()):
    entry_id = doc['entry_id']
    refer_ids = doc.get('refer_ids', [])
    
    # 对于每个引用的文档，更新其refered_ids字段
    for ref_id in refer_ids:
        collection.update_one(
            {'entry_id': ref_id},
            {'$addToSet': {'refered_ids': entry_id}}
        )

print("处理完成")
