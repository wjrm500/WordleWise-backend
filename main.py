import datetime
import html
import json
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
        
        return jsonify({
            'success': False,
            'error': 'Could not find answer on the page. The format may have changed.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin/set-title', methods=['GET', 'POST'])
def set_title_page():
    if request.method == 'POST':
        password = request.form.get('password')
        title = request.form.get('title', '').strip()
        expiry_str = request.form.get('expiry')
        
        try:
            user = database.login('wjrm500', password)
            if not user.admin:
                return '<h1>Unauthorised</h1><a href="/admin/set-title">Back</a>'
        except:
            return '<h1>Wrong password</h1><a href="/admin/set-title">Back</a>'
        
        if not title:
            return '<h1>Title cannot be empty</h1><a href="/admin/set-title">Back</a>'
        
        # Escape any HTML to prevent XSS
        title = html.escape(title)
        
        # Parse expiry datetime
        try:
            expiry = datetime.datetime.fromisoformat(expiry_str)
        except:
            return '<h1>Invalid expiry date</h1><a href="/admin/set-title">Back</a>'
        
        with open('custom_title.json', 'w') as f:
            json.dump({'title': title, 'expiry': expiry.isoformat()}, f)
        
        expiry_display = expiry.strftime('%Y-%m-%d %H:%M:%S')
        return f'''
            <h1>Done!</h1>
            <p>Title: {title}</p>
            <p>Expires: {expiry_display}</p>
        '''
    
    # Default expiry: today at 23:59:59
    default_expiry = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    default_expiry_str = default_expiry.strftime('%Y-%m-%dT%H:%M')
    
    return f'''
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Set Title</title></head>
    <body>
    <h1>Set custom page title</h1>
    <form method="POST">
    <label>Password for wjrm500:</label><br>
    <input type="password" name="password" placeholder="Password" required autocomplete="current-password"><br><br>
    <label>New page title:</label><br>
    <input type="text" name="title" placeholder="Title" required><br><br>
    <label>Expires:</label><br>
    <input type="datetime-local" name="expiry" value="{default_expiry_str}" required><br><br>
    <button type="submit">Update</button>
    </form>
    </body>
    </html>
    '''

@app.route('/getTitle', methods=['GET'])
def get_title():
    try:
        with open('custom_title.json', 'r') as f:
            data = json.load(f)
        expiry = datetime.datetime.fromisoformat(data['expiry'])
        if expiry > datetime.datetime.now():
            return jsonify({'title': data['title']})
    except:
        pass
    return jsonify({'title': 'Welcome to WordleWise'})

database = Database(database_url='sqlite:///wordlewise.db')

if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
