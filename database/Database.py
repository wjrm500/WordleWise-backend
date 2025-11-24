import datetime
import hashlib
import secrets
import string
from typing import List, Optional

import pytz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, scoped_session

from database.models import Base
from database.models.Score import Score
from database.models.User import User
from database.models.Group import Group
from database.models.GroupMember import GroupMember


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_engine(self.database_url, echo=False)
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

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter_by(id=user_id).first()

    # =========================================================================
    # SCORE METHODS
    # =========================================================================

    def get_scores_for_users(
        self,
        user_ids: List[int],
        start_date: Optional[datetime.date] = None
    ) -> List:
        """
        Get scores for a list of users, optionally filtered by start date.
        Returns data in the weekly format expected by the frontend.
        """
        # Build query
        query = self.session.query(Score).filter(Score.user_id.in_(user_ids))
        if start_date:
            query = query.filter(Score.date >= start_date)

        # Get username mapping
        users = self.session.query(User).filter(User.id.in_(user_ids)).all()
        user_id_to_username = {u.id: u.username for u in users}

        # Build scores dict
        all_scores_dict = {}
        for score in query.all():
            score_date: datetime.date = score.date
            week_start_date = score_date - datetime.timedelta(days=score_date.weekday())
            if week_start_date not in all_scores_dict:
                all_scores_dict[week_start_date] = {
                    "start_of_week": str(week_start_date),
                    "data": {
                        str(week_start_date + datetime.timedelta(days=i)): {} for i in range(7)
                    }
                }
            username = user_id_to_username.get(score.user_id)
            if username:
                all_scores_dict[week_start_date]["data"][str(score_date)][username] = score.score

        if not all_scores_dict:
            # No scores found, return current week
            current_week_start = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
            if start_date and current_week_start < start_date:
                current_week_start = start_date - datetime.timedelta(days=start_date.weekday())
            return [{
                "start_of_week": str(current_week_start),
                "data": {
                    str(current_week_start + datetime.timedelta(days=i)): {} for i in range(7)
                }
            }]

        # Fill in missing weeks
        earliest_date = min(all_scores_dict.keys())
        if start_date:
            # Don't go earlier than start_date's week
            start_date_week = start_date - datetime.timedelta(days=start_date.weekday())
            if earliest_date < start_date_week:
                earliest_date = start_date_week

        while earliest_date <= datetime.date.today() - datetime.timedelta(days=7):
            if earliest_date not in all_scores_dict:
                all_scores_dict[earliest_date] = {
                    "start_of_week": str(earliest_date),
                    "data": {
                        str(earliest_date + datetime.timedelta(days=i)): {} for i in range(7)
                    }
                }
            earliest_date += datetime.timedelta(days=7)

        # Include the current week
        current_week_start_date = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
        if current_week_start_date not in all_scores_dict:
            all_scores_dict[current_week_start_date] = {
                "start_of_week": str(current_week_start_date),
                "data": {
                    str(current_week_start_date + datetime.timedelta(days=i)): {} for i in range(7)
                }
            }

        # Sort the weeks
        all_scores_dict = dict(sorted(all_scores_dict.items(), key=lambda x: x[0]))

        # Sort the days within each week
        for week in all_scores_dict.values():
            week["data"] = dict(sorted(week["data"].items(), key=lambda x: x[0]))

        return list(all_scores_dict.values())

    def get_scores(self) -> List:
        """Legacy method - gets all scores (used before groups)."""
        all_user_ids = [u.id for u in self.session.query(User).all()]
        return self.get_scores_for_users(all_user_ids)

    def add_score(self, date: str, user_id: int, score: int) -> None:
        """Add or update a score for a user on a given date."""
        score_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        # Check if score already exists for this user and date
        existing_score = self.session.query(Score).filter_by(
            date=score_date,
            user_id=user_id
        ).first()

        if existing_score:
            existing_score.score = score
        else:
            self.session.add(
                Score(
                    date=score_date,
                    user_id=user_id,
                    score=score
                )
            )
        self.session.commit()

    def get_users(self) -> List[User]:
        return self.session.query(User).all()

    # =========================================================================
    # GROUP METHODS
    # =========================================================================

    @staticmethod
    def generate_invite_code(length: int = 8) -> str:
        """Generate a random alphanumeric invite code."""
        # Use uppercase letters and digits, removing ambiguous characters
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '').replace('L', '')
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_group(
        self,
        name: str,
        creator_user_id: int,
        include_historical_data: bool = True
    ) -> Group:
        """Create a new group with the creator as admin."""
        # Generate unique invite code
        invite_code = self.generate_invite_code()
        while self.session.query(Group).filter_by(invite_code=invite_code).first():
            invite_code = self.generate_invite_code()

        group = Group(
            name=name,
            invite_code=invite_code,
            created_by_user_id=creator_user_id,
            include_historical_data=1 if include_historical_data else 0
        )
        self.session.add(group)
        self.session.flush()  # Get the ID

        # Add creator as admin
        membership = GroupMember(
            group_id=group.id,
            user_id=creator_user_id,
            role='admin'
        )
        self.session.add(membership)
        self.session.commit()

        return group

    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """Get a group by ID."""
        return self.session.query(Group).filter_by(id=group_id).first()

    def get_group_by_invite_code(self, invite_code: str) -> Optional[Group]:
        """Get a group by invite code (case-insensitive)."""
        return self.session.query(Group).filter(
            Group.invite_code.ilike(invite_code)
        ).first()

    def get_user_groups(self, user_id: int) -> List[dict]:
        """Get all groups a user is a member of."""
        memberships = self.session.query(GroupMember).filter_by(user_id=user_id).all()
        result = []
        for membership in memberships:
            group = membership.group
            member_count = self.session.query(GroupMember).filter_by(group_id=group.id).count()
            result.append({
                'id': group.id,
                'name': group.name,
                'member_count': member_count,
                'role': membership.role,
                'include_historical_data': bool(group.include_historical_data)
            })
        return result

    def get_group_details(self, group_id: int) -> Optional[dict]:
        """Get full group details including members."""
        group = self.get_group_by_id(group_id)
        if not group:
            return None

        members = []
        for membership in group.members:
            user = membership.user
            members.append({
                'id': user.id,
                'username': user.username,
                'forename': user.forename,
                'role': membership.role
            })

        return {
            'id': group.id,
            'name': group.name,
            'invite_code': group.invite_code,
            'include_historical_data': bool(group.include_historical_data),
            'created_at': group.created_at.isoformat() if group.created_at else None,
            'members': members
        }

    def get_group_membership(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        """Get a user's membership in a group."""
        return self.session.query(GroupMember).filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()

    def is_group_member(self, group_id: int, user_id: int) -> bool:
        """Check if a user is a member of a group."""
        return self.get_group_membership(group_id, user_id) is not None

    def is_group_admin(self, group_id: int, user_id: int) -> bool:
        """Check if a user is an admin of a group."""
        membership = self.get_group_membership(group_id, user_id)
        return membership is not None and membership.role == 'admin'

    def get_group_admin_count(self, group_id: int) -> int:
        """Get the number of admins in a group."""
        return self.session.query(GroupMember).filter_by(
            group_id=group_id,
            role='admin'
        ).count()

    def get_group_member_count(self, group_id: int) -> int:
        """Get the number of members in a group."""
        return self.session.query(GroupMember).filter_by(group_id=group_id).count()

    def update_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        include_historical_data: Optional[bool] = None
    ) -> Optional[Group]:
        """Update group settings."""
        group = self.get_group_by_id(group_id)
        if not group:
            return None

        if name is not None:
            group.name = name
        if include_historical_data is not None:
            group.include_historical_data = 1 if include_historical_data else 0

        self.session.commit()
        return group

    def delete_group(self, group_id: int) -> bool:
        """Delete a group and all its memberships."""
        group = self.get_group_by_id(group_id)
        if not group:
            return False

        self.session.delete(group)
        self.session.commit()
        return True

    def join_group(self, invite_code: str, user_id: int) -> dict:
        """
        Join a group via invite code.
        Returns dict with 'success', 'error', and optionally 'group'.
        """
        group = self.get_group_by_invite_code(invite_code)
        if not group:
            return {'success': False, 'error': 'Invalid invite code'}

        # Check if already a member
        if self.is_group_member(group.id, user_id):
            return {'success': False, 'error': "You're already a member of this group"}

        # Check if group is full (max 4 members)
        if self.get_group_member_count(group.id) >= 4:
            return {'success': False, 'error': 'Group is full (maximum 4 members)'}

        # Add membership
        membership = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role='member'
        )
        self.session.add(membership)
        self.session.commit()

        return {'success': True, 'group': self.get_group_details(group.id)}

    def leave_group(self, group_id: int, user_id: int) -> dict:
        """
        Leave a group.
        Returns dict with 'success' and optionally 'error'.
        """
        membership = self.get_group_membership(group_id, user_id)
        if not membership:
            return {'success': False, 'error': "You're not a member of this group"}

        # Check if this is the last admin
        if membership.role == 'admin' and self.get_group_admin_count(group_id) == 1:
            # Check if there are other members who could be promoted
            member_count = self.get_group_member_count(group_id)
            if member_count > 1:
                return {
                    'success': False,
                    'error': "You can't leave as the only admin. Promote another member first, or delete the group."
                }
            # Last member - delete the group
            self.delete_group(group_id)
            return {'success': True, 'group_deleted': True}

        # Check if last member
        if self.get_group_member_count(group_id) == 1:
            self.delete_group(group_id)
            return {'success': True, 'group_deleted': True}

        # Remove membership
        self.session.delete(membership)
        self.session.commit()
        return {'success': True}

    def remove_member(self, group_id: int, user_id: int, remover_user_id: int) -> dict:
        """
        Remove a member from a group (admin action).
        Returns dict with 'success' and optionally 'error'.
        """
        # Can't remove yourself - use leave instead
        if user_id == remover_user_id:
            return {'success': False, 'error': "You can't remove yourself. Use 'Leave Group' instead."}

        membership = self.get_group_membership(group_id, user_id)
        if not membership:
            return {'success': False, 'error': 'User is not a member of this group'}

        # Can't remove other admins
        if membership.role == 'admin':
            return {'success': False, 'error': 'Remove admin status first before removing this member'}

        self.session.delete(membership)
        self.session.commit()
        return {'success': True}

    def update_member_role(self, group_id: int, user_id: int, new_role: str, updater_user_id: int) -> dict:
        """
        Update a member's role (promote/demote).
        Returns dict with 'success' and optionally 'error'.
        """
        if new_role not in ('admin', 'member'):
            return {'success': False, 'error': 'Invalid role'}

        membership = self.get_group_membership(group_id, user_id)
        if not membership:
            return {'success': False, 'error': 'User is not a member of this group'}

        # Demoting self check
        if user_id == updater_user_id and new_role == 'member':
            # Check if there are other admins
            if self.get_group_admin_count(group_id) == 1:
                return {
                    'success': False,
                    'error': "You can't demote yourself as the only admin. Promote another member first."
                }

        # Demoting last admin check
        if membership.role == 'admin' and new_role == 'member':
            if self.get_group_admin_count(group_id) == 1:
                return {
                    'success': False,
                    'error': "Can't demote the only admin. Promote another member first."
                }

        membership.role = new_role
        self.session.commit()
        return {'success': True}

    def regenerate_invite_code(self, group_id: int) -> Optional[str]:
        """Generate a new invite code for a group."""
        group = self.get_group_by_id(group_id)
        if not group:
            return None

        new_code = self.generate_invite_code()
        while self.session.query(Group).filter_by(invite_code=new_code).first():
            new_code = self.generate_invite_code()

        group.invite_code = new_code
        self.session.commit()
        return new_code

    def get_group_members(self, group_id: int) -> List[dict]:
        """Get all members of a group with their details."""
        group = self.get_group_by_id(group_id)
        if not group:
            return []

        members = []
        for membership in group.members:
            user = membership.user
            members.append({
                'id': user.id,
                'username': user.username,
                'forename': user.forename,
                'role': membership.role
            })
        return members

    def get_scores_for_group(self, group_id: int) -> List:
        """Get scores for all members of a group, respecting include_historical_data."""
        group = self.get_group_by_id(group_id)
        if not group:
            return []

        member_ids = [m.user_id for m in group.members]
        if not member_ids:
            return []

        start_date = None
        if not group.include_historical_data:
            start_date = group.created_at.date() if group.created_at else None

        return self.get_scores_for_users(member_ids, start_date)

    def get_scores_for_user(self, user_id: int) -> List:
        """Get scores for a single user (personal scope)."""
        return self.get_scores_for_users([user_id])
