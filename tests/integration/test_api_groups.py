import json
import pytest



def test_groups_flow(client, db):
    # Seed user
    from database.models.User import User
    import hashlib
    
    # Create user manually in the DB
    password = 'password'
    password_hash = hashlib.md5(password.encode()).hexdigest()
    user = User(username='wjrm500', password_hash=password_hash, forename='Test')
    db.session.add(user)
    db.session.commit()
    
    # Login
    login_resp = client.post('/login', json={'username': 'wjrm500', 'password': 'password'})
    
    if login_resp.status_code != 200:
        pytest.fail(f"Login failed: {login_resp.json}")
        
    token = login_resp.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Create Group
    group_data = {'name': 'Test API Group', 'include_historical_data': True}
    resp = client.post('/groups', json=group_data, headers=headers)
    assert resp.status_code == 200
    
    group_id = resp.json['group']['id']
    invite_code = resp.json['group']['invite_code']
    
    # 3. Get Groups
    resp = client.get('/groups', headers=headers)
    assert resp.status_code == 200
    groups = resp.json
    found = any(g['id'] == group_id for g in groups)
    assert found
    
    # 4. Get Group Details
    resp = client.get(f'/groups/{group_id}', headers=headers)
    assert resp.status_code == 200
    assert resp.json['name'] == 'Test API Group'
        
    # 5. Update Group
    resp = client.put(f'/groups/{group_id}', json={'name': 'Updated API Group'}, headers=headers)
    assert resp.status_code == 200
    
    # Verify update
    resp = client.get(f'/groups/{group_id}', headers=headers)
    assert resp.json['name'] == 'Updated API Group'
        
    # 6. Regenerate Invite Code
    resp = client.post(f'/groups/{group_id}/regenerate-code', headers=headers)
    assert resp.status_code == 200
    new_code = resp.json['invite_code']
    assert new_code != invite_code
        
    # 7. Delete Group
    resp = client.delete(f'/groups/{group_id}', headers=headers)
    assert resp.status_code == 200
    
    # Verify deletion
    resp = client.get(f'/groups/{group_id}', headers=headers)
    assert resp.status_code in [403, 404, 500] 
