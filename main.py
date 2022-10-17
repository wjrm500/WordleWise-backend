import datetime
import json
import os
from flask import Flask, jsonify
from flask_cors import CORS

from database.models import db
from database.models.Score import Score

DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = f'{DIR}/database'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_DIR}/wordle.db'
CORS(app)
db.init_app(app)

@app.route('/getTestData', methods = ['GET'])
def get_test_data():
    text = open('test_data.json', 'r')
    return json.loads(text.read())

@app.route('/getData', methods = ['GET'])
def get_data():
    all_scores = []
    for score in Score.query.all():
        all_scores.append({
            "Date": score.date,
            "Kate": score.kate_score,
            "Will": score.will_score
        })
    all_scores = sorted(all_scores, key = lambda x: x['Date'])
    all_scores_dict = {str(x['Date']): x for x in all_scores}
    earliest_date = all_scores[0]['Date']
    earliest_date_weekday = earliest_date.weekday()
    start_date = earliest_date - datetime.timedelta(days = earliest_date_weekday)
    all_weeks = []
    while start_date <= datetime.date.today():
        single_week = []
        for _ in range(7):
            str_start_date = str(start_date)
            if str_start_date in all_scores_dict:
                data = all_scores_dict[str_start_date]
                kate_score = data['Kate']
                will_score = data['Will']
            else:
                future = start_date > datetime.date.today()
                kate_score = will_score = None if future else 8
            single_week.append({
                'Date': str_start_date,
                'Kate': kate_score,
                'Will': will_score
            })
            start_date = start_date + datetime.timedelta(days = 1)
        all_weeks.append(single_week)
    return jsonify(all_weeks)

if __name__ == '__main__':
    app.run()