import datetime
import hashlib
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from database.models import db
from database.models.Day import Day
from database.models.User import User

DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = f'{DIR}/database'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_DIR}/wordle.db'
CORS(app)
db.init_app(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    provided_username = data['username']
    provided_password = data['password']
    user = db.session.query(User).filter_by(username = provided_username).first()
    if user is not None:
        hash_to_match = user.password_hash
        if hashlib.md5(provided_password.encode()).hexdigest() == hash_to_match:
            return jsonify({'success': True, 'error': None})
        return jsonify({'success': False, 'error': 'Password incorrect'})
    return jsonify({'success': False, 'error': 'User does not exist'})

@app.route('/getData', methods = ['GET'])
def get_data():
    all_days = []
    for day in Day.query.all():
        all_days.append({
            "Date": day.date,
            "Kate": day.kate_score,
            "Will": day.will_score
        })
    all_days = sorted(all_days, key = lambda x: x['Date'])
    all_days_dict = {str(x['Date']): x for x in all_days}
    earliest_date = all_days[0]['Date']
    earliest_date_weekday = earliest_date.weekday()
    start_date = earliest_date - datetime.timedelta(days = earliest_date_weekday)
    all_weeks = []
    while start_date <= datetime.date.today():
        single_week = []
        for _ in range(7):
            str_start_date = str(start_date)
            if str_start_date in all_days_dict:
                data = all_days_dict[str_start_date]
                kate_score = data['Kate']
                will_score = data['Will']
            else:
                future = start_date >= datetime.date.today()
                kate_score = will_score = None if future else 8
            single_week.append({
                'Date': str_start_date,
                'Kate': kate_score,
                'Will': will_score
            })
            start_date = start_date + datetime.timedelta(days = 1)
        all_weeks.append(single_week)
    return jsonify(all_weeks)

@app.route('/addScore', methods = ['POST'])
def add_score():
    data = request.json
    print(data)
    day = db.session.query(Day).filter_by(date = data['date']).first()
    if day is not None:
        if data['user'] == 'Will':
            day.will_score = data['score']
        elif data['user'] == 'Kate':
            day.kate_score = data['score']
    else:
        if data['user'] == 'Will':
            day = Day(
                date = datetime.datetime.strptime(data['date'], "%Y-%m-%d"),
                will_score = data['score'],
                kate_score = None
            )
        elif data['user'] == 'Kate':
            day = Day(
                date = datetime.datetime.strptime(data['date'], "%Y-%m-%d"),
                will_score = None,
                kate_score = data['score']
            )
        db.session.add(day)
    db.session.commit()
    resp = jsonify('')
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp

if __name__ == '__main__':
    app.run()