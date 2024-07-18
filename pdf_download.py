import arxiv
import pymongo
from config import config
from multiprocessing import Pool
from pdf_comprese import compress_pdf
import os
import requests
import sys
myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
save_path = config.save_path
count=1926856
pool_num=61
headers = {
        "referer": "https://www.baidu.com.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }
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
        pdf_url = arxiv_data['pdf_url']
        response = requests.get(pdf_url,headers=headers)
        if  os.path.exists(pdf_path):
            return
        try:
            if "arXiv reCAPTCHA" in response.text:
                print("reCAPTCHA")
                sys.exit(0)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            compress_pdf(pdf_path, pdf_path_temp)
            os.remove(pdf_path)
            os.rename(pdf_path_temp,pdf_path)
            db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"downloaded":True}})
        except Exception as e:
            print(e)
            # db_data.update_one({"entry_id":arxiv_data['entry_id']},{"$set":{"downloaded":False}})
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(pdf_path_temp):
                os.remove(pdf_path_temp)
if __name__ == "__main__": 
    for arxiv_data in db_data.find({"downloaded": False}):
        download_pdf(arxiv_data)
    pool = Pool(pool_num)
    pool.map(download_pdf,db_data.find({"downloaded": False}))
    pool.close()
    pool.join()
    # download_pdf()