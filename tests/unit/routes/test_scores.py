import pytest
import datetime
from flask import json
import freezegun

@pytest.fixture
def auth_client(client, db):
    user = db.register_user("testuser", "password", "Test User")
    login_resp = client.post('/login', json={'username': 'testuser', 'password': 'password'})
    token = login_resp.json['access_token']
    return client, {'Authorization': f'Bearer {token}'}, user

def test_add_score(auth_client, db):
    client, headers, user = auth_client
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    score_data = {
        'date': today,
        'score': 4,
        'timezone': 'Europe/London'
    }
    
    resp = client.post('/scores', json=score_data, headers=headers)
    assert resp.status_code == 200
    
    # Verify in DB
    scores = db.get_scores(user.id, 'personal')
    # Finding the score in the nested structure is complex, let's check DB directly
    from database.models.Score import Score
    score_obj = db.session.query(Score).filter_by(user_id=user.id).first()
    assert score_obj.score == 4

def test_delete_score(auth_client, db):
    client, headers, user = auth_client
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Add first
    db.add_score(today, user.id, 3)
    
    # Delete (send null)
    score_data = {
        'date': today,
        'score': None,
        'timezone': 'Europe/London'
    }
    resp = client.post('/scores', json=score_data, headers=headers)
    assert resp.status_code == 200
    
    from database.models.Score import Score
    score_obj = db.session.query(Score).filter_by(user_id=user.id).first()
    assert score_obj is None

def test_get_scores_personal(auth_client, db):
    client, headers, user = auth_client
    
    with freezegun.freeze_time("2023-01-01"):
        db.add_score("2023-01-01", user.id, 5)
        
        # Re-login to get a token valid for 2023
        login_resp = client.post('/login', json={'username': 'testuser', 'password': 'password'})
        headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
        
        query_params = {
            'scope': 'personal',
            'timezone': 'Europe/London'
        }
        resp = client.get('/scores', query_string=query_params, headers=headers)
        
        assert resp.status_code == 200
        assert len(resp.json) == 1
        assert resp.json[0]['data']['2023-01-01']['testuser'] == 5

def test_get_scores_group(client, db):
    # Setup: U1 (admin), U2 (member) in G1
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("G1", u1.id)
    u2 = db.register_user("u2", "pass", "U2")
    db.join_group(g1.id, u2.id)
    
    # Add scores
    with freezegun.freeze_time("2023-01-01"):
        db.add_score("2023-01-01", u1.id, 3)
        db.add_score("2023-01-01", u2.id, 4)
        
        # Login as U1
        login_resp = client.post('/login', json={'username': 'u1', 'password': 'pass'})
        headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
        
        query_params = {
            'scope': 'group',
            'groupId': g1.id,
            'timezone': 'Europe/London'
        }
        resp = client.get('/scores', query_string=query_params, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json[0]['data']['2023-01-01']
        assert data['u1'] == 3
        assert data['u2'] == 4

def test_get_scores_group_not_member(client, db):
    u1 = db.register_user("u1", "pass", "U1")
    g1 = db.create_group("G1", u1.id)
    
    u2 = db.register_user("u2", "pass", "U2")
    login_resp = client.post('/login', json={'username': 'u2', 'password': 'pass'})
    headers = {'Authorization': f"Bearer {login_resp.json['access_token']}"}
    
    query_params = {
        'scope': 'group',
        'groupId': g1.id,
        'timezone': 'Europe/London'
    }
    resp = client.get('/scores', query_string=query_params, headers=headers)
    assert resp.status_code == 403
