from database.Database import Database
from database.models import User, Score, Group, GroupMember
from datetime import date, timedelta
import random

import os
from dotenv import load_dotenv

load_dotenv()

def seed_database():
    print("Seeding database...")
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment, using default.")
        database_url = 'sqlite:///wordlewise.db'
        
    db = Database(database_url)
    
    # 1. Clear existing data (optional, but good for a fresh start)
    # Be careful with this in production!
    try:
        db.session.query(Score).delete()
        db.session.query(GroupMember).delete()
        db.session.query(Group).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("Cleared existing data.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data: {e}")
        return

    # 2. Create Users
    users = [
        {"username": "wjrm500", "password": "password", "forename": "Will"},
        {"username": "kjem500", "password": "password", "forename": "Kate"},
        {"username": "testuser", "password": "password", "forename": "Tester"}
    ]
    
    created_users = {}
    
    for u_data in users:
        user = db.register_user(u_data["username"], u_data["password"], u_data["forename"])
        if user:
            created_users[u_data["username"]] = user
            print(f"Created user: {u_data['username']}")
        else:
            print(f"Failed to create user: {u_data['username']}")

    # 3. Create a Group
    will = created_users.get("wjrm500")
    kate = created_users.get("kjem500")
    
    if will and kate:
        group = db.create_group("Will & Kate", will.id, include_historical=True)
        if group:
            print(f"Created group: {group.name} (Invite Code: {group.invite_code})")
            # Add Kate to group
            db.join_group(group.id, kate.id)
            print(f"Added Kate to group.")

    # 4. Add Scores
    # Generate scores for the last 30 days
    today = date.today()
    start_date = today - timedelta(days=30)
    
    current_date = start_date
    while current_date <= today:
        # Will's score
        if will:
            score_val = random.choices([1, 2, 3, 4, 5, 6, None], weights=[1, 5, 30, 40, 15, 5, 4])[0]
            if score_val:
                db.add_score(current_date.strftime("%Y-%m-%d"), will.id, score_val)
        
        # Kate's score
        if kate:
            score_val = random.choices([1, 2, 3, 4, 5, 6, None], weights=[2, 8, 35, 35, 15, 3, 2])[0]
            if score_val:
                db.add_score(current_date.strftime("%Y-%m-%d"), kate.id, score_val)
                
        current_date += timedelta(days=1)
        
    print("Added sample scores.")
    
    # Verification
    print("\nVerifying scores...")
    for username, user in created_users.items():
        count = db.session.query(Score).filter_by(user_id=user.id).count()
        print(f"User {username}: {count} scores")
        
    print("Seeding complete!")

if __name__ == "__main__":
    seed_database()
