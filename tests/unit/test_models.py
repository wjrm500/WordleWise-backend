from database.models import User
import pytest

def test_model_relationships(db):
    user = User(username='testuser_models', password_hash='hash', forename='Test')
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    
    group = db.create_group("Test Model Group", user.id)
    assert group.id is not None
    assert group.name == "Test Model Group"
    assert group.invite_code is not None
    
    members = db.get_user_groups(user.id)
    assert len(members) == 1
    assert members[0].name == "Test Model Group"
    
    member_details = db.get_group_member_details(group.id)
    assert len(member_details) == 1
    assert member_details[0][0].username == 'testuser_models'
