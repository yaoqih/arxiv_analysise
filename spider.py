import arxiv
import pymongo
from config import config
from multiprocessing import Pool

myclient = pymongo.MongoClient(config.mongo_client_url)
mydb = myclient["paper_connect"]
db_data = mydb["data"]
process_record = mydb["process_record"]
# from requests.adapters import HTTPAdapter
# proxies = {
#     'http': f'{config.clash_address}:{config.clash_port}',
#     'https': f'{config.clash_address.replace("http","https")}:{config.clash_port}'
# }
# s = requests.Session()
# s.proxies = proxies
# s.verify = False
# s.mount('http://', HTTPAdapter(max_retries=3))
# s.mount('https://', HTTPAdapter(max_retries=3))

# Construct the default API client.
# client._session = s
client = arxiv.Client()
def generate_nested_list(start=0,end=100000,step=500):
    outer_list = []
    for i in range(start, end, step):
        inner_list = list(range(i + 1, i + step+1))
        outer_list.append(inner_list)
    return outer_list
def number_format(num,size=5):
    num_str = str(num)
    return "0"*(size-len(num_str))+num_str
def papers_info(id_list):
    search_by_id = arxiv.Search(id_list=id_list)
    success_num=0
    for paper_data in client.results(search_by_id):
        # print(paper_data,"paper_data")
        success_num+=1
        if db_data.find_one({"entry_id":paper_data.entry_id}):
            continue
        paper_data_dict=translate_dict(paper_data)
        db_data.update_one({"entry_id":paper_data_dict['entry_id']},{"$set":paper_data_dict},upsert=True)
    return success_num
def translate_dict(arixv_result):
    arixv_result.authors = [author.name for author in arixv_result.authors]
    arixv_result.links = [{"href":link.href,"rel":link.rel,"title":link.title} for link in arixv_result.links]
    arixv_result.date = arixv_result.published.strftime('%Y-%m-%d')
    return {
        "title":arixv_result.title,
        "authors":arixv_result.authors,
        "abstract":arixv_result.summary,
        "date":arixv_result.date,
        "links":arixv_result.links,
        "categories":arixv_result.categories,
        "pdf_url":arixv_result.pdf_url,
        "comment":arixv_result.comment,
        "doi":arixv_result.doi,
        "entry_id":arixv_result.entry_id,
        "journal_ref":arixv_result.journal_ref,
        "primary_category":arixv_result.primary_category,
        "published":arixv_result.published,
        "summary":arixv_result.summary,
        "updated":arixv_result.updated,
        "refer_ids":[],
        "project_url":"",
        "content":"",
        "meeting":"",
        "downloaded":False,
        "arxiv_pdf_error":False,
        "connect_extract":False,
    }
def get_paper_infos(year,month):
    if start_number:=process_record.find_one({"year":year,"month":month}):
        number_list_genrate=generate_nested_list(start=start_number["number"])
    else:
        number_list_genrate=generate_nested_list()
    for number_list in number_list_genrate:
        success_num=papers_info([f'{year}{month}.{number_format(number)}' for number in number_list])
        print(f'{year}{month}.{number_list[0]}-{year}{month}.{number_list[-1]}',success_num)
        if success_num<100:
            process_record.update_one({"year":year,"month":month},{"$set":{"number":number_list[0]-500 if number_list[0]>500 else 0}},upsert=True)
            print(f'{year}{month}.{number_list[0]}-{year}{month}.{number_list[-1]}',"break")
            open("log.txt","a").write(f'{year}{month}.{number_list[0]}-{year}{month}.{number_list[-1]}\n')
            break
if __name__ =="__main__":
    # get_paper_infos('08','01')
    for year in range(24,25):
        p=Pool(6)
        p.starmap(get_paper_infos,[[number_format(year,2),number_format(i,2)] for i in range(7,8)])
        p.close()
        p.join()