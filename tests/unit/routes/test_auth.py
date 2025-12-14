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

def test_login_rate_limiting(client, db):
    """Test that login rate limiting works (5 attempts per minute)."""
    db.register_user("testuser", "password", "Test User")

    # Make 5 login attempts (should all succeed or fail based on credentials)
    for i in range(5):
        resp = client.post('/login', json={
            'username': 'testuser',
            'password': 'password'
        })
        assert resp.status_code == 200

    # 6th attempt should be rate limited
    resp = client.post('/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    assert resp.status_code == 429
    assert 'Retry-After' in resp.headers

def test_register_rate_limiting(client):
    """Test that registration rate limiting works (10 attempts per hour)."""
    # Make 10 registration attempts
    for i in range(10):
        resp = client.post('/register', json={
            'username': f'user{i}',
            'password': 'password',
            'forename': f'User{i}'
        })
        # Should succeed (200) or fail with validation error (400)
        assert resp.status_code in [200, 400]

    # 11th attempt should be rate limited
    resp = client.post('/register', json={
        'username': 'user11',
        'password': 'password',
        'forename': 'User11'
    })
    assert resp.status_code == 429
    assert 'Retry-After' in resp.headers

def test_register_password_too_short(client):
    """Test that registration fails if password is less than 8 characters"""
    response = client.post('/register', json={
        'username': 'validuser',
        'password': 'short',
        'forename': 'Test'
    })
    assert response.status_code == 400
    assert response.json['success'] == False
    assert response.json['error'] == 'Password must be at least 8 characters long'

def test_register_password_exactly_8_chars(client, db):
    """Test that registration succeeds with password exactly 8 characters"""
    response = client.post('/register', json={
        'username': 'validuser',
        'password': '12345678',
        'forename': 'Test'
    })
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['user']['username'] == 'validuser'

def test_register_password_longer_than_8_chars(client, db):
    """Test that registration succeeds with password longer than 8 characters"""
    response = client.post('/register', json={
        'username': 'validuser',
        'password': 'verylongpassword123',
        'forename': 'Test'
    })
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['user']['username'] == 'validuser'
