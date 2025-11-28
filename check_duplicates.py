"""
Script to check for duplicate scores before adding UNIQUE constraint.
Run this before modifying the Score model.
"""
from database.Database import Database

def check_for_duplicates():
    db = Database(database_url='sqlite:///wordlewise.db')
    
    # Query for duplicates
    query = """
        SELECT date, user_id, COUNT(*) as count
        FROM score
        GROUP BY date, user_id
        HAVING COUNT(*) > 1
    """
    
    result = db.session.execute(query)
    duplicates = result.fetchall()
    
    if duplicates:
        print("⚠️  WARNING: Found duplicate scores!")
        print("\nDuplicate entries:")
        for row in duplicates:
            print(f"  Date: {row[0]}, User ID: {row[1]}, Count: {row[2]}")
        print("\n❌ Cannot add UNIQUE constraint until duplicates are resolved.")
        print("Please review and delete duplicate entries manually.")
        return False
    else:
        print("✅ No duplicate scores found!")
        print("Safe to add UNIQUE constraint to Score model.")
        return True

if __name__ == '__main__':
    check_for_duplicates()
