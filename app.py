from flask import Flask, render_template, request, jsonify,send_from_directory
from flask_compress import Compress
import os
from query import find_neighbors,collection
app = Flask(__name__)
Compress(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')#设置icon
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),#对于当前文件所在路径,比如这里是static下的favicon.ico
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    query=collection.find_one({"entry_id":{"$regex":query.split('/')[-1].split('v')[0]}})
    if query:
        data=find_neighbors(query['entry_id'])
    else:
        data={}
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=2333,host='0.0.0.0')
