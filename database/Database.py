from collections import defaultdict
import datetime
import hashlib
from typing import List
import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session

from database.models import Base
from database.models.Score import Score
from database.models.User import User

class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_engine(self.database_url, echo = False)
        Base.metadata.create_all(self.engine, checkfirst = True)
        self.session: Session = scoped_session(sessionmaker(bind = self.engine))
        self.timezone = None
    
    def execute(self, sql) -> None:
        self.session.execute(sql)
        self.session.commit()
    
    def set_timezone(self, timezone) -> None:
        if timezone not in pytz.all_timezones:
            raise Exception('Invalid timezone')
        self.timezone = timezone
    
    def today(self) -> datetime.date:
        if self.timezone is None:
            raise Exception('No timezone has been set')
        return datetime.datetime.now(pytz.timezone(self.timezone)).date()
    
    def login(self, username: str, password: str) -> User:
        user = self.session.query(User).filter_by(username = username).first()
        if user is not None:
            hash_to_match = user.password_hash
            if hashlib.md5(password.encode()).hexdigest() == hash_to_match:
                return user
            raise Exception('Password incorrect')
        raise Exception('User does not exist')
        
    def get_scores(self) -> List:
        all_scores_dict = {}
        for score in self.session.query(Score).all():
            score: Score
            score_date: datetime.date = score.date
            start_of_week = score_date - datetime.timedelta(days=score_date.weekday())
            if start_of_week not in all_scores_dict:
                all_scores_dict[start_of_week] = {
                    "start_of_week": str(start_of_week),
                    "data": {
                        str(start_of_week + datetime.timedelta(days = i)): {} for i in range(7)
                    }
                }
            all_scores_dict[start_of_week]["data"][str(score_date)][score.user.username] = score.score
        for k in all_scores_dict.keys():
            all_scores_dict[k]["data"] = dict(sorted(all_scores_dict[k]["data"].items(), key = lambda x: x[0]))
        return [x[1] for x in sorted(all_scores_dict.items(), key = lambda x: x[0])]
    
    def add_score(self, date: str, user_id: int, score: int) -> None:
        self.session.add(
            Score(
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date(),
                user_id = user_id,
                score = score
            )
        )
        self.session.commit()

    def get_players(self) -> List[User]:
        return self.session.query(User).all()