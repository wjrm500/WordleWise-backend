import datetime
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from http import HTTPStatus
import os
import requests
from bs4 import BeautifulSoup
import base64

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
    
@app.route('/getWordleAnswer', methods=['POST'])
@jwt_required()
def get_wordle_answer():
    try:
        date_str = request.json['date']  # Format: YYYY-MM-DD
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Format date for rockpapershotgun URL
        formatted_date = f"{date_obj.day:02d}-{date_obj.month:02d}-{str(date_obj.year)[2:]}"
        url = f"https://www.rockpapershotgun.com/wordle-hint-and-answer-today-{formatted_date}"
        
        # Check if feature is disabled
        try:
            with open('wordle_answer_findable.txt', 'r') as f:
                if f.read().strip().lower() == 'false':
                    return jsonify({
                        'success': False,
                        'error': 'Feature is currently disabled due to source format changes'
                    })
        except FileNotFoundError:
            # If file doesn't exist, create it with default 'true'
            with open('wordle_answer_findable.txt', 'w') as f:
                f.write('true')
        
        # Fetch the page content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the answer section
        answer_section = soup.find('h2', string=lambda s: s and 'What is today\'s Wordle answer' in s)
        if not answer_section:
            raise Exception("Could not find answer section")
        
        # Look for the answer in a <strong> tag within paragraphs after the h2
        paragraphs = answer_section.find_next_siblings('p')
        for p in paragraphs:
            strong_tag = p.find('strong')
            if strong_tag:
                answer = strong_tag.text.strip().lower().replace('.', '')
                # Generate the playable URL
                encoded_word = base64.b64encode(answer.encode()).decode()
                playable_url = f"https://www.thewordfinder.com/wordle-maker/?game={encoded_word}"
                
                return jsonify({
                    'success': True,
                    'answer': answer,
                    'playable_url': playable_url
                })
        
        # If we got here, the format has likely changed
        with open('wordle_answer_findable.txt', 'w') as f:
            f.write('false')
            
        return jsonify({
            'success': False,
            'error': 'Could not find answer on the page. The format may have changed.'
        })
        
    except Exception as e:
        # If there's any error, disable the feature for future requests
        try:
            with open('wordle_answer_findable.txt', 'w') as f:
                f.write('false')
        except:
            pass
            
        return jsonify({
            'success': False,
            'error': str(e)
        })

database = Database(database_url='sqlite:///wordlewise.db')

if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
