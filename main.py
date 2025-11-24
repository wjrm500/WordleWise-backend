import datetime
import html
import json
import time
from functools import wraps

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    JWTManager,
    get_jwt_identity
)
from http import HTTPStatus
import os
import requests
from bs4 import BeautifulSoup
import base64

from database.Database import Database

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
JWTManager(app)
CORS(app)

database = Database(database_url='sqlite:///wordlewise.db')

serialise_model = lambda model: {col.name: getattr(model, col.name) for col in model.__table__.columns}


# =============================================================================
# HELPERS & DECORATORS
# =============================================================================

def get_current_user_from_db():
    """Get the current user object from the database."""
    username = get_jwt_identity()
    if not username:
        return None
    from database.models.User import User
    return database.session.query(User).filter_by(username=username).first()


def require_group_member(f):
    """Decorator to require the user to be a member of the group."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        group_id = kwargs.get('group_id')
        if not group_id:
            return jsonify({'success': False, 'error': 'Group ID required'}), HTTPStatus.BAD_REQUEST
        
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        if not database.is_group_member(group_id, user.id):
            return jsonify({'success': False, 'error': 'You are not a member of this group'}), HTTPStatus.FORBIDDEN
        
        g.current_user = user
        g.group_id = group_id
        return f(*args, **kwargs)
    return decorated_function


def require_group_admin(f):
    """Decorator to require the user to be an admin of the group."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        group_id = kwargs.get('group_id')
        if not group_id:
            return jsonify({'success': False, 'error': 'Group ID required'}), HTTPStatus.BAD_REQUEST
        
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        if not database.is_group_admin(group_id, user.id):
            return jsonify({'success': False, 'error': 'Admin access required'}), HTTPStatus.FORBIDDEN
        
        g.current_user = user
        g.group_id = group_id
        return f(*args, **kwargs)
    return decorated_function


