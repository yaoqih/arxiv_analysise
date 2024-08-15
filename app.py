from flask import Flask, render_template, request, jsonify
from query import find_neighbors,collection
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
