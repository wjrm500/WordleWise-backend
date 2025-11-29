from collections import defaultdict
import datetime
import hashlib
from typing import List
import pytz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from database.models.base import Base
from database.models.Score import Score
from database.models.User import User
from database.models.Group import Group
from database.models.GroupMember import GroupMember
from utilities.invite_code import generate_invite_code


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        
        # Configure engine with proper pool settings
        if 'sqlite' in database_url:
            # SQLite doesn't support real connection pooling
            # Use StaticPool for SQLite to avoid threading issues
            self.engine = create_engine(
                self.database_url,
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # For other databases (PostgreSQL, MySQL, etc.)
            self.engine = create_engine(
                self.database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
        
        Base.metadata.create_all(self.engine, checkfirst=True)
        self.session: Session = scoped_session(sessionmaker(bind=self.engine))
        self.timezone = None
    
    def execute(self, sql) -> None:
        self.session.execute(text(sql))
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
        user = self.session.query(User).filter_by(username=username).first()
        if user is not None:
            hash_to_match = user.password_hash
            if hashlib.md5(password.encode()).hexdigest() == hash_to_match:
                return user
            raise Exception('Password incorrect')
        raise Exception('User does not exist')

    def register_user(self, username, password, forename):
        if self.session.query(User).filter_by(username=username).first():
            raise Exception("Username already exists")
            
        password_hash = hashlib.md5(password.encode()).hexdigest()
        new_user = User(username=username, password_hash=password_hash, forename=forename)
        self.session.add(new_user)
        self.session.commit()
        return new_user
    
    def get_user_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter_by(id=user_id).first()
        
    def get_scores(self, user_id: int, scope_type: str, group_id: int = None) -> List:
        # Determine query based on scope
        query = self.session.query(Score)
        
        group_created_date = None
        
        if scope_type == 'personal':
            query = query.filter(Score.user_id == user_id)
        elif scope_type == 'group' and group_id:
            # Get group members
            members = self.session.query(GroupMember).filter_by(group_id=group_id).all()
            member_ids = [m.user_id for m in members]
            query = query.filter(Score.user_id.in_(member_ids))
            
            # Check historical data setting
            group = self.get_group(group_id)
            if group and not group.include_historical_data:
                group_created_date = group.created_at.date()
                # Filter scores to only those on or after group creation
                query = query.filter(Score.date >= group_created_date)
        
        # Execute query
        scores = query.all()
        
        # Process scores into weeks
        all_scores_dict = {}
        for score in scores:
            score: Score
            score_date: datetime.date = score.date
            week_start_date = score_date - datetime.timedelta(days=score_date.weekday())
            if week_start_date not in all_scores_dict:
                all_scores_dict[week_start_date] = {
                    "start_of_week": str(week_start_date),
                    "data": {
                        str(week_start_date + datetime.timedelta(days=i)): {} for i in range(7)
                    }
                }
            all_scores_dict[week_start_date]["data"][str(score_date)][score.user.username] = score.score
        
        # Determine the earliest week to show
        today = datetime.date.today()
        current_week_start = today - datetime.timedelta(days=today.weekday())
        
        if group_created_date:
            # When historical data is OFF, start from the week containing group creation
            earliest_week_start = group_created_date - datetime.timedelta(days=group_created_date.weekday())
        elif all_scores_dict:
            # When historical data is ON, start from earliest score
            earliest_week_start = min(all_scores_dict.keys())
        else:
            # No scores at all, just show current week
            earliest_week_start = current_week_start
        
        # Fill in missing weeks from earliest to current
        week_cursor = earliest_week_start
        while week_cursor <= current_week_start:
            if week_cursor not in all_scores_dict:
                all_scores_dict[week_cursor] = {
                    "start_of_week": str(week_cursor),
                    "data": {
                        str(week_cursor + datetime.timedelta(days=i)): {} for i in range(7)
                    }
                }
            week_cursor += datetime.timedelta(days=7)
        
        # Add group_created_at metadata to each week if historical data is off
        if group_created_date:
            for week_start, week_data in all_scores_dict.items():
                week_data["group_created_at"] = str(group_created_date)

        # Sort the weeks
        all_scores_dict = dict(sorted(all_scores_dict.items(), key=lambda x: x[0]))

        # Sort the days within each week
        for week in all_scores_dict.values():
            week["data"] = dict(sorted(week["data"].items(), key=lambda x: x[0]))

        # Return as a list
        return list(all_scores_dict.values())
    
    def add_score(self, date: str, user_id: int, score: int) -> None:
        # Upsert logic
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        existing_score = self.session.query(Score).filter_by(user_id=user_id, date=date_obj).first()
        
        if existing_score:
            existing_score.score = score
        else:
            new_score = Score(
                date=date_obj,
                user_id=user_id,
                score=score
            )
            self.session.add(new_score)
        self.session.commit()

    def get_users(self, user_id: int = None, scope_type: str = None, group_id: int = None) -> List[User]:
        query = self.session.query(User)
        
        if scope_type == 'personal' and user_id:
            query = query.filter(User.id == user_id)
        elif scope_type == 'group' and group_id:
            query = query.join(GroupMember).filter(GroupMember.group_id == group_id)
            
        return query.all()

    # Group Management Methods
    def get_group(self, group_id: int) -> Group:
        return self.session.query(Group).filter_by(id=group_id).first()

    def get_user_groups(self, user_id: int) -> List[Group]:
        return self.session.query(Group).join(GroupMember).filter(GroupMember.user_id == user_id).all()

    def get_group_by_invite_code(self, invite_code: str) -> Group:
        return self.session.query(Group).filter_by(invite_code=invite_code).first()

    def create_group(self, name, user_id, include_historical=True):
        invite_code = generate_invite_code()
        while self.session.query(Group).filter_by(invite_code=invite_code).first():
            invite_code = generate_invite_code()
            
        new_group = Group(
            name=name,
            invite_code=invite_code,
            created_by_user_id=user_id,
            include_historical_data=1 if include_historical else 0
        )
        self.session.add(new_group)
        self.session.flush()  # Get ID
        
        # Add creator as admin
        member = GroupMember(
            group_id=new_group.id,
            user_id=user_id,
            role='admin'
        )
        self.session.add(member)
        self.session.commit()
        return new_group

    def join_group(self, group_id, user_id):
        # Check capacity
        count = self.session.query(GroupMember).filter_by(group_id=group_id).count()
        if count >= 4:
            return False, "Group is full (maximum 4 members)"
            
        member = GroupMember(group_id=group_id, user_id=user_id, role='member')
        self.session.add(member)
        self.session.commit()
        return True, "Joined successfully"

    def leave_group(self, group_id, user_id):
        member = self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).first()
        if not member:
            return False, "Not a member"
            
        # Check if last admin
        if member.role == 'admin':
            admin_count = self.session.query(GroupMember).filter_by(group_id=group_id, role='admin').count()
            if admin_count == 1:
                # Check if other members exist
                member_count = self.session.query(GroupMember).filter_by(group_id=group_id).count()
                if member_count > 1:
                    return False, "Cannot leave as last admin. Promote someone else first."
        
        self.session.delete(member)
        
        user = self.get_user_by_id(user_id)
        if user and user.default_group_id == group_id:
            user.default_group_id = None
        
        remaining = self.session.query(GroupMember).filter_by(group_id=group_id).count()
        if remaining == 0:
            self.session.query(Group).filter_by(id=group_id).delete()
            
        self.session.commit()
        return True, "Left successfully"

    def get_group_members(self, group_id):
        return self.session.query(User).join(GroupMember).filter(GroupMember.group_id == group_id).all()
        
    def get_group_member_details(self, group_id):
        return self.session.query(User, GroupMember).join(GroupMember).filter(GroupMember.group_id == group_id).all()

    def update_group(self, group_id, **kwargs):
        group = self.get_group(group_id)
        if group:
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            self.session.commit()
            return True
        return False

    def remove_member(self, group_id, user_id):
        user = self.get_user_by_id(user_id)
        if user and user.default_group_id == group_id:
            user.default_group_id = None
        
        self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).delete()
        self.session.commit()

    def update_member_role(self, group_id, user_id, role):
        member = self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).first()
        if member:
            member.role = role
            self.session.commit()
            return True
        return False

    def regenerate_invite_code(self, group_id):
        group = self.get_group(group_id)
        if group:
            new_code = generate_invite_code()
            while self.session.query(Group).filter_by(invite_code=new_code).first():
                new_code = generate_invite_code()
            group.invite_code = new_code
            self.session.commit()
            return new_code
        return None

    def get_membership(self, group_id, user_id):
        return self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).first()

    def delete_score(self, date: str, user_id: int) -> None:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        self.session.query(Score).filter_by(user_id=user_id, date=date_obj).delete()
        self.session.commit()

    def delete_group(self, group_id: int) -> None:
        self.session.query(User).filter_by(default_group_id=group_id).update(
            {User.default_group_id: None}
        )
        
        group = self.get_group(group_id)
        if group:
            self.session.delete(group)
            self.session.commit()

    def set_default_scope(self, user_id: int, group_id: int = None) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if group_id is not None:
            membership = self.get_membership(group_id, user_id)
            if not membership:
                return False
        
        user.default_group_id = group_id
        self.session.commit()
        return True
