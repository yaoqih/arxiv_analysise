import arxiv
import pymongo
from config import config
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor

from pdf_comprese import compress_pdf
import os
import requests
import sys
myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
save_path = config.save_path
pool_num =64
import re
import fitz  # PyMuPDF库


def extract_arxiv_citations(arxiv_data):
    # 编译正则表达式模式
    entey = arxiv_data['entry_id'].split('/')[-1]
    date = entey.split('.')[0]
    entey_id = entey.split('.')[1]
    if not os.path.exists(save_path + date):
        os.makedirs(save_path + date)
    pdf_path = save_path + date + '/' + entey + '.pdf'
    arxiv_pattern = re.compile(r'arXiv:(\d{4}\.\d{4,5})(v\d+)?')

    # 打开PDF文件
    doc = fitz.open(pdf_path)

    citations = set()  # 使用集合来存储唯一的引用

    # 遍历PDF的每一页
    for page in doc:
        # 提取文本内容
        text = page.get_text()

        # 查找所有匹配的arXiv引用
        matches = arxiv_pattern.findall(text)

        # 将匹配结果添加到集合中
        for match in matches:
            arxiv_id = match[0]
            version = match[1] if match[1] else ''
            citations.add(f"arXiv:{arxiv_id}{version}")

        # 提取超链接
        links = page.get_links()
        for link in links:
            if 'uri' in link and 'arxiv.org' in link['uri']:
                url = link['uri']
                arxiv_match = arxiv_pattern.search(url)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    version = arxiv_match.group(2) if arxiv_match.group(2) else ''
                    citations.add(f"arXiv:{arxiv_id}{version}")
    citations=["http://arxiv.org/abs/"+i.split("arXiv:")[1] for i in citations]
    db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"refer_ids":citations,"connected":True}})


# 使用示例
# pdf_path = 'D:/arxiv_data/2312/2312.15796v2.pdf'
# links = extract_arxiv_citations(pdf_path)

if __name__ == "__main__":
    filte={"downloaded": True,"connected": False, "primary_category": {"$regex": "^cs"}}
    # for arxiv_data in db_data.find(filte):
    #     extract_arxiv_citations(arxiv_data)

    pool = Pool(pool_num)
    pool.map_async(extract_arxiv_citations, db_data.find(filte))
    pool.close()
    pool.join()