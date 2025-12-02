from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required

from utils.auth_helpers import get_current_user, require_group_member, require_group_admin

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
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

@groups_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Group name is required'}), 400
            
        if len(name) > 15:
            return jsonify({'error': 'Group name must be 15 characters or less'}), 400

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

@groups_bp.route('/groups/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_details(group_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        membership = require_group_member(database, group_id, user)

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

@groups_bp.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        require_group_admin(database, group_id, user)

        data = request.json
        updates = {}
        if 'name' in data:
            if len(data['name']) > 15:
                return jsonify({'error': 'Group name must be 15 characters or less'}), 400
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

@groups_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        require_group_admin(database, group_id, user)

        database.delete_group(group_id)

        return jsonify({"success": True})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/groups/join', methods=['POST'])
@jwt_required()
def join_group():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
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

@groups_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        success, message = database.leave_group(group_id, user.id)

        if not success:
            return jsonify({"success": False, "error": message}), 400

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(group_id, member_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        require_group_admin(database, group_id, user)

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

@groups_bp.route('/groups/<int:group_id>/members/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_member_role(group_id, member_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        require_group_admin(database, group_id, user)

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

@groups_bp.route('/groups/<int:group_id>/regenerate-code', methods=['POST'])
@jwt_required()
def regenerate_invite_code(group_id):
    database = current_app.config['database']
    try:
        user = get_current_user(database)
        require_group_admin(database, group_id, user)

        new_code = database.regenerate_invite_code(group_id)
        return jsonify({"success": True, "invite_code": new_code})
    except Exception as e:
        if hasattr(e, 'code'):
            return jsonify({'error': str(e)}), e.code
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/user/default-scope', methods=['PUT'])
@jwt_required()
def set_default_scope():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
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

@groups_bp.route('/user/default-scope', methods=['GET'])
@jwt_required()
def get_default_scope():
    database = current_app.config['database']
    try:
        user = get_current_user(database)
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
