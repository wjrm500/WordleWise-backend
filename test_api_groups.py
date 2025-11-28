import requests
import json
import os
import sys

# Base URL
BASE_URL = 'http://localhost:5000'

def test_groups():
    print("Testing Group Endpoints...")
    
    # 1. Login to get token
    print("Logging in...")
    resp = requests.post(f'{BASE_URL}/login', json={'username': 'wjrm500', 'password': 'password'}) # Assuming this user exists from previous phases or seed
    # If user doesn't exist, we might need to create one or use existing one. 
    # Based on previous context, wjrm500 exists.
    
    if resp.status_code != 200:
        print("Login failed. Make sure server is running and user exists.")
        return
        
    token = resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Create Group
    print("Creating group...")
    group_data = {'name': 'Test API Group', 'include_historical_data': True}
    resp = requests.post(f'{BASE_URL}/groups', json=group_data, headers=headers)
    print(f"Create Group: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.json())
        return
        
    group_id = resp.json()['group']['id']
    invite_code = resp.json()['group']['invite_code']
    print(f"Group Created: ID {group_id}, Code {invite_code}")
    
    # 3. Get Groups
    print("Listing groups...")
    resp = requests.get(f'{BASE_URL}/groups', headers=headers)
    print(f"Get Groups: {resp.status_code}")
    groups = resp.json()
    found = False
    for g in groups:
        if g['id'] == group_id:
            found = True
            break
    if not found:
        print("Error: Created group not found in list")
    
    # 4. Get Group Details
    print("Getting group details...")
    resp = requests.get(f'{BASE_URL}/groups/{group_id}', headers=headers)
    print(f"Get Details: {resp.status_code}")
    if resp.json()['name'] != 'Test API Group':
        print("Error: Group name mismatch")
        
    # 5. Update Group
    print("Updating group...")
    resp = requests.put(f'{BASE_URL}/groups/{group_id}', json={'name': 'Updated API Group'}, headers=headers)
    print(f"Update Group: {resp.status_code}")
    
    # Verify update
    resp = requests.get(f'{BASE_URL}/groups/{group_id}', headers=headers)
    if resp.json()['name'] != 'Updated API Group':
        print("Error: Update failed")
        
    # 6. Regenerate Invite Code
    print("Regenerating invite code...")
    resp = requests.post(f'{BASE_URL}/groups/{group_id}/regenerate-code', headers=headers)
    print(f"Regenerate Code: {resp.status_code}")
    new_code = resp.json()['invite_code']
    if new_code == invite_code:
        print("Error: Code did not change")
        
    # 7. Delete Group
    print("Deleting group...")
    resp = requests.delete(f'{BASE_URL}/groups/{group_id}', headers=headers)
    print(f"Delete Group: {resp.status_code}")
    
    # Verify deletion
    resp = requests.get(f'{BASE_URL}/groups/{group_id}', headers=headers)
    if resp.status_code != 403 and resp.status_code != 500: # Should probably be 403 (not member) or 404 if we handled that
        print(f"Warning: Get deleted group returned {resp.status_code}")
        
    print("Test Complete")

if __name__ == '__main__':
    test_groups()
