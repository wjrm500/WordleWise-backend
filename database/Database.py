import datetime
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from database.models import Base
from database.models.Day import Day
from database.models.User import User

class Database:
    def __init__(self, database_url: str) -> None:
        self.created_at = datetime.datetime.now()
        self.database_url = database_url
        self.engine = create_engine(self.database_url, echo = False)
        Base.metadata.create_all(self.engine, checkfirst = True)
        self.session = scoped_session(sessionmaker(bind = self.engine))
    
    def login(self, username: str, password: str):
        user = self.session.query(User).filter_by(username = username).first()
        if user is not None:
            hash_to_match = user.password_hash
            if hashlib.md5(password.encode()).hexdigest() == hash_to_match:
                return
            raise Exception('Password incorrect')
        raise Exception('User does not exist')
        
    def get_data(self):
        all_days = []
        for day in self.session.query(Day).all():
            all_days.append({
                "Date": day.date,
                "Kate": day.kate_score,
                "Will": day.will_score
            })
        all_days = sorted(all_days, key = lambda x: x['Date'])
        all_days_dict = {str(x['Date']): x for x in all_days}
        earliest_date = all_days[0]['Date']
        earliest_date_weekday = earliest_date.weekday()
        start_date = earliest_date - datetime.timedelta(days = earliest_date_weekday)
        all_weeks = []
        while start_date <= datetime.date.today():
            single_week = []
            for _ in range(7):
                str_start_date = str(start_date)
                if str_start_date in all_days_dict:
                    data = all_days_dict[str_start_date]
                    kate_score = data['Kate']
                    will_score = data['Will']
                else:
                    future = start_date >= datetime.date.today()
                    kate_score = will_score = None if future else 8
                single_week.append({
                    'Date': str_start_date,
                    'Kate': kate_score,
                    'Will': will_score
                })
                start_date = start_date + datetime.timedelta(days = 1)
            all_weeks.append(single_week)
        return all_weeks
    
    def add_score(self, data):
        day = self.session.query(Day).filter_by(date = data['date']).first()
        if day is not None:
            if data['user'] == 'wjrm500':
                day.will_score = data['score']
            elif data['user'] == 'kjem500':
                day.kate_score = data['score']
        else:
            input_date = datetime.datetime.strptime(data['date'], "%Y-%m-%d").date()
            opponent_score = None if input_date == datetime.date.today() else 8
            if data['user'] == 'wjrm500':
                day = Day(
                    date = input_date,
                    will_score = data['score'],
                    kate_score = opponent_score
                )
            elif data['user'] == 'kjem500':
                day = Day(
                    date = input_date,
                    will_score = opponent_score,
                    kate_score = data['score']
                )
            self.session.add(day)
        self.session.commit()