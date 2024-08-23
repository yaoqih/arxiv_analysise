from query import collection
from tqdm import tqdm
# 清空所有文档的refered_ids字段
# collection.update_many({}, {'$set': {'refered_ids': []}})

# 遍历所有文档
from pymongo import UpdateOne
from tqdm import tqdm

def update_reverse_index(collection, batch_size=10000):
    updates = []
    processed = 0
    
    for doc in tqdm(collection.find()):
        entry_id = doc['entry_id']
        refer_ids = doc.get('refer_ids', [])
        
        for ref_id in refer_ids:
            updates.append(UpdateOne(
                {'entry_id': ref_id},
                {'$addToSet': {'refered_ids': entry_id}}
            ))
        
        if len(updates) >= batch_size:
            try:
                collection.bulk_write(updates, ordered=False)
                processed += len(updates)
                updates = []
            except Exception as e:
                print(f"Error during bulk write: {e}")
    
    if updates:
        try:
            collection.bulk_write(updates, ordered=False)
            processed += len(updates)
        except Exception as e:
            print(f"Error during final bulk write: {e}")
    
    print(f"处理完成，更新了 {processed} 条记录")

# 使用函数
update_reverse_index(collection)
