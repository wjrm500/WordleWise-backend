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
        today = self.today()
        all_days_dict = {}
        for score in self.session.query(Score).all():
            score: Score
            key = str(score.date)
            if key not in all_days_dict:
                all_days_dict[key] = {"Date": score.date}
            if score.user_id == 1:
                all_days_dict[key]["Will"] = score.score
            elif score.user_id == 2:
                all_days_dict[key]["Kate"] = score.score
        if len(all_days_dict) > 0:
            all_days_dict = dict(sorted(all_days_dict.items()))
            earliest_date = all_days_dict[min(all_days_dict)]["Date"]
        else:
            earliest_date = today
        earliest_date_weekday = earliest_date.weekday()
        start_date = earliest_date - datetime.timedelta(days = earliest_date_weekday)
        all_weeks = []
        while start_date <= today:
            single_week = []
            for _ in range(7):
                str_start_date = str(start_date)
                if str_start_date in all_days_dict:
                    data = all_days_dict[str_start_date]
                    kate_score = data.get('Kate')
                    will_score = data.get('Will')
                else:
                    kate_score = will_score = None
                single_week.append({
                    'Date': str_start_date,
                    'Kate': kate_score,
                    'Will': will_score
                })
                start_date = start_date + datetime.timedelta(days = 1)
            all_weeks.append(single_week)
        return all_weeks
    
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