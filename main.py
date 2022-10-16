from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/currentWeekData', methods = ['GET'])
def currentWeekData():
    return jsonify([
        [
            {
                'Date': '20221003',
                'Kate': 3,
                'Will': 4
            },
            {
                'Date': '20221004',
                'Kate': 3,
                'Will': 2
            },
            {
                'Date': '20221005',
                'Kate': 2,
                'Will': 4
            },
            {
                'Date': '20221006',
                'Kate': 5,
                'Will': 4
            },
            {
                'Date': '20221007',
                'Kate': 4,
                'Will': 4
            },
           {
                'Date': '20221008',
                'Kate': 3,
                'Will': 3
            },
            {
                'Date': '20221009',
                'Kate': 4,
                'Will': 3
            }
        ],
        [
            {
                'Date': '20221010',
                'Kate': 5,
                'Will': 4
            },
            {
                'Date': '20221011',
                'Kate': 3,
                'Will': 3
            },
            {
                'Date': '20221012',
                'Kate': 2,
                'Will': 3
            },
            {
                'Date': '20221013',
                'Kate': 4,
                'Will': 4
            },
            {
                'Date': '20221014',
                'Kate': 4,
                'Will': 3
            },
            {
                'Date': '20221015',
                'Kate': None,
                'Will': None
            },
            {
                'Date': '20221016',
                'Kate': None,
                'Will': None
            }
        ]
    ])

if __name__ == '__main__':
    app.run()