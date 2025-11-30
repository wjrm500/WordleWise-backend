import datetime
import pytest
from database.models.User import User
import hashlib

def test_scoped_endpoints(client, db):
    # Seed user
    password = 'password'
    password_hash = hashlib.md5(password.encode()).hexdigest()
    user = User(username='wjrm500_scope', password_hash=password_hash, forename='TestScope')
    db.session.add(user)
    db.session.commit()
    
    # 1. Login
    login_resp = client.post('/login', json={'username': 'wjrm500_scope', 'password': 'password'})
    assert login_resp.status_code == 200
    token = login_resp.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Create a group for testing
    group_resp = client.post('/groups', json={'name': 'Scope Test Group'}, headers=headers)
    assert group_resp.status_code == 200
    group_id = group_resp.json['group']['id']
    
    # 3. Add a score for today
    today = datetime.date.today().strftime("%Y-%m-%d")
    score_data = {
        'date': today,
        'score': 3,
        'timezone': 'Europe/London'
    }
    resp = client.post('/addScore', json=score_data, headers=headers)
    assert resp.status_code == 200
    
    # 4. Get Scores - Personal Scope
    personal_req = {
        'scope': 'personal',
        'timezone': 'Europe/London'
    }
    resp = client.post('/getScores', json=personal_req, headers=headers)
    assert resp.status_code == 200
    data = resp.json
    assert isinstance(data, list)
        
    # 5. Get Scores - Group Scope
    group_req = {
        'scope': {'type': 'group', 'groupId': group_id},
        'timezone': 'Europe/London'
    }
    resp = client.post('/getScores', json=group_req, headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    
    # 6. Get Users - Personal
    resp = client.get('/getUsers?scope=personal', headers=headers)
    assert resp.status_code == 200
    users = resp.json
    assert len(users) == 1
    assert users[0]['username'] == 'wjrm500_scope'
        
    # 7. Get Users - Group
    resp = client.get(f'/getUsers?scope=group&groupId={group_id}', headers=headers)
    assert resp.status_code == 200
    users = resp.json
    assert len(users) >= 1
    assert any(u['username'] == 'wjrm500_scope' for u in users)
