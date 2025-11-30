from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from http import HTTPStatus

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/executeSql', methods=['POST'])
@jwt_required()
def execute_sql():
    database = current_app.config['database']
    try:
        database.execute(request.json['sql'])
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)
