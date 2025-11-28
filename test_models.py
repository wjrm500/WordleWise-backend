from database.Database import Database
from database.models import User, Group, GroupMember
import os

# Use a temporary test database
TEST_DB = 'test_wordlewise.db'
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

db = Database(database_url=f'sqlite:///{TEST_DB}')

print("Creating tables...")
# Tables are created in Database.__init__ via Base.metadata.create_all

print("Creating user...")
user = User(username='testuser', password_hash='hash', forename='Test')
db.session.add(user)
db.session.commit()
print(f"User created: {user.id}")

print("Creating group...")
group = db.create_group("Test Group", user.id)
print(f"Group created: {group.name} (ID: {group.id}, Code: {group.invite_code})")

print("Verifying membership...")
members = db.get_user_groups(user.id)
print(f"User is in {len(members)} groups")
assert len(members) == 1
assert members[0].name == "Test Group"

member_details = db.get_group_member_details(group.id)
print(f"Group has {len(member_details)} members")
assert len(member_details) == 1
assert member_details[0][1].role == 'admin'

print("Test complete!")
