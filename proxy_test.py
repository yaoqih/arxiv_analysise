import requests
address=requests.get("http://127.0.0.1:5555/random").text
# 代理服务器设置
proxies = {
    'http': address,
    'https': address,
}

# 目标URL
url = 'https://arxiv.org/pdf/2407.13420'

# 本地文件路径
local_filename = 'downloaded_file.pdf'

def download_file(url, local_filename, proxies):
    with requests.get(url, proxies=proxies, stream=True) as response:
        response.raise_for_status()  # 检查请求是否成功
        with open(local_filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # 分块下载
                file.write(chunk)
    print(f"File downloaded successfully as {local_filename}")

# 调用下载函数
download_file(url, local_filename, proxies)
