from flask import abort
from flask_jwt_extended import get_jwt_identity
from database.models.User import User

def get_current_user(database):
    username = get_jwt_identity()
    user = database.session.query(User).filter_by(username=username).first()
    if not user:
        abort(401, 'User not found')
    return user

def require_group_member(database, group_id, user):
    membership = database.get_membership(group_id, user.id)
    if not membership:
        abort(403, "You are not a member of this group")
    return membership

def require_group_admin(database, group_id, user):
    membership = require_group_member(database, group_id, user)
    if membership.role != 'admin':
        abort(403, "Admin access required")
    return membership
