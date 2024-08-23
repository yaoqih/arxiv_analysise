import multiprocessing as mp
from collections import defaultdict
import ahocorasick
import os
from pymongo import MongoClient
from config import config
import redis   # 导入redis 模块
import  fitz
from tqdm import  tqdm
r = redis.Redis(host='localhost', port=6379, decode_responses=True, db=0, password='hwt439876.')
# 连接到MongoDB
client = MongoClient(config.mongo_client_url)
db = client['paper_connect']
collection = db['data']
filte={"downloaded": True,"connect_extract_title": False, "primary_category": {"$regex": "^cs"}}
def load_strings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]


def load_papers(directory):
    papers = []
    for date in os.listdir(directory):
        if os.path.isdir(directory+date):  # 假设论文是txt文件
            for filename in os.listdir(os.path.join(directory, date)):
                if filename.endswith('.pdf'):
                    if not r.exists(os.path.join(directory, date, filename)):
                        papers.append(os.path.join(directory, date, filename))
    return papers


def build_automaton(strings):
    A = ahocorasick.Automaton()
    for idx, s in enumerate(strings):
        A.add_word(s, (idx, s))
    A.make_automaton()
    return A


def process_paper(paper, automaton):
    results = []
    for _, (idx, s) in automaton.iter(paper):
        results.append(s)
    return results


def process_chunk(chunk, automaton):
    results = []
    for paper in tqdm(chunk):
        try:
            doc = fitz.open(paper)
        except:
            continue
        paper_info=collection.find_one({"entry_id": 'http://arxiv.org/abs/'+paper.split('/')[-1][:-4]})
        if not paper_info:
            continue
        # 遍历PDF的每一页
        for page in range(int(doc.page_count/2),doc.page_count):
            # 提取文本内容
            text = doc[page].get_text()
            results=process_paper(text, automaton)
            for title in results:
                refer_paper=collection.find_one({"title": title}, {"entry_id": 1})
                if refer_paper['entry_id'] != paper_info['entry_id']:
                    collection.update_one({"entry_id": refer_paper['entry_id']}, {"$addToSet": {"refered_ids": paper_info['entry_id']}})
                    collection.update_one({"entry_id": paper_info['entry_id']}, {"$addToSet": {"refer_ids": refer_paper['entry_id']}})
        collection.update_one({"entry_id": paper_info['entry_id']}, {"$set": {"connect_extract_title": True}})
        # r.set(paper,1)
    return results


def main():
    # 加载字符串列表
    strings = [i['title'] for i in collection.find({},{"title":1}) if len(i['title'])>40]
    # open('title.txt','w',encoding='utf-8').write('\n'.join(strings))
    # 构建Aho-Corasick自动机
    automaton = build_automaton(strings)

    # 加载论文
    papers = load_papers('D:/arxiv_data/')

    for paper in tqdm(papers):
        process_chunk([paper], automaton)

    # 确定进程数
    num_processes = mp.cpu_count()-4

    # 将论文分成多个块
    chunk_size = len(papers) // num_processes
    chunks = [papers[i:i + chunk_size] for i in range(0, len(papers), chunk_size)]

    # 创建进程池
    pool = mp.Pool(processes=num_processes)

    # 并行处理论文
    results = pool.starmap(process_chunk, [(chunk, automaton) for chunk in chunks])

    # 关闭进程池
    pool.close()
    pool.join()

    # 合并结果
    # final_results = []
    # for chunk_result in results:
    #     final_results.extend(chunk_result)

    # 输出结果
    # for i, paper_result in enumerate(final_results):
    #     print(f"Paper {i}:")
    #     for string_idx, count in paper_result.items():
    #         print(f"  String {string_idx}: {count} occurrences")


if __name__ == '__main__':
    # main()

    strings = [i['title'] for i in collection.find({}, {"title": 1}) if len(i['title']) > 40]
    # open('title.txt','w',encoding='utf-8').write('\n'.join(strings))
    # 构建Aho-Corasick自动机
    automaton = build_automaton(strings)
    paper_datas=[arxiv_data['entry_id'].split('/')[-1] for arxiv_data in collection.find(filte)]
    process_chunk([f"D:/arxiv_data/{i.split('.')[0]}/{i}.pdf" for i in paper_datas], automaton)
