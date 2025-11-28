import hashlib
from database.Database import Database
from database.models.User import User
import os

# Assuming default sqlite path if not in env, but better to check main.py
# For now, let's try to load from .env or hardcode what we see in main.py
# If main.py uses python-dotenv, we should too.

db_url = 'sqlite:///manual_test.db' # Matches main.py
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                db_url = line.strip().split('=', 1)[1]

print(f"Connecting to {db_url}")
print(f"Absolute path: {os.path.abspath('wordlewise.db')}")
db = Database(db_url)

username = 'wjrm500'
password = 'password'
password_hash = hashlib.md5(password.encode()).hexdigest()

user = db.session.query(User).filter_by(username=username).first()
if user:
    print(f"Updating password for {username}")
    user.password_hash = password_hash
    db.session.commit()
    print("Password updated.")
else:
    print(f"User {username} not found. Creating...")
    user = User(username=username, password_hash=password_hash, forename='Will')
    db.session.add(user)
    db.session.commit()
    print("User created.")
