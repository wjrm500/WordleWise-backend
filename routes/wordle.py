import datetime
import base64
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import requests
from bs4 import BeautifulSoup

from utils.error_handler import handle_success_error_response

wordle_bp = Blueprint('wordle', __name__)

@wordle_bp.route('/wordle/answer', methods=['GET'])
@jwt_required()
def get_wordle_answer():
    try:
        date_str = request.args.get('date')
        if not date_str:
             return jsonify({'success': False, 'error': 'Date parameter is required'}), 400
             
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        formatted_date = f"{date_obj.day:02d}-{date_obj.month:02d}-{str(date_obj.year)[2:]}"
        url = f"https://www.rockpapershotgun.com/wordle-hint-and-answer-today-{formatted_date}"

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        answer_section = soup.find('h2', string=lambda s: s and 'What is today\'s Wordle answer' in s)
        if not answer_section:
            raise Exception("Could not find answer section")

        paragraphs = answer_section.find_next_siblings('p')
        for p in paragraphs:
            strong_tag = p.find('strong')
            if strong_tag:
                answer = strong_tag.text.strip().lower().replace('.', '')
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
        return handle_success_error_response(e, success_key=False)
