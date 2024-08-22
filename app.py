from flask import Flask, render_template, request, jsonify,send_from_directory
from flask_compress import Compress
import os
from query import find_neighbors,collection,find_neighbors_aggregation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address #以ip地址作为流量控制条件
from flask import make_response
import re

app = Flask(__name__)
Compress(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000/day"],
)
def extract_arxiv(text):
    pattern = r'(?:\d{4}\.\d{4,5})(?:v\d+)?'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')#设置icon
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),#对于当前文件所在路径,比如这里是static下的favicon.ico
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/search', methods=['POST'])
@limiter.limit("25/minute")
def search():
    query = extract_arxiv(request.form['query'])
    if not query:
        return make_response("未找到节点"),404
    query=collection.find_one({"entry_id":{"$regex":query.split('/')[-1].split('v')[0]}})
    if query:
        data=find_neighbors(query['entry_id'])
        if not data:
            return make_response("超级节点"),408	
    else:
        return make_response("未找到节点"),404
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=False, port=2333,host='0.0.0.0')
