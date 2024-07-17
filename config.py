import sys
import math


class Config:
    mongo_client_username = 'huyaoqi'
    mongo_client_password = 'hwt439876.'
    if 'win' in sys.platform:
        mongo_client_host = 'huyaoqi.tpddns.cn:27017'
        # mongo_client_host = '124.70.80.182:27017'
    else:
        mongo_client_host = '124.70.80.182:27017'
    mongo_client_url = f'mongodb://{mongo_client_username}:{mongo_client_password}@{mongo_client_host}/'
    # mongo_client_url=f'mongodb://127.0.0.1:27017/'
    ajax_origin_url = '127.0.0.1:5173'
    openai_key = 'sk-T4p4PNbNOBuVBxXpwt2Hr67YtPbMVH0xCFDDZ5ieDSbtfr7i'
    clash_port = 8466
    clash_address='http://127.0.0.1'
    pdf_save_path = './pdf_download/'
    result_save_path = './result/'
    # result_img_path = 'http://127.0.0.1:83/C%3A/Users/13756/OneDrive%20-%20integrate%20collaborative%20models/%E6%96%87%E6%A1%A3/paper_daily_format/paper_daily_back_flask/result/'
    # result_img_path = 'http://127.0.0.1:83/C%3A/Users/13756/Documents/GitHub/paper_daily_format/paper_daily_back_flask/result/'
    result_img_path = 'http://huyaoqi.tpddns.cn:83/C%3A/Users/13756/Documents/GitHub/paper_daily_format/paper_daily_back_flask/result/'
config = Config()