import pytest
from flask import json

@pytest.fixture
def auth_client(client, db):
    user = db.register_user("adminuser", "password", "Admin User")
    login_resp = client.post('/login', json={'username': 'adminuser', 'password': 'password'})
    token = login_resp.json['access_token']
    return client, {'Authorization': f'Bearer {token}'}

def test_execute_sql_success(auth_client):
    client, headers = auth_client
    
    sql = "SELECT 1"
    resp = client.post('/executeSql', json={'sql': sql}, headers=headers)
    
    assert resp.status_code == 200

def test_execute_sql_failure(auth_client):
    client, headers = auth_client
    
    sql = "SELECT * FROM non_existent_table"
    resp = client.post('/executeSql', json={'sql': sql}, headers=headers)
    
    assert resp.status_code == 500
    assert 'error' in resp.json or isinstance(resp.json, str)
