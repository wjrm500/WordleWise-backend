import datetime
import pytest
import freezegun
from database.models.User import User
from database.models.Score import Score

def test_get_scores_structure(db):
    """Test that get_scores returns the correct nested structure."""
    # Setup
    user = db.register_user("user1", "pass", "User One")
    
    # Add scores
    with freezegun.freeze_time("2023-01-01"): # Sunday
        db.add_score("2022-12-31", user.id, 2) # Saturday
        db.add_score("2023-01-01", user.id, 3) # Sunday

    # Test
    with freezegun.freeze_time("2023-01-03"): # Tuesday
        result = db.get_scores(user_id=user.id, scope_type='personal')
        
        assert len(result) == 2 # Two weeks
        
        # Week 1: Dec 26 - Jan 1
        week1 = result[0]
        assert week1["start_of_week"] == "2022-12-26"
        assert week1["data"]["2022-12-31"]["user1"] == 2
        assert week1["data"]["2023-01-01"]["user1"] == 3
        
        # Week 2: Jan 2 - Jan 8
        week2 = result[1]
        assert week2["start_of_week"] == "2023-01-02"
        # No scores in week 2 yet

def test_get_scores_sorting(db):
    """Test that weeks and days are sorted correctly."""
    user = db.register_user("user1", "pass", "User One")
    
    # Add scores in random order
    db.add_score("2023-01-01", user.id, 3)
    db.add_score("2022-12-31", user.id, 2)
    
    with freezegun.freeze_time("2023-01-03"):
        result = db.get_scores(user_id=user.id, scope_type='personal')
        
        # Check week sorting
        week_starts = [w["start_of_week"] for w in result]
        assert week_starts == sorted(week_starts)
        
        # Check day sorting within week
        for week in result:
            days = list(week["data"].keys())
            assert days == sorted(days)

def test_get_scores_gap_filling(db):
    """Test that missing weeks are filled in."""
    user = db.register_user("user1", "pass", "User One")
    
    db.add_score("2023-01-01", user.id, 1) # Week 1
    db.add_score("2023-01-15", user.id, 2) # Week 3
    
    with freezegun.freeze_time("2023-01-16"):
        result = db.get_scores(user_id=user.id, scope_type='personal')
        
        # Should have 3 weeks: Dec 26, Jan 2, Jan 9
        # Wait, Jan 15 is Sunday, so it belongs to week starting Jan 9
        # Week 1: Dec 26 - Jan 1
        # Week 2: Jan 2 - Jan 8 (Empty)
        # Week 3: Jan 9 - Jan 15
        # Week 4: Jan 16 - Jan 22 (Current week)
        
        assert len(result) == 4
        assert result[0]["start_of_week"] == "2022-12-26"
        assert result[1]["start_of_week"] == "2023-01-02" # Gap filled
        assert result[2]["start_of_week"] == "2023-01-09"
        assert result[3]["start_of_week"] == "2023-01-16"

def test_add_score(db):
    """Test adding and updating scores."""
    user = db.register_user("user1", "pass", "User One")
    
    # Add new score
    db.add_score("2023-01-01", user.id, 3)
    
    scores = db.session.query(Score).filter_by(user_id=user.id).all()
    assert len(scores) == 1
    assert scores[0].score == 3
    
    # Update existing score
    db.add_score("2023-01-01", user.id, 5)
    
    scores = db.session.query(Score).filter_by(user_id=user.id).all()
    assert len(scores) == 1
    assert scores[0].score == 5

def test_get_users(db):
    """Test user retrieval."""
    u1 = db.register_user("user1", "pass", "User One")
    u2 = db.register_user("user2", "pass", "User Two")
    
    users = db.get_users()
    assert len(users) == 2
    assert any(u.username == "user1" for u in users)
    assert any(u.username == "user2" for u in users)
