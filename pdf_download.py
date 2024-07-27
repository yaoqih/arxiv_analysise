import traceback

import arxiv
import pymongo
from config import config
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import concurrent.futures
import time

from pdf_comprese import compress_pdf
from pdf_check import  check_pdf_integrity
import os
import requests
import sys
session = requests.session()
session.headers ={
        "referer": "https://www.baidu.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
}
myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
save_path = config.save_path
count=1926856
pool_num=61
def download_pdf(arxiv_data):
    # arxiv_data=db_data.find_one({"downloaded":{'$exists':False}})
    # random_index = random.randint(0, count - 1)
    if arxiv_data:
        entey = arxiv_data['entry_id'].split('/')[-1]
        date=entey.split('.')[0]
        entey_id=entey.split('.')[1]
        if not os.path.exists(save_path+date):
            os.makedirs(save_path+date)
        pdf_path = save_path+date+'/'+entey+'.pdf'
        pdf_path_temp = save_path+date+'/'+entey+'_temp.pdf'
        pdf_url = arxiv_data['pdf_url']#.replace("http://arxiv.org/","http://xxx.itp.ac.cn/")
        try:
            response = session.get(pdf_url)
        except:
            traceback.print_exc()
            return
        # if  os.path.exists(pdf_path):
        #     return
        try:
            if len(response.content)<10000 and "arXiv reCAPTCHA" in response.text:
                print("reCAPTCHA")
                sys.exit(0)
            if response.status_code == 404:
                if 'v' in pdf_url.split('.')[-1] and int(pdf_url.split('.')[-1].split('v')[-1])>1:
                    url_no_v=pdf_url[:pdf_url.rfind('v')]
                    version=int(pdf_url.split('.')[-1].split('v')[-1])
                    pdf_url=f'{url_no_v}v{version-1}'
                    entey_id=f"{arxiv_data['entry_id'][:arxiv_data['entry_id'].rfind('v')]}v{version-1}"
                    db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"pdf_url":pdf_url,"entry_id":entey_id}})
                    try:
                        response = session.get(pdf_url)
                    except:
                        traceback.print_exc()
                        return
                else:
                    db_data.update_one({"entry_id": arxiv_data['entry_id']}, {"$set": {"arxiv_pdf_error": True}})
                    return
            if response.status_code != 200:
                print(pdf_url,"status_code:",response.status_code)
                if response.status_code == 403:
                    sys.exit(0)
                if response.status_code // 100 == 5:
                    db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"arxiv_pdf_error":True}})
                time.sleep(4)
                return
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            try:
                compress_pdf(pdf_path, pdf_path_temp)
            except:
                traceback.print_exc()
            if check_pdf_integrity(pdf_path_temp):
                os.remove(pdf_path)
                os.rename(pdf_path_temp,pdf_path)
            else:
                os.remove(pdf_path_temp)
            if check_pdf_integrity(pdf_path):
                db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"downloaded":True}})
            else:
                os.remove(pdf_path)
        except Exception as e:
            print(e)
            # db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"downloaded":False}})
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(pdf_path_temp):
                os.remove(pdf_path_temp)
def process_chunk(chunk_and_threads):
    chunk, num_threads = chunk_and_threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as thread_pool:
        return list(thread_pool.map(download_pdf, chunk))

def process_with_pools(data, num_processes, num_threads):
    # 创建进程池
    with multiprocessing.Pool(processes=num_processes) as process_pool:
        # 将数据分割成块，每个进程处理一块
        chunk_size = len(data) // num_processes
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # 为每个chunk添加线程数
        chunks_with_threads = [(chunk, num_threads) for chunk in chunks]
        
        # 使用进程池处理每个块
        results = process_pool.map(process_chunk, chunks_with_threads)
    
    # 展平结果列表
    return [item for sublist in results for item in sublist]

if __name__ == "__main__": 
    # for arxiv_data in db_data.find({"downloaded": False,"primary_category":{"$regex": "^cs"}}):
    #     download_pdf(arxiv_data)
    # 示例数据
    # data = list(range(100))
    
    # 指定进程数和每个进程的线程数
    num_processes = 1
    num_threads = 10
    process_with_pools([i for i in db_data.find({"downloaded": False,"primary_category":{"$regex": "^cs"},"arxiv_pdf_error":False})], num_processes, num_threads)



    # pool = Pool(pool_num)
    # pool.map_async(download_pdf,db_data.find({"downloaded": False,"primary_category":{"$regex": "^cs"}}))
    # pool.close()
    # pool.join()
    # with ThreadPoolExecutor(max_workers=pool_num) as executor:
    #     executor.map(download_pdf,db_data.find({"downloaded": False,"primary_category":{"$regex": "^cs"}}))