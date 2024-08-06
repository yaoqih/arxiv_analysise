import os
import PyPDF2
from config import config
import  pymongo
from multiprocessing import Pool

save_path = config.save_path
myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
pool_num=61
def check_pdf_integrity(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            if num_pages == 0:
                # print(f"PDF文件 '{file_path}' 是空白的（没有页面）.")
                return False

            # # 检查是否所有页面都是空白的
            # all_pages_blank = True
            # for page in pdf_reader.pages:
            #     text = page.extract_text().strip()
            #     if text:
            #         all_pages_blank = False
            #         break

            # if all_pages_blank:
            #     # print(f"PDF文件 '{file_path}' 可能是空白的（所有页面都没有文本）.")
            #     return False

            # print(f"PDF文件 '{file_path}' 完整且包含内容.")
            # print(f"总页数: {num_pages}")
            return True
    except PyPDF2.errors.PdfReadError as e:
        # print(f"PDF文件 '{file_path}' 不完整或已损坏.")
        # print(f"错误信息: {str(e)}")
        return False
    except Exception as e:
        # print(f"检查PDF文件时发生错误: {str(e)}")
        return False
def chenck_path(date):
    for file in os.listdir(save_path+date+"/"):
        if not check_pdf_integrity(save_path+date+"/"+file) or "temp" in file:
            res=db_data.update_one({"entry_id":"http://arxiv.org/abs/"+file[:-4]},{"$set":{"downloaded":False}})
            if res.acknowledged:
                os.remove(save_path+date+"/"+file)
if __name__=="__main__":
    # for date in os.listdir(save_path):
    #     for file in os.listdir(save_path+date+"/"):
    #         if not check_pdf_integrity(save_path+date+"/"+file) or "temp" in file:
    #             res=db_data.update_one({"entry_id":"http://arxiv.org/abs/"+file[:-4]},{"$set":{"downloaded":False}})
    #             if res.acknowledged:
    #                 os.remove(save_path+date+"/"+file)
    pool = Pool(pool_num)
    pool.map_async(chenck_path,os.listdir(save_path))
    pool.close()
    pool.join()