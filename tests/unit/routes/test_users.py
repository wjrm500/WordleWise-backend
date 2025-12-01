import pytest
from flask import json

@pytest.fixture
def auth_client(client, db):
    user = db.register_user("testuser", "password", "Test User")
    login_resp = client.post('/login', json={'username': 'testuser', 'password': 'password'})
    token = login_resp.json['access_token']
    return client, {'Authorization': f'Bearer {token}'}, user

def test_get_users_personal(auth_client):
    client, headers, user = auth_client
    
    resp = client.get('/users?scope=personal', headers=headers)
    
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]['username'] == 'testuser'

def test_get_users_group(client, db):
    # Setup: U1, U2 in G1
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("G1", u1.id)
    u2 = db.register_user("u2", "pass", "U2")
    db.join_group(g1.id, u2.id)
    
    # Login as U1
    login_resp = client.post('/login', json={'username': 'u1', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.get(f'/users?scope=group&groupId={g1.id}', headers=headers)
    
    assert resp.status_code == 200
    assert len(resp.json) == 2
    usernames = [u['username'] for u in resp.json]
    assert 'u1' in usernames
    assert 'u2' in usernames

def test_get_users_group_not_member(client, db):
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("G1", u1.id)
    
    u2 = db.register_user("u2", "pass", "U2")
    login_resp = client.post('/login', json={'username': 'u2', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.get(f'/users?scope=group&groupId={g1.id}', headers=headers)
    assert resp.status_code == 403
