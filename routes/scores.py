from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from http import HTTPStatus

from utils.auth_helpers import get_current_user, require_group_member

scores_bp = Blueprint('scores', __name__)

@scores_bp.route('/scores', methods=['GET'])
@jwt_required()
def get_scores():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        
        timezone = request.args.get('timezone')
        if timezone:
            database.set_timezone(timezone)

        scope_type = request.args.get('scope', 'personal')
        group_id = request.args.get('groupId')
        
        if group_id:
            group_id = int(group_id)

        if scope_type == 'group':
            if not group_id:
                return jsonify({'error': 'Group ID required for group scope'}), 400
            require_group_member(database, group_id, user)

        all_weeks = database.get_scores(user.id, scope_type, group_id)
        return jsonify(all_weeks)
    except Exception as e:
        print(e)
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify(str(e)), HTTPStatus.INTERNAL_SERVER_ERROR

@scores_bp.route('/scores', methods=['POST'])
@jwt_required()
def add_score():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        data = request.json
        database.set_timezone(data['timezone'])

        score = data.get('score')
        if score is None:
            database.delete_score(data['date'], user.id)
        else:
            database.add_score(data['date'], user.id, score)

        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        print(e)
        return jsonify(str(e)), HTTPStatus.INTERNAL_SERVER_ERROR
