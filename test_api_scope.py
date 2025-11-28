import requests
import json
import datetime

# Base URL
BASE_URL = 'http://localhost:5000'

def test_scoped_endpoints():
    print("Testing Scoped Endpoints...")
    
    # 1. Login
    print("Logging in...")
    resp = requests.post(f'{BASE_URL}/login', json={'username': 'wjrm500', 'password': 'password'})
    if resp.status_code != 200:
        print("Login failed")
        return
    token = resp.json().get('access_token')
    print(f"Token received: {token}")
    if not token:
        print("Error: No access token received")
        print(resp.json())
        return
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Create a group for testing
    print("Creating test group...")
    group_resp = requests.post(f'{BASE_URL}/groups', json={'name': 'Scope Test Group'}, headers=headers)
    if group_resp.status_code != 200:
        print("Group creation failed")
        print(group_resp.text)
        return
    group_id = group_resp.json()['group']['id']
    print(f"Created group {group_id}")
    
    # 3. Add a score for today
    print("Adding score...")
    today = datetime.date.today().strftime("%Y-%m-%d")
    score_data = {
        'date': today,
        'score': 3,
        'timezone': 'Europe/London'
    }
    requests.post(f'{BASE_URL}/addScore', json=score_data, headers=headers)
    
    # 4. Get Scores - Personal Scope
    print("Getting Personal Scores...")
    personal_req = {
        'scope': 'personal',
        'timezone': 'Europe/London'
    }
    resp = requests.post(f'{BASE_URL}/getScores', json=personal_req, headers=headers)
    print(f"Personal Scores: {resp.status_code}")
    # Verify we see our score
    data = resp.json()
    # Basic check - just ensure it returns a list
    if not isinstance(data, list):
        print("Error: Personal scores not a list")
        
    # 5. Get Scores - Group Scope
    print("Getting Group Scores...")
    group_req = {
        'scope': {'type': 'group', 'groupId': group_id},
        'timezone': 'Europe/London'
    }
    resp = requests.post(f'{BASE_URL}/getScores', json=group_req, headers=headers)
    print(f"Group Scores: {resp.status_code}")
    
    # 6. Get Users - Personal
    print("Getting Personal Users...")
    resp = requests.get(f'{BASE_URL}/getUsers?scope=personal', headers=headers)
    users = resp.json()
    print(f"Personal Users count: {len(users)}")
    if len(users) != 1:
        print("Error: Should be 1 user for personal scope")
        
    # 7. Get Users - Group
    print("Getting Group Users...")
    resp = requests.get(f'{BASE_URL}/getUsers?scope=group&groupId={group_id}', headers=headers)
    users = resp.json()
    print(f"Group Users count: {len(users)}")
    if len(users) < 1:
        print("Error: Should be at least 1 user for group scope")
        
    # Cleanup
    print("Cleaning up...")
    requests.delete(f'{BASE_URL}/groups/{group_id}', headers=headers)
    
    print("Test Complete")

if __name__ == '__main__':
    test_scoped_endpoints()
