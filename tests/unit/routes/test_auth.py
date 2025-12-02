import pytest
from flask import json

def test_login_success(client, db):
    """Test successful login."""
    db.register_user("testuser", "password", "Test User")
    
    resp = client.post('/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    assert resp.status_code == 200
    assert resp.json['success'] == True
    assert resp.json['access_token'] is not None
    assert resp.json['user']['username'] == 'testuser'

def test_login_failure_wrong_password(client, db):
    """Test login with incorrect password."""
    db.register_user("testuser", "password", "Test User")
    
    resp = client.post('/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert resp.status_code == 200 # API returns 200 with success: False
    assert resp.json['success'] == False
    assert resp.json['error'] == 'Password incorrect'

def test_login_failure_user_not_found(client, db):
    """Test login with non-existent user."""
    resp = client.post('/login', json={
        'username': 'nonexistent',
        'password': 'password'
    })
    
    assert resp.status_code == 200
    assert resp.json['success'] == False
    assert resp.json['error'] == 'User does not exist'

def test_register_success(client, db):
    """Test successful registration."""
    resp = client.post('/register', json={
        'username': 'newuser',
        'password': 'password',
        'forename': 'New User'
    })
    
    assert resp.status_code == 200
    assert resp.json['success'] == True
    assert resp.json['user']['username'] == 'newuser'
    
    # Verify user in DB
    user = db.get_user_by_id(resp.json['user']['id'])
    assert user is not None

def test_register_duplicate_username(client, db):
    """Test registration with existing username."""
    db.register_user("existing", "password", "ExistUser")
    
    resp = client.post('/register', json={
        'username': 'existing',
        'password': 'password',
        'forename': 'Another'
    })
    
    assert resp.status_code == 400
    assert resp.json['success'] == False
    assert 'Username already exists' in resp.json['error']

def test_register_missing_fields(client):
    """Test registration with missing fields."""
    resp = client.post('/register', json={
        'username': 'incomplete'
    })
    
    assert resp.status_code == 400
    assert resp.json['success'] == False

def test_register_username_limit(client):
    """Test that registration fails if username is too long (>12 chars)"""
    response = client.post('/register', json={
        'username': 'a' * 13,
        'password': 'password123',
        'forename': 'Test'
    })
    assert response.status_code == 400
    assert b'Username must be 12 characters or less' in response.data

def test_register_forename_limit(client):
    """Test that registration fails if forename is too long (>10 chars)"""
    response = client.post('/register', json={
        'username': 'validuser',
        'password': 'password123',
        'forename': 'a' * 11
    })
    assert response.status_code == 400
    assert b'Display name must be 10 characters or less' in response.data
