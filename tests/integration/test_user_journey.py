import pytest
import datetime
import freezegun

def test_journey_new(client, db):
    """
    Test a complete user journey:
    1. Register User 1 (Admin)
    2. Login User 1
    3. Create Group
    4. Register User 2 (Member)
    5. Login User 2
    6. Join Group
    7. Add scores for both
    8. Verify group scores
    """
    
    # Freeze time for the entire test to ensure token iat is consistent
    with freezegun.freeze_time("2023-01-01"):
        # 1. Register User 1
        resp = client.post('/register', json={
            'username': 'admin',
            'password': 'password',
            'forename': 'Admin'
        })
        assert resp.status_code == 200
        
        # 2. Login User 1
        resp = client.post('/login', json={'username': 'admin', 'password': 'password'})
        token1 = resp.json['access_token']
        headers1 = {'Authorization': f'Bearer {token1}'}
        
        # 3. Create Group
        resp = client.post('/groups', json={'name': 'Integration Group'}, headers=headers1)
        assert resp.status_code == 200
        group_id = resp.json['group']['id']
        invite_code = resp.json['group']['invite_code']
        
        # 4. Register User 2
        resp = client.post('/register', json={
            'username': 'member',
            'password': 'password',
            'forename': 'Member'
        })
        assert resp.status_code == 200
        
        # 5. Login User 2
        resp = client.post('/login', json={'username': 'member', 'password': 'password'})
        token2 = resp.json['access_token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # 6. Join Group
        resp = client.post('/groups/join', json={'invite_code': invite_code}, headers=headers2)
        assert resp.status_code == 200
        
        # 7. Add scores (on 2023-01-01)
        today = "2023-01-01"
        # Admin score
        client.post('/addScore', json={
            'date': today,
            'score': 3,
            'timezone': 'Europe/London'
        }, headers=headers1)
        
        # Member score
        client.post('/addScore', json={
            'date': today,
            'score': 5,
            'timezone': 'Europe/London'
        }, headers=headers2)
        
        # 8. Verify group scores (as Admin)
        # Move time forward slightly if needed, or just check the data
        # We'll check for the week containing 2023-01-01
        
        req_data = {
            'scope': {'type': 'group', 'groupId': group_id},
            'timezone': 'Europe/London'
        }
        resp = client.post('/getScores', json=req_data, headers=headers1)
        assert resp.status_code == 200
        
        # Find the week and day
        # Week starts Dec 26 2022
        week_data = resp.json[0]
        day_data = week_data['data'][today]
        
        assert day_data['admin'] == 3
        assert day_data['member'] == 5
