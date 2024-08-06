import traceback
from tqdm import tqdm
import arxiv
import pymongo
from config import config
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import concurrent.futures
import time
import arxiv
from pdf_comprese import compress_pdf
from pdf_check import  check_pdf_integrity
import os
import requests
import sys
session = requests.session()
session.headers  = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "max-age=0",
    "Priority": "u=0, i",
    "Referer": "https://arxiv.org/abs/2310.00333v1",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWe8bKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
}

myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
save_path = config.save_path
count=1926856
pool_num=61
filter={"downloaded": False,"primary_category":{"$regex": "^cs"},"arxiv_pdf_error":False}
def download_pdf(arxiv_data):
    # arxiv_data=db_data.find_one({"downloaded":{'$exists':False}})
    # random_index = random.randint(0, count - 1)
    start=time.time()
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
                exit(0)
            if response.status_code == 404:
                if 'v' in pdf_url.split('.')[-1] and int(pdf_url.split('.')[-1].split('v')[-1])>1:
                    url_no_v=pdf_url[:pdf_url.rfind('v')]
                    version=int(pdf_url.split('.')[-1].split('v')[-1])
                    pdf_url=f'{url_no_v}v{version-1}'
                    entey_id=f"{arxiv_data['entry_id'][:arxiv_data['entry_id'].rfind('v')]}v{version-1}"
                    if db_data.find_one({"entry_id":entey_id}):
                        db_data.delete_one({"entry_id":entey_id})
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
                    exit(0)
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
    end=time.time()
    time.sleep(max(0,10-(end-start)))
def download_by_arxiv_api(data):
    id_list = [arxiv_data['entry_id'].split('/')[-1] for arxiv_data in data]
    for (paper_index,paper) in enumerate(arxiv.Client().results(arxiv.Search(id_list=id_list))):
        arxiv_data=data[paper_index]
        entey = arxiv_data['entry_id'].split('/')[-1]
        date=entey.split('.')[0]
        entey_id=entey.split('.')[1]
        if not os.path.exists(save_path+date):
            os.makedirs(save_path+date)
        pdf_path = save_path+date+'/'+entey+'.pdf'
        pdf_path_temp = save_path+date+'/'+entey+'_temp.pdf'
        pdf_url = arxiv_data['pdf_url']
        try:
            paper.download_pdf(dirpath=save_path+date,filename=entey+'.pdf')
        except Exception as e:
            if e.code==404:
                if 'v' in pdf_url.split('.')[-1] and int(pdf_url.split('.')[-1].split('v')[-1])>1:
                    url_no_v=pdf_url[:pdf_url.rfind('v')]
                    version=int(pdf_url.split('.')[-1].split('v')[-1])
                    pdf_url=f'{url_no_v}v{version-1}'
                    entey_id=f"{arxiv_data['entry_id'][:arxiv_data['entry_id'].rfind('v')]}v{version-1}"
                    if db_data.find_one({"entry_id":entey_id}):
                        db_data.delete_one({"entry_id":entey_id})
                    db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"pdf_url":pdf_url,"entry_id":entey_id}})
                else:
                    db_data.update_one({"entry_id": arxiv_data['entry_id']}, {"$set": {"arxiv_pdf_error": True}})
            else:
                print(e)
                exit(0)
            continue
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
def arxiv_task_split(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
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
    for arxiv_data in tqdm(db_data.find(filter)):
        download_pdf(arxiv_data)
    # 示例数据
    # data = list(range(100))
    
    # # 指定进程数和每个进程的线程数
    # num_processes = 1
    # num_threads = 3
    # process_with_pools([i for i in db_data.find(filter)], num_processes, num_threads)
    # chunk_task=arxiv_task_split([i for i in db_data.find(filter)],100)
    # for chunk in tqdm(chunk_task):
    #     download_by_arxiv_api(chunk)

    # pool = Pool(5)
    # pool.map_async(download_by_arxiv_api,chunk_task)
    # pool.close()
    # pool.join()
    # with ThreadPoolExecutor(max_workers=pool_num) as executor:
    #     executor.map(download_pdf,db_data.find({"downloaded": False,"primary_category":{"$regex": "^cs"}}))