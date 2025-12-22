import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token

from config.limiter import limiter
from utils.serializers import serialise_user
from utils.error_handler import handle_success_error_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    database = current_app.config['database']
    data = request.json
    username = data['username']
    password = data['password']
    try:
        user = database.login(username, password)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_user(user)})
    except Exception as e:
        response, status_code = handle_success_error_response(e)
        # Add access_token and user fields for consistency with success response
        response_data = response.get_json()
        response_data['access_token'] = None
        response_data['user'] = None
        return jsonify(response_data), status_code

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    database = current_app.config['database']
    data = request.json
    username = data.get('username')
    password = data.get('password')
    forename = data.get('forename')

    if not username or not password or not forename:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    if len(username) > 12:
        return jsonify({'success': False, 'error': 'Username must be 12 characters or less'}), 400
        
    if len(forename) > 10:
        return jsonify({'success': False, 'error': 'Display name must be 10 characters or less'}), 400

    if len(password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400

    try:
        user = database.register_user(username, password, forename)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_user(user)})
    except Exception as e:
        return handle_success_error_response(e)
