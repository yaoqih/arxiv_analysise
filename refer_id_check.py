from pymongo import MongoClient
from config import config
import tqdm
# 连接到MongoDB
client = MongoClient(config.mongo_client_url)
db = client['paper_connect']
collection = db['data']
for paper in tqdm.tqdm(collection.find()):
    refer_ids = paper.get('refer_ids', [])
    for refer_id in refer_ids:
        if not collection.find_one({'entry_id': refer_id}):
            id=refer_id.split('/')[-1].split('v')[0]
            if temp:=collection.find_one({'entry_id': {'$regex': f'{id}'}}):
                refer_ids.remove(refer_id)
                refer_ids.append(temp['entry_id'])
                collection.update_one({'entry_id': paper['entry_id']}, {'$set': {'refer_ids': refer_ids}})
            else:
                collection.update_one({'entry_id': paper['entry_id']}, {'$pull': {'refer_ids': refer_id}})