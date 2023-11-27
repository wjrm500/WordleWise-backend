import sys

sys.path.append("../..")

import datetime
import unittest
from unittest.mock import Mock

import freezegun

from database.Database import Database
from database.models.Score import Score, User

class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.database = Database(database_url="sqlite:///:memory:")
        self.database.session = Mock()
    
    def mock_users(self):
        return [
            User(id=1, username="user1"),
            User(id=2, username="user2"),
        ]

    def test_get_scores(self) -> None:
        mock_users = self.mock_users()
        mock_scores = [
            Score(date=datetime.date(2022, 12, 31), score=2, user=mock_users[0]),
            Score(date=datetime.date(2023, 1, 1), score=3, user=mock_users[0]),
            Score(date=datetime.date(2023, 1, 2), score=4, user=mock_users[1]),
        ]
        self.database.session.query.return_value.all.return_value = mock_scores

        # Test that the scores are returned in the correct format
        with freezegun.freeze_time("2023-01-03"):
            result = self.database.get_scores()
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
                        "2023-01-02": {
                            "user2": 4
                        },
                        "2023-01-03": {},
                        "2023-01-04": {},
                        "2023-01-05": {},
                        "2023-01-06": {},
                        "2023-01-07": {},
                        "2023-01-08": {}
                    }
                },
            ]
            self.assertEqual(result, expected_result)

            # Test that days and weeks are sorted correctly
            mock_scores = list(reversed(mock_scores))
            self.database.session.query.return_value.all.return_value = mock_scores
            result = self.database.get_scores()
            self.assertEqual(list(result[0]["data"].keys()), sorted(result[0]["data"].keys()))
            week_start_dates = [week["start_of_week"] for week in result]
            self.assertEqual(week_start_dates, sorted(week_start_dates))
        
        # Test that the scores are returned in the correct format when the current week is empty
        with freezegun.freeze_time("2023-01-09"):
            result = self.database.get_scores()
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
                        "2023-01-02": {
                            "user2": 4
                        },
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
            self.assertEqual(result, expected_result)
        
            # Test that missing weeks are filled in
            mock_scores = [
                Score(date=datetime.date(2023, 1, 1), score=3, user=mock_users[0]),
                Score(date=datetime.date(2023, 1, 9), score=4, user=mock_users[1]),
            ]
            self.database.session.query.return_value.all.return_value = mock_scores
            result = self.database.get_scores()
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
                            "user2": 4
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
            self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
