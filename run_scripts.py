import subprocess

# 要运行的Python文件列表
python_files = [
    "spider.py",
    "pdf_download.py",
    "connect_extract.py",
    "title_refered.py"
]

# 依次运行每个Python文件
for file in python_files:
    print(f"正在运行 {file}...")
    try:
        # 使用subprocess运行Python文件
        subprocess.run([r"C:\ProgramData\anaconda3\envs\arxiv_analysise\python.exe", file], check=True)
        print(f"{file} 运行完成")
    except subprocess.CalledProcessError as e:
        print(f"运行 {file} 时出错: {e}")
    except FileNotFoundError:
        print(f"找不到文件 {file}")
    print("-" * 30)  # 分隔线

print("所有脚本运行完毕")