def require_site_admin(f):
    """Decorator to require the user to be a site admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        if not user.admin:
            return jsonify({'success': False, 'error': 'Site admin access required'}), HTTPStatus.FORBIDDEN
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def before_request_func():
    time.sleep(0)


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    try:
        user = database.login(username, password)
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(minutes=30))
        return jsonify({
            'success': True,
            'error': None,
            'access_token': access_token,
            'user': serialise_model(user)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'access_token': None, 'user': None})


# =============================================================================
# SCORE ENDPOINTS
# =============================================================================

@app.route('/getScores', methods=['POST'])
@jwt_required()
def get_scores():
    """
    Get scores based on scope.
    
    Request body:
    {
        "timezone": "Europe/London",
        "scope": "personal" | {"type": "group", "groupId": 123}
    }
    """
    try:
        data = request.json
        database.set_timezone(data.get('timezone', 'UTC'))
        
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        scope = data.get('scope', 'personal')
        
        if scope == 'personal':
            # Personal scope - just the user's scores
            scores = database.get_scores_for_user(user.id)
            members = [{
                'id': user.id,
                'username': user.username,
                'forename': user.forename
            }]
        elif isinstance(scope, dict) and scope.get('type') == 'group':
            # Group scope
            group_id = scope.get('groupId')
            if not group_id:
                return jsonify({'success': False, 'error': 'Group ID required'}), HTTPStatus.BAD_REQUEST
            
            if not database.is_group_member(group_id, user.id):
                return jsonify({'success': False, 'error': 'You are not a member of this group'}), HTTPStatus.FORBIDDEN
            
            scores = database.get_scores_for_group(group_id)
            members = database.get_group_members(group_id)
        else:
            # Legacy behavior - return all scores (backwards compatibility)
            scores = database.get_scores()
            members = [{'id': u.id, 'username': u.username, 'forename': u.forename} for u in database.get_users()]
        
        return jsonify({
            'scores': scores,
            'members': members
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/addScore', methods=['POST'])
@jwt_required()
def add_score():
    """
    Add a score for the authenticated user.
    
    Request body:
    {
        "date": "2024-01-15",
        "score": 4,
        "timezone": "Europe/London"
    }
    """
    try:
        data = request.json
        database.set_timezone(data.get('timezone', 'UTC'))
        
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        date = data.get('date')
        score = data.get('score')
        
        if not date or score is None:
            return jsonify({'success': False, 'error': 'Date and score are required'}), HTTPStatus.BAD_REQUEST
        
        # Validate score
        if score not in [1, 2, 3, 4, 5, 6, 8]:
            return jsonify({'success': False, 'error': 'Score must be 1-6 or 8 (fail)'}), HTTPStatus.BAD_REQUEST
        
        # Validate date is not in future
        score_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if score_date > datetime.date.today():
            return jsonify({'success': False, 'error': 'Cannot add scores for future dates'}), HTTPStatus.BAD_REQUEST
        
        database.add_score(date, user.id, score)
        
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/getUsers', methods=['GET'])
@jwt_required()
def get_users():
    """
    Get users, optionally scoped to a group.
    
    Query params:
    - scope: "personal" | "group"
    - groupId: required if scope is "group"
    """
    try:
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        scope = request.args.get('scope', 'all')
        
        if scope == 'personal':
            users = [{'id': user.id, 'username': user.username, 'forename': user.forename}]
        elif scope == 'group':
            group_id = request.args.get('groupId', type=int)
            if not group_id:
                return jsonify({'success': False, 'error': 'Group ID required'}), HTTPStatus.BAD_REQUEST
            
            if not database.is_group_member(group_id, user.id):
                return jsonify({'success': False, 'error': 'You are not a member of this group'}), HTTPStatus.FORBIDDEN
            
            users = database.get_group_members(group_id)
        else:
            # Legacy behavior - return all users
            users = [{"id": u.id, "username": u.username, "forename": u.forename} for u in database.get_users()]
        
        return jsonify(users)
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# GROUP ENDPOINTS
# =============================================================================

@app.route('/groups', methods=['GET'])
@jwt_required()
def list_groups():
    """Get all groups the current user is a member of."""
    try:
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        groups = database.get_user_groups(user.id)
        return jsonify(groups)
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    """
    Create a new group.
    
    Request body:
    {
        "name": "Family Wordle",
        "include_historical_data": true
    }
    """
    try:
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Group name is required'}), HTTPStatus.BAD_REQUEST
        
        if len(name) > 50:
            return jsonify({'success': False, 'error': 'Group name must be 50 characters or less'}), HTTPStatus.BAD_REQUEST
        
        include_historical_data = data.get('include_historical_data', True)
        
        group = database.create_group(name, user.id, include_historical_data)
        group_details = database.get_group_details(group.id)
        
        return jsonify({
            'success': True,
            'group': group_details
        }), HTTPStatus.CREATED
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>', methods=['GET'])
@jwt_required()
@require_group_member
def get_group(group_id):
    """Get detailed information about a group."""
    try:
        group_details = database.get_group_details(group_id)
        if not group_details:
            return jsonify({'success': False, 'error': 'Group not found'}), HTTPStatus.NOT_FOUND
        
        # Add current user's role
        group_details['current_user_role'] = 'admin' if database.is_group_admin(group_id, g.current_user.id) else 'member'
        
        return jsonify(group_details)
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
@require_group_admin
def update_group(group_id):
    """
    Update group settings (admin only).
    
    Request body:
    {
        "name": "New Name",
        "include_historical_data": false
    }
    """
    try:
        data = request.json
        
        name = data.get('name')
        if name is not None:
            name = name.strip()
            if not name:
                return jsonify({'success': False, 'error': 'Group name cannot be empty'}), HTTPStatus.BAD_REQUEST
            if len(name) > 50:
                return jsonify({'success': False, 'error': 'Group name must be 50 characters or less'}), HTTPStatus.BAD_REQUEST
        
        include_historical_data = data.get('include_historical_data')
        
        group = database.update_group(group_id, name=name, include_historical_data=include_historical_data)
        if not group:
            return jsonify({'success': False, 'error': 'Group not found'}), HTTPStatus.NOT_FOUND
        
        group_details = database.get_group_details(group_id)
        return jsonify({
            'success': True,
            'group': group_details
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
@require_group_admin
def delete_group(group_id):
    """Delete a group (admin only)."""
    try:
        success = database.delete_group(group_id)
        if not success:
            return jsonify({'success': False, 'error': 'Group not found'}), HTTPStatus.NOT_FOUND
        
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# MEMBERSHIP ENDPOINTS
# =============================================================================

@app.route('/groups/join', methods=['POST'])
@jwt_required()
def join_group():
    """
    Join a group via invite code.
    
    Request body:
    {
        "invite_code": "ABC12XYZ"
    }
    """
    try:
        user = get_current_user_from_db()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.UNAUTHORIZED
        
        data = request.json
        invite_code = data.get('invite_code', '').strip()
        
        if not invite_code:
            return jsonify({'success': False, 'error': 'Invite code is required'}), HTTPStatus.BAD_REQUEST
        
        result = database.join_group(invite_code, user.id)
        
        if result['success']:
            return jsonify(result), HTTPStatus.OK
        else:
            return jsonify(result), HTTPStatus.BAD_REQUEST
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required()
@require_group_member
def leave_group(group_id):
    """Leave a group."""
    try:
        result = database.leave_group(group_id, g.current_user.id)
        
        if result['success']:
            return jsonify(result), HTTPStatus.OK
        else:
            return jsonify(result), HTTPStatus.BAD_REQUEST
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_group_admin
def remove_member(group_id, user_id):
    """Remove a member from the group (admin only)."""
    try:
        result = database.remove_member(group_id, user_id, g.current_user.id)
        
        if result['success']:
            return jsonify(result), HTTPStatus.OK
        else:
            return jsonify(result), HTTPStatus.BAD_REQUEST
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>/members/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_group_admin
def update_member_role(group_id, user_id):
    """
    Update a member's role (admin only).
    
    Request body:
    {
        "role": "admin" | "member"
    }
    """
    try:
        data = request.json
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({'success': False, 'error': 'Role is required'}), HTTPStatus.BAD_REQUEST
        
        result = database.update_member_role(group_id, user_id, new_role, g.current_user.id)
        
        if result['success']:
            return jsonify(result), HTTPStatus.OK
        else:
            return jsonify(result), HTTPStatus.BAD_REQUEST
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/groups/<int:group_id>/regenerate-code', methods=['POST'])
@jwt_required()
@require_group_admin
def regenerate_invite_code(group_id):
    """Generate a new invite code for the group (admin only)."""
    try:
        new_code = database.regenerate_invite_code(group_id)
        
        if not new_code:
            return jsonify({'success': False, 'error': 'Group not found'}), HTTPStatus.NOT_FOUND
        
        return jsonify({
            'success': True,
            'invite_code': new_code
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# SITE ADMIN ENDPOINTS
# =============================================================================

@app.route('/admin/updateScore', methods=['POST'])
@jwt_required()
@require_site_admin
def admin_update_score():
    """
    Update any user's score (site admin only).
    
    Request body:
    {
        "date": "2024-01-15",
        "user_id": 2,
        "score": 4,
        "timezone": "Europe/London"
    }
    """
    try:
        data = request.json
        database.set_timezone(data.get('timezone', 'UTC'))
        
        date = data.get('date')
        user_id = data.get('user_id')
        score = data.get('score')
        
        if not date or user_id is None or score is None:
            return jsonify({'success': False, 'error': 'Date, user_id, and score are required'}), HTTPStatus.BAD_REQUEST
        
        # Validate score
        if score not in [1, 2, 3, 4, 5, 6, 8]:
            return jsonify({'success': False, 'error': 'Score must be 1-6 or 8 (fail)'}), HTTPStatus.BAD_REQUEST
        
        # Check user exists
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), HTTPStatus.NOT_FOUND
        
        database.add_score(date, user_id, score)
        
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# LEGACY ENDPOINTS (kept for backwards compatibility)
# =============================================================================

@app.route('/executeSql', methods=['POST'])
@jwt_required()
@require_site_admin
def execute_sql():
    try:
        database.execute(request.json['sql'])
        resp = jsonify('')
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify(str(e)), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/getWordleAnswer', methods=['POST'])
@jwt_required()
def get_wordle_answer():
    try:
        date_str = request.json['date']  # Format: YYYY-MM-DD
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Format date for rockpapershotgun URL
        formatted_date = f"{date_obj.day:02d}-{date_obj.month:02d}-{str(date_obj.year)[2:]}"
        url = f"https://www.rockpapershotgun.com/wordle-hint-and-answer-today-{formatted_date}"
        
        # Fetch the page content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the answer section
        answer_section = soup.find('h2', string=lambda s: s and 'What is today\'s Wordle answer' in s)
        if not answer_section:
            raise Exception("Could not find answer section")
        
        # Look for the answer in a <strong> tag within paragraphs after the h2
        paragraphs = answer_section.find_next_siblings('p')
        for p in paragraphs:
            strong_tag = p.find('strong')
            if strong_tag:
                answer = strong_tag.text.strip().lower().replace('.', '')
                # Generate the playable URL
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


@app.route('/admin/set-title', methods=['GET', 'POST'])
def set_title_page():
    if request.method == 'POST':
        password = request.form.get('password')
        title = request.form.get('title', '').strip()
        expiry_str = request.form.get('expiry')
        
        try:
            user = database.login('wjrm500', password)
            if not user.admin:
                return '<h1>Unauthorised</h1><a href="/admin/set-title">Back</a>'
        except:
            return '<h1>Wrong password</h1><a href="/admin/set-title">Back</a>'
        
        if not title:
            return '<h1>Title cannot be empty</h1><a href="/admin/set-title">Back</a>'
        
        # Escape any HTML to prevent XSS
        title = html.escape(title)
        
        # Parse expiry datetime
        try:
            expiry = datetime.datetime.fromisoformat(expiry_str)
        except:
            return '<h1>Invalid expiry date</h1><a href="/admin/set-title">Back</a>'
        
        with open('custom_title.json', 'w') as f:
            json.dump({'title': title, 'expiry': expiry.isoformat()}, f)
        
        expiry_display = expiry.strftime('%Y-%m-%d %H:%M:%S')
        return f'''
            <h1>Done!</h1>
            <p>Title: {title}</p>
            <p>Expires: {expiry_display}</p>
        '''
    
    # Default expiry: today at 23:59:59
    default_expiry = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    default_expiry_str = default_expiry.strftime('%Y-%m-%dT%H:%M')
    
    return f'''
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Set Title</title></head>
    <body>
    <h1>Set custom page title</h1>
    <form method="POST">
    <label>Password for wjrm500:</label><br>
    <input type="password" name="password" placeholder="Password" required autocomplete="current-password"><br><br>
    <label>New page title:</label><br>
    <input type="text" name="title" placeholder="Title" required><br><br>
    <label>Expires:</label><br>
    <input type="datetime-local" name="expiry" value="{default_expiry_str}" required><br><br>
    <button type="submit">Update</button>
    </form>
    </body>
    </html>
    '''


@app.route('/getTitle', methods=['GET'])
def get_title():
    try:
        with open('custom_title.json', 'r') as f:
            data = json.load(f)
        expiry = datetime.datetime.fromisoformat(data['expiry'])
        if expiry > datetime.datetime.now():
            return jsonify({'title': data['title']})
    except:
        pass
    return jsonify({'title': 'Welcome to WordleWise'})


if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
