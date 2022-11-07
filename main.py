from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from http import HTTPStatus
import os

from database.Database import Database
from database.aws.download_database import download_database
from database.aws.upload_database import upload_database

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
JWTManager(app)
CORS(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    try:
        database.login(username, password)
        access_token = create_access_token(identity = username)
        return jsonify({'success': True, 'error': None, 'access_token': access_token})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'access_token': None})

@app.route('/getData', methods = ['GET'])
@jwt_required()
def get_data():
    try:
        all_weeks = database.get_data()
        return jsonify(all_weeks)
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/addScore', methods = ['POST'])
@jwt_required()
def add_score():
    try:
        data = request.json
        database.add_score(data['date'], data['score'], data['user'])
        upload_database()
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

download_database()
global database
database_filename = os.environ.get('AWS_S3_OBJECT_NAME')
database = Database(database_url = f'sqlite:///{database_filename}')
if __name__ == '__main__':
    app.run()