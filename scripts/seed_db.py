import sys
import os
import argparse
import random
from datetime import date, timedelta
from dotenv import load_dotenv

# Add parent directory to path to allow imports from backend root
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

# Change working directory to backend root to ensure relative paths work
os.chdir(backend_dir)

from database.Database import Database
from database.models import User, Score, Group, GroupMember

load_dotenv()

def get_database_url():
    """Get database URL from environment or default."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        print("DATABASE_URL not found in environment, using default.")
        return 'sqlite:///wordlewise.db'
    return url

def confirm_action(message):
    """Ask user for confirmation."""
    response = input(f"{message} (y/N): ").lower()
    return response == 'y'

def clear_data(db):
    """Clear existing data and recreate tables to ensure schema is up to date."""
    try:
        print("Recreating database schema...")
        from database.models.base import Base
        Base.metadata.drop_all(db.engine)
        Base.metadata.create_all(db.engine)
        print("Schema recreated successfully.")
    except Exception as e:
        print(f"Error recreating schema: {e}")
        raise

def create_users(db):
    """Create initial users."""
    users_data = [
        {"username": "wjrm500", "password": "password", "forename": "Will"},
        {"username": "kjem500", "password": "password", "forename": "Kate"},
        {"username": "jtrm500", "password": "password", "forename": "Jasper"}
    ]
    
    created_users = {}
    print("Creating users...")
    for u_data in users_data:
        user = db.register_user(u_data["username"], u_data["password"], u_data["forename"])
        if user:
            created_users[u_data["username"]] = user
            print(f"  - Created user: {u_data['username']} ({u_data['forename']})")
        else:
            print(f"  - Failed to create user: {u_data['username']}")
            
    return created_users

def create_groups(db, users):
    """Create groups and add members."""
    will = users.get("wjrm500")
    kate = users.get("kjem500")
    jasper = users.get("jtrm500")
    
    if not will:
        print("Error: User 'wjrm500' (Will) not found. Cannot create groups.")
        return

    print("Creating groups...")
    
    # Group 1: Will & Kate
    if kate:
        group_wk = db.create_group("Will & Kate", will.id, include_historical=True)
        if group_wk:
            db.join_group(group_wk.id, kate.id)
            print(f"  - Created group: '{group_wk.name}' with members Will, Kate")

    # Group 2: All Users
    if kate and jasper:
        group_all = db.create_group("All Users", will.id, include_historical=True)
        if group_all:
            db.join_group(group_all.id, kate.id)
            db.join_group(group_all.id, jasper.id)
            print(f"  - Created group: '{group_all.name}' with members Will, Kate, Jasper")

def add_scores(db, users):
    """Add random scores for users over the last 30 days."""
    print("Adding scores...")
    today = date.today()
    start_date = today - timedelta(days=30)
    
    # Define score weights for a realistic distribution
    # 1: 1%, 2: 5%, 3: 30%, 4: 40%, 5: 15%, 6: 5%, X: 4%
    weights = [1, 5, 30, 40, 15, 5, 4]
    options = [1, 2, 3, 4, 5, 6, None]

    current_date = start_date
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        
        for username, user in users.items():
            # Randomly skip some days (80% chance to play)
            if random.random() > 0.2:
                score_val = random.choices(options, weights=weights)[0]
                if score_val:
                    db.add_score(date_str, user.id, score_val)
        
        current_date += timedelta(days=1)
    print("  - Added sample scores for the last 30 days.")

def seed_database():
    parser = argparse.ArgumentParser(description="Seed the database with test data.")
    parser.add_argument("--force", action="store_true", help="Force execution without confirmation (required in production).")
    args = parser.parse_args()

    flask_env = os.environ.get('FLASK_ENV', 'production')
    is_production = flask_env == 'production'

    print(f"Environment: {flask_env}")

    if is_production and not args.force:
        print("ERROR: You are running in a PRODUCTION environment.")
        print("This script will wipe all data. Use --force to proceed.")
        sys.exit(1)

    if not args.force:
        # Check if database file exists
        if os.path.exists('wordlewise.db'):
            print("WARNING: This script will DELETE ALL DATA in the database.")
            if not confirm_action("Are you sure you want to continue?"):
                print("Operation cancelled.")
                sys.exit(0)
        else:
            print("Database file not found. Creating new database...")

    db_url = get_database_url()
    db = Database(db_url)

    try:
        clear_data(db)
        users = create_users(db)
        create_groups(db, users)
        add_scores(db, users)
        print("\nSeeding complete!")
    except Exception as e:
        print(f"\nAn error occurred during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_database()
