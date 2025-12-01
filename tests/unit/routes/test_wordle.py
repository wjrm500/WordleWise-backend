import pytest
import datetime
from unittest.mock import patch, MagicMock

@pytest.fixture
def auth_client(client, db):
    user = db.register_user("wordleuser", "password", "Wordle User")
    login_resp = client.post('/login', json={'username': 'wordleuser', 'password': 'password'})
    token = login_resp.json['access_token']
    return client, {'Authorization': f'Bearer {token}'}

def test_get_wordle_answer_success(auth_client):
    client, headers = auth_client
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <h2>What is today's Wordle answer?</h2>
                <p><strong>TESTS</strong></p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        resp = client.get(f'/wordle/answer?date={today}', headers=headers)
        
        assert resp.status_code == 200
        assert resp.json['success'] == True
        assert resp.json['answer'] == 'tests'

def test_get_wordle_answer_not_found(auth_client):
    client, headers = auth_client
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No answer here</body></html>"
        mock_get.return_value = mock_response
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        resp = client.get(f'/wordle/answer?date={today}', headers=headers)
        
        assert resp.status_code == 200
        assert resp.json['success'] == False
        assert 'error' in resp.json
