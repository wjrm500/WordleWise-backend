from database.Database import Database
from database.models import User, Group
import os
from dotenv import load_dotenv
import json

load_dotenv()

def debug_scores():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = 'sqlite:///wordlewise.db'
    
    db = Database(database_url)
    
    # Get users
    will = db.session.query(User).filter_by(username='wjrm500').first()
    kate = db.session.query(User).filter_by(username='kjem500').first()
    
    if not will or not kate:
        print("Users not found")
        return

    # Get group
    group = db.session.query(Group).filter_by(name="Will & Kate").first()
    if not group:
        print("Group not found")
        return
        
    print(f"Group: {group.name}, ID: {group.id}, Include Historical: {group.include_historical_data}")
    
    # Check group members
    members = db.session.query(GroupMember).filter_by(group_id=group.id).all()
    print("Members:", [m.user.username for m in members])

    # Get scores for Will in Group scope
    print("\nFetching scores for wjrm500 in group scope...")
    scores = db.get_scores(will.id, 'group', group.id)
    
    # Inspect a few days
    count_will = 0
    count_kate = 0
    
    for week in scores:
        for date, day_data in week['data'].items():
            if 'wjrm500' in day_data:
                count_will += 1
            if 'kjem500' in day_data:
                count_kate += 1
                
    print(f"Total days with Will's score: {count_will}")
    print(f"Total days with Kate's score: {count_kate}")
    
    # Print sample day
    if scores:
        sample_week = scores[-1] # Last week
        print("\nSample Week Data (Last Week):")
        print(json.dumps(sample_week, indent=2))

from database.models import GroupMember

if __name__ == "__main__":
    debug_scores()
