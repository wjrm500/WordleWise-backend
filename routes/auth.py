import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token

from utils.serializers import serialise_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
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
        return jsonify({'success': False, 'error': str(e), 'access_token': None, 'user': None})

@auth_bp.route('/register', methods=['POST'])
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

    try:
        user = database.register_user(username, password, forename)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_user(user)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
