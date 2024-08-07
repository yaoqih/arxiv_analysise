from flask import Flask, render_template, request, jsonify
import requests
from query import find_neighbors,collection
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    query=collection.find_one({"entry_id":{"$regex":query.split('/')[-1].split('v')[0]}})['entry_id']
    data=find_neighbors(query)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000,host='0.0.0.0')
