

import os
from config import config
import  pymongo
from multiprocessing import Pool

save_path = config.save_path
myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]

pool_num =20
import re
import fitz  # PyMuPDF库
filte={"downloaded": True,"connect_extract": False, "primary_category": {"$regex": "^cs"}}
arxiv_id_map={arxiv_data['entry_id'].split('/')[-1].split('v')[0]:arxiv_data['entry_id'] for arxiv_data in db_data.find()}
def extract_arxiv_citations(arxiv_data):
    # 编译正则表达式模式
    entey = arxiv_data['entry_id'].split('/')[-1]
    date = entey.split('.')[0]
    entey_id = entey.split('.')[1]
    if not os.path.exists(save_path + date):
        os.makedirs(save_path + date)
    pdf_path = save_path + date + '/' + entey + '.pdf'
    arxiv_pattern = re.compile(r'arXiv[:.](\d{4}\.\d{4,5})(v\d+)?', re.IGNORECASE)
    arxiv_pattern2 = re.compile(r'http[s]?://arxiv.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(v\d+)?', re.IGNORECASE)
    arxiv_pattern3 = re.compile(r'abs/(\d{4}\.\d{4,5})(v\d+)?', re.IGNORECASE)
    arxiv_pattern4 = re.compile(r'arXiv[:.](\d{4}\d{4,5})(v\d+)?\.', re.IGNORECASE)
    # 打开PDF文件
    try:
        doc = fitz.open(pdf_path)
    except:
        res=db_data.update_one({"entry_id": arxiv_data['entry_id']}, {"$set":{"downloaded":False}})
        open("pdf_open_error.txt","a").write(pdf_path+'\n')
        if res.acknowledged:
            os.remove(pdf_path)
        return
    citations = set()  # 使用集合来存储唯一的引用

    # 遍历PDF的每一页
    for page in doc:
        # 提取文本内容
        text = page.get_text()

        # 查找所有匹配的arXiv引用
        matches = arxiv_pattern.findall(text)+arxiv_pattern2.findall(text)+arxiv_pattern3.findall(text)+arxiv_pattern4.findall(text)
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
                arxiv_match = arxiv_pattern2.search(url)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    version = arxiv_match.group(2) if arxiv_match.group(2) else ''
                    citations.add(f"arXiv:{arxiv_id}{version}")
    citations_res=[]
    for i in citations:
        if temp:=arxiv_id_map.get(i.split("arXiv:")[1].split("v")[0]):
            citations_res.append(temp)
    if arxiv_data['entry_id'] in citations_res:
        citations_res.remove(arxiv_data['entry_id'])
    # print(arxiv_data['entry_id'],citations_res)
    db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"refer_ids":citations_res,"connect_extract":True}})

# 使用示例
# pdf_path = 'D:/arxiv_data/2312/2312.15796v2.pdf'
# links = extract_arxiv_citations(pdf_path)

if __name__ == "__main__":

    # for arxiv_data in db_data.find(filte):
    #     extract_arxiv_citations(arxiv_data)
    pool = Pool(pool_num)
    pool.map_async(extract_arxiv_citations, [_ for _ in db_data.find(filte)])
    pool.close()
    pool.join()
    # extract_arxiv_citations({"entry_id": "http://arxiv.org/abs/2304.00006v1"})
    # extract_arxiv_citations({"entry_id":"http://arxiv.org/abs/2304.00005v1"})