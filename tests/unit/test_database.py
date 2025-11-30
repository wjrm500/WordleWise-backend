import datetime
from unittest.mock import Mock
import freezegun
import pytest
from database.models.Score import Score, User

def test_get_scores(db):
    db.session = Mock()
    
    mock_users = [
        User(id=1, username="user1"),
        User(id=2, username="user2"),
    ]
    
    mock_scores_u1 = [
        Score(date=datetime.date(2022, 12, 31), score=2, user=mock_users[0]),
        Score(date=datetime.date(2023, 1, 1), score=3, user=mock_users[0]),
    ]
    
    query_mock = Mock()
    query_mock.all.return_value = mock_scores_u1
    query_mock.filter.return_value = query_mock
    db.session.query.return_value = query_mock

    # Test that the scores are returned in the correct format
    with freezegun.freeze_time("2023-01-03"):
        result = db.get_scores(user_id=1, scope_type='personal')
        expected_result = [
            {
                "start_of_week": "2022-12-26",
                "data": {
                    "2022-12-26": {},
                    "2022-12-27": {},
                    "2022-12-28": {},
                    "2022-12-29": {},
                    "2022-12-30": {},
                    "2022-12-31": {
                        "user1": 2
                    },
                    "2023-01-01": {
                        "user1": 3
                    }
                }
            },
            {
                "start_of_week": "2023-01-02",
                "data": {
                    "2023-01-02": {},
                    "2023-01-03": {},
                    "2023-01-04": {},
                    "2023-01-05": {},
                    "2023-01-06": {},
                    "2023-01-07": {},
                    "2023-01-08": {}
                }
            },
        ]
        assert result == expected_result

        # Test that days and weeks are sorted correctly
        mock_scores_u1_reversed = list(reversed(mock_scores_u1))
        query_mock.all.return_value = mock_scores_u1_reversed
        result = db.get_scores(user_id=1, scope_type='personal')
        assert list(result[0]["data"].keys()) == sorted(result[0]["data"].keys())
        week_start_dates = [week["start_of_week"] for week in result]
        assert week_start_dates == sorted(week_start_dates)
    
    # Test that the scores are returned in the correct format when the current week is empty
    with freezegun.freeze_time("2023-01-09"):
        result = db.get_scores(user_id=1, scope_type='personal')
        expected_result = [
            {
                "start_of_week": "2022-12-26",
                "data": {
                    "2022-12-26": {},
                    "2022-12-27": {},
                    "2022-12-28": {},
                    "2022-12-29": {},
                    "2022-12-30": {},
                    "2022-12-31": {
                        "user1": 2
                    },
                    "2023-01-01": {
                        "user1": 3
                    }
                }
            },
            {
                "start_of_week": "2023-01-02",
                "data": {
                    "2023-01-02": {},
                    "2023-01-03": {},
                    "2023-01-04": {},
                    "2023-01-05": {},
                    "2023-01-06": {},
                    "2023-01-07": {},
                    "2023-01-08": {}
                }
            },
            {
                "start_of_week": "2023-01-09",
                "data": {
                    "2023-01-09": {},
                    "2023-01-10": {},
                    "2023-01-11": {},
                    "2023-01-12": {},
                    "2023-01-13": {},
                    "2023-01-14": {},
                    "2023-01-15": {}
                }
            },
        ]
        assert result == expected_result
    
        # Test that missing weeks are filled in
        mock_scores_gap = [
            Score(date=datetime.date(2023, 1, 1), score=3, user=mock_users[0]),
            Score(date=datetime.date(2023, 1, 9), score=4, user=mock_users[0]),
        ]
        query_mock.all.return_value = mock_scores_gap
        result = db.get_scores(user_id=1, scope_type='personal')
        expected_result = [
            {
                "start_of_week": "2022-12-26",
                "data": {
                    "2022-12-26": {},
                    "2022-12-27": {},
                    "2022-12-28": {},
                    "2022-12-29": {},
                    "2022-12-30": {},
                    "2022-12-31": {},
                    "2023-01-01": {
                        "user1": 3
                    }
                }
            },
            {
                "start_of_week": "2023-01-02",
                "data": {
                    "2023-01-02": {},
                    "2023-01-03": {},
                    "2023-01-04": {},
                    "2023-01-05": {},
                    "2023-01-06": {},
                    "2023-01-07": {},
                    "2023-01-08": {}
                }
            },
            {
                "start_of_week": "2023-01-09",
                "data": {
                    "2023-01-09": {
                        "user1": 4
                    },
                    "2023-01-10": {},
                    "2023-01-11": {},
                    "2023-01-12": {},
                    "2023-01-13": {},
                    "2023-01-14": {},
                    "2023-01-15": {}
                }
            },
        ]
        assert result == expected_result

def test_add_score(db):
    db.session = Mock()
    
    score_date = "2023-01-01"
    user_id = 1
    score_value = 3
    
    query_mock = Mock()
    query_mock.filter_by.return_value = query_mock
    query_mock.first.return_value = None
    db.session.query.return_value = query_mock

    db.add_score(score_date, user_id, score_value)

    db.session.add.assert_called_once()

    score = db.session.add.call_args[0][0]
    assert score.date == datetime.date(2023, 1, 1)
    assert score.user_id == 1
    assert score.score == 3

    db.session.commit.assert_called_once()

def test_get_users(db):
    db.session = Mock()
    
    mock_users = [
        User(id=1, username="user1"),
        User(id=2, username="user2"),
    ]
    db.session.query.return_value.all.return_value = mock_users

    result = db.get_users()

    assert result == mock_users
