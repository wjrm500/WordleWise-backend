import datetime
import html
import json
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from flask import abort
from http import HTTPStatus
import os
from dotenv import load_dotenv

load_dotenv()
import requests
from bs4 import BeautifulSoup
import base64

from database.Database import Database
from database.models.User import User

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
JWTManager(app)
CORS(app)

database = Database(database_url='sqlite:///wordlewise.db')

def serialise_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'forename': user.forename,
        'default_group_id': user.default_group_id
    }

serialise_model = lambda model: {col.name: getattr(model, col.name) for col in model.__table__.columns}

@app.before_request
def before_request_func():
    time.sleep(0)

@app.teardown_appcontext
def shutdown_session(exception=None):
    database.session.remove()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    try:
        user = database.login(username, password)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_user(user)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'access_token': None, 'user': None})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    forename = data.get('forename')
    
    if not username or not password or not forename:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
    try:
        user = database.register_user(username, password, forename)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({'success': True, 'error': None, 'access_token': access_token, 'user': serialise_user(user)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/getScores', methods=['POST'])
@jwt_required()
def get_scores():
    try:
        user = get_current_user()
        data = request.json
        database.set_timezone(data['timezone'])
        
        scope = data.get('scope')
        scope_type = 'personal'
        group_id = None
        
        if isinstance(scope, dict):
            scope_type = scope.get('type', 'personal')
            group_id = scope.get('groupId')
        elif scope == 'personal':
            scope_type = 'personal'
            
        if scope_type == 'group':
            if not group_id:
                return jsonify({'error': 'Group ID required for group scope'}), 400
            require_group_member(group_id, user)
            
        all_weeks = database.get_scores(user.id, scope_type, group_id)
        return jsonify(all_weeks)
    except Exception as e:
        print(e)
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/addScore', methods=['POST'])
@jwt_required()
def add_score():
    try:
        user = get_current_user()
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
        return jsonify(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route('/getUsers', methods=['GET'])
@jwt_required()
def get_users():
    try:
        user = get_current_user()
        scope_param = request.args.get('scope')
        group_id_param = request.args.get('groupId')
        
        scope_type = 'personal'
        group_id = None
        
        if scope_param == 'group' and group_id_param:
            scope_type = 'group'
            group_id = int(group_id_param)
            require_group_member(group_id, user)
            
        users = database.get_users(user.id, scope_type, group_id)
        return jsonify([{"id": u.id, "username": u.username, "forename": u.forename} for u in users])
    except Exception as e:
        print(e)
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
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
        date_str = request.json['date']
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
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_current_user():
    username = get_jwt_identity()
    user = database.session.query(User).filter_by(username=username).first()
    if not user:
        abort(401, 'User not found')
    return user

def require_group_member(group_id, user):
    membership = database.get_membership(group_id, user.id)
    if not membership:
        abort(403, "You are not a member of this group")
    return membership

def require_group_admin(group_id, user):
    membership = require_group_member(group_id, user)
    if membership.role != 'admin':
        abort(403, "Admin access required")
    return membership

@app.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    try:
        user = get_current_user()
        groups = database.get_user_groups(user.id)
        
        result = []
        for group in groups:
            membership = database.get_membership(group.id, user.id)
            member_count = len(group.members)
            result.append({
                "id": group.id,
                "name": group.name,
                "member_count": member_count,
                "role": membership.role,
                "include_historical_data": bool(group.include_historical_data),
                "is_default": user.default_group_id == group.id
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    try:
        user = get_current_user()
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Group name is required'}), 400
            
        include_historical = data.get('include_historical_data', True)
        
        group = database.create_group(name, user.id, include_historical)
        
        return jsonify({
            "success": True,
            "group": {
                "id": group.id,
                "name": group.name,
                "invite_code": group.invite_code,
                "include_historical_data": bool(group.include_historical_data),
                "created_at": group.created_at.isoformat(),
                "members": [{
                    "id": user.id,
                    "username": user.username,
                    "forename": user.forename,
                    "role": "admin"
                }]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_details(group_id):
    try:
        user = get_current_user()
        membership = require_group_member(group_id, user)
        
        group = database.get_group(group_id)
        members = []
        for m in group.members:
            members.append({
                "id": m.user.id,
                "username": m.user.username,
                "forename": m.user.forename,
                "role": m.role,
                "joined_at": m.joined_at.isoformat()
            })
            
        return jsonify({
            "id": group.id,
            "name": group.name,
            "invite_code": group.invite_code,
            "include_historical_data": bool(group.include_historical_data),
            "created_at": group.created_at.isoformat(),
            "members": members,
            "current_user_role": membership.role
        })
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    try:
        user = get_current_user()
        require_group_admin(group_id, user)
        
        data = request.json
        updates = {}
        if 'name' in data:
            updates['name'] = data['name']
        if 'include_historical_data' in data:
            updates['include_historical_data'] = 1 if data['include_historical_data'] else 0
            
        if updates:
            database.update_group(group_id, **updates)
            
        return jsonify({"success": True})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    try:
        user = get_current_user()
        require_group_admin(group_id, user)
        
        database.delete_group(group_id)
        
        return jsonify({"success": True})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/groups/join', methods=['POST'])
@jwt_required()
def join_group():
    try:
        user = get_current_user()
        invite_code = request.json.get('invite_code', '').strip().upper()
        
        group = database.get_group_by_invite_code(invite_code)
        if not group:
            return jsonify({"success": False, "error": "Invalid invite code"}), 400
            
        existing = database.get_membership(group.id, user.id)
        if existing:
            return jsonify({"success": False, "error": "You're already a member of this group"}), 400
            
        success, message = database.join_group(group.id, user.id)
        if not success:
            return jsonify({"success": False, "error": message}), 400
            
        return jsonify({
            "success": True,
            "group": {
                "id": group.id,
                "name": group.name
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    try:
        user = get_current_user()
        success, message = database.leave_group(group_id, user.id)
        
        if not success:
            return jsonify({"success": False, "error": message}), 400
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(group_id, member_id):
    try:
        user = get_current_user()
        require_group_admin(group_id, user)
        
        if user.id == member_id:
            return jsonify({"success": False, "error": "Cannot remove yourself. Use 'Leave Group' instead."}), 400
            
        target_membership = database.get_membership(group_id, member_id)
        if target_membership and target_membership.role == 'admin':
             return jsonify({"success": False, "error": "Cannot remove admin. Demote first."}), 400
             
        database.remove_member(group_id, member_id)
        return jsonify({"success": True})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>/members/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_member_role(group_id, member_id):
    try:
        user = get_current_user()
        require_group_admin(group_id, user)
        
        if user.id == member_id:
             return jsonify({"success": False, "error": "Cannot change your own role."}), 400
             
        role = request.json.get('role')
        if role not in ['admin', 'member']:
            return jsonify({"success": False, "error": "Invalid role"}), 400
            
        if role == 'member':
            target_membership = database.get_membership(group_id, member_id)
            if target_membership.role == 'admin':
                admins = [m for m in database.get_group(group_id).members if m.role == 'admin']
                if len(admins) <= 1:
                     return jsonify({"success": False, "error": "Cannot demote last admin."}), 400

        database.update_member_role(group_id, member_id, role)
        return jsonify({"success": True})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/groups/<int:group_id>/regenerate-code', methods=['POST'])
@jwt_required()
def regenerate_invite_code(group_id):
    try:
        user = get_current_user()
        require_group_admin(group_id, user)
        
        new_code = database.regenerate_invite_code(group_id)
        return jsonify({"success": True, "invite_code": new_code})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@app.route('/user/default-scope', methods=['PUT'])
@jwt_required()
def set_default_scope():
    try:
        user = get_current_user()
        data = request.json
        scope_type = data.get('type', 'personal')
        
        if scope_type == 'personal':
            success = database.set_default_scope(user.id, None)
        elif scope_type == 'group':
            group_id = data.get('groupId')
            if not group_id:
                return jsonify({"success": False, "error": "Group ID required"}), 400
            membership = database.get_membership(group_id, user.id)
            if not membership:
                return jsonify({"success": False, "error": "You are not a member of this group"}), 403
            success = database.set_default_scope(user.id, group_id)
        else:
            return jsonify({"success": False, "error": "Invalid scope type"}), 400
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to update default scope"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/default-scope', methods=['GET'])
@jwt_required()
def get_default_scope():
    try:
        user = get_current_user()
        if user.default_group_id:
            return jsonify({
                "type": "group",
                "groupId": user.default_group_id
            })
        else:
            return jsonify({
                "type": "personal",
                "groupId": None
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
