import datetime
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from http import HTTPStatus
import os

from database.Database import Database

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
JWTManager(app)
CORS(app)

serialise_model = lambda model: {col.name: getattr(model, col.name) for col in model.__table__.columns}

@app.before_request
def before_request_func():
    time.sleep(0)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    try:
        user = database.login(username, password)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_model(user)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'access_token': None, 'user': None})

@app.route('/getScores', methods=['POST'])
@jwt_required()
def get_scores():
    try:
        database.set_timezone(request.json['timezone'])
        all_weeks = database.get_scores()
        return jsonify(all_weeks)
    except Exception as e:
        print(e)
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/addScore', methods=['POST'])
@jwt_required()
def add_score():
    try:
        data = request.json
        database.set_timezone(data['timezone'])
        database.add_score(data['date'], data['user_id'], data['score'])
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        print(e)
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/getUsers', methods=['GET'])
@jwt_required()
def get_users():
    try:
        users = database.get_users()
        return jsonify([{"id": user.id, "username": user.username} for user in users])
    except Exception as e:
        print(e)
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/executeSql', methods=['POST'])
@jwt_required()
def execute_sql():
    try:
        database.execute(request.json['sql'])
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

database = Database(database_url='sqlite:///wordlewise.db')

if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
