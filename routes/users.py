from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from http import HTTPStatus

from utils.auth_helpers import get_current_user, require_group_member

users_bp = Blueprint('users', __name__)

@users_bp.route('/getUsers', methods=['GET'])
@jwt_required()
def get_users():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        scope_param = request.args.get('scope')
        group_id_param = request.args.get('groupId')

        scope_type = 'personal'
        group_id = None

        if scope_param == 'group' and group_id_param:
            scope_type = 'group'
            group_id = int(group_id_param)
            require_group_member(database, group_id, user)

        users = database.get_users(user.id, scope_type, group_id)
        return jsonify([{"id": u.id, "username": u.username, "forename": u.forename} for u in users])
    except Exception as e:
        print(e)
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify(str(e)), HTTPStatus.INTERNAL_SERVER_ERROR
