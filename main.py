from http import HTTPStatus
from flask import Flask, jsonify, request
from flask_cors import CORS
from database.Database import Database
from database.aws.download_database import download_database
from database.aws.upload_database import upload_database

app = Flask(__name__)
CORS(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    try:
        database.login(username, password)
        return jsonify({'success': True, 'error': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/getData', methods = ['GET'])
def get_data():
    try:
        all_weeks = database.get_data()
        return jsonify(all_weeks)
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/addScore', methods = ['POST'])
def add_score():
    try:
        data = request.json
        database.add_score(data)
        upload_database()
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

download_database()
global database
database = Database(database_url = 'sqlite:///wordle.db')
if __name__ == '__main__':
    app.run()