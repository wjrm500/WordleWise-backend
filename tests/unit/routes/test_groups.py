import pytest
from flask import json

@pytest.fixture
def auth_client(client, db):
    """Fixture to provide an authenticated client and the user."""
    user = db.register_user("testuser", "password", "Test User")
    login_resp = client.post('/login', json={'username': 'testuser', 'password': 'password'})
    token = login_resp.json['access_token']
    return client, {'Authorization': f'Bearer {token}'}, user

def test_create_group(auth_client):
    client, headers, user = auth_client
    
    resp = client.post('/groups', json={'name': 'New Group'}, headers=headers)
    
    assert resp.status_code == 200
    assert resp.json['success'] == True
    assert resp.json['group']['name'] == 'New Group'
    assert resp.json['group']['invite_code'] is not None
    assert len(resp.json['group']['members']) == 1
    assert resp.json['group']['members'][0]['role'] == 'admin'

def test_create_group_missing_name(auth_client):
    client, headers, _ = auth_client
    resp = client.post('/groups', json={}, headers=headers)
    assert resp.status_code == 400
    assert 'Group name is required' in resp.json['error']

def test_get_groups(auth_client):
    client, headers, _ = auth_client
    
    # Create two groups
    client.post('/groups', json={'name': 'G1'}, headers=headers)
    client.post('/groups', json={'name': 'G2'}, headers=headers)
    
    resp = client.get('/groups', headers=headers)
    
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert any(g['name'] == 'G1' for g in resp.json)
    assert any(g['name'] == 'G2' for g in resp.json)

def test_get_group_details(auth_client):
    client, headers, _ = auth_client
    
    create_resp = client.post('/groups', json={'name': 'Detail Group'}, headers=headers)
    group_id = create_resp.json['group']['id']
    
    resp = client.get(f'/groups/{group_id}', headers=headers)
    
    assert resp.status_code == 200
    assert resp.json['name'] == 'Detail Group'
    assert resp.json['current_user_role'] == 'admin'

def test_get_group_details_not_member(client, db):
    # User 1 creates group
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("G1", u1.id)
    
    # User 2 tries to access
    db.register_user("u2", "pass", "U2")
    login_resp = client.post('/login', json={'username': 'u2', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.get(f'/groups/{g1.id}', headers=headers)
    assert resp.status_code == 403

def test_update_group(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post('/groups', json={'name': 'Old Name'}, headers=headers)
    group_id = create_resp.json['group']['id']
    
    resp = client.put(f'/groups/{group_id}', json={'name': 'New Name'}, headers=headers)
    assert resp.status_code == 200
    
    # Verify
    resp = client.get(f'/groups/{group_id}', headers=headers)
    assert resp.json['name'] == 'New Name'

def test_delete_group(auth_client, db):
    client, headers, _ = auth_client
    create_resp = client.post('/groups', json={'name': 'Delete Me'}, headers=headers)
    group_id = create_resp.json['group']['id']
    
    resp = client.delete(f'/groups/{group_id}', headers=headers)
    assert resp.status_code == 200
    
    assert db.get_group(group_id) is None

def test_join_group(client, db):
    # U1 creates group
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("Joinable", u1.id)
    invite_code = g1.invite_code
    
    # U2 joins
    db.register_user("u2", "pass", "U2")
    login_resp = client.post('/login', json={'username': 'u2', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.post('/groups/join', json={'invite_code': invite_code}, headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] == True
    
    # Verify membership
    members = db.get_group_members(g1.id)
    assert len(members) == 2

def test_join_group_invalid_code(auth_client):
    client, headers, _ = auth_client
    resp = client.post('/groups/join', json={'invite_code': 'INVALID'}, headers=headers)
    assert resp.status_code == 400
    assert resp.json['error'] == 'Invalid invite code'

def test_leave_group(client, db):
    # U1 creates, U2 joins
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("Leavable", u1.id)
    
    u2 = db.register_user("u2", "pass", "U2")
    db.join_group(g1.id, u2.id)
    
    # U2 leaves
    login_resp = client.post('/login', json={'username': 'u2', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.post(f'/groups/{g1.id}/leave', headers=headers)
    assert resp.status_code == 200
    
    members = db.get_group_members(g1.id)
    assert len(members) == 1
    assert members[0].id == u1.id

def test_remove_member(client, db):
    # U1 (admin), U2 (member)
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("Removable", u1.id)
    u2 = db.register_user("u2", "pass", "U2")
    db.join_group(g1.id, u2.id)
    
    # U1 removes U2
    login_resp = client.post('/login', json={'username': 'u1', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.delete(f'/groups/{g1.id}/members/{u2.id}', headers=headers)
    assert resp.status_code == 200
    
    members = db.get_group_members(g1.id)
    assert len(members) == 1

def test_update_member_role(client, db):
    # U1 (admin), U2 (member)
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("RoleChange", u1.id)
    u2 = db.register_user("u2", "pass", "U2")
    db.join_group(g1.id, u2.id)
    
    # U1 promotes U2
    login_resp = client.post('/login', json={'username': 'u1', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    resp = client.put(f'/groups/{g1.id}/members/{u2.id}', json={'role': 'admin'}, headers=headers)
    assert resp.status_code == 200
    
    membership = db.get_membership(g1.id, u2.id)
    assert membership.role == 'admin'

def test_regenerate_invite_code(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post('/groups', json={'name': 'Code Group'}, headers=headers)
    group_id = create_resp.json['group']['id']
    old_code = create_resp.json['group']['invite_code']
    
    resp = client.post(f'/groups/{group_id}/regenerate-code', headers=headers)
    assert resp.status_code == 200
    new_code = resp.json['invite_code']
    
    assert new_code != old_code

def test_default_scope(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post('/groups', json={'name': 'Scope Group'}, headers=headers)
    group_id = create_resp.json['group']['id']
    
    # Set default scope to group
    resp = client.put('/user/default-scope', json={'type': 'group', 'groupId': group_id}, headers=headers)
    assert resp.status_code == 200
    
    # Verify
    resp = client.get('/user/default-scope', headers=headers)
    assert resp.json['type'] == 'group'
    assert resp.json['groupId'] == group_id
