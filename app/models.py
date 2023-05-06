from app.extensions import db
from typing import List
import datetime, time, uuid
from sqlalchemy.dialects.mysql import CHAR

class SyncData():
    def __init__(self) -> None:
        self.users: List[User] = []
        self.groups: List[Group] = []
        self.group_members: List[GroupMember] = []
        self.events: List[Event] = []
        self.shared_events: List[SharedEvent] = []
        self.shared_event_participances: List[SharedEventParticipance] = []

    def flatten(self)->List[db.Model]:
        return self.users + self.groups + self.group_members + self.events + self.shared_events + self.shared_event_participances
    
    def __repr__(self) -> str:
        return f"SyncData(users*{len(self.users)},\
              groups*{len(self.groups)},\
                  group_members*{len(self.group_members)},\
                      events*{len(self.events)},\
                          shared_events*{len(self.shared_events)}, \
                            shared_event_participances*{len(self.shared_event_participances)})"


class User(db.Model):
    user_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True, default=str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('student', 'teacher', 'staff'), nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    # @property
    # def as_dict(self):
    #     return { 'user_id': self.user_id, 'email': self.email, 'full_name': self.full_name, 'created_at': self.created_at.astimezone().isoformat(), 'user_type': self.user_type}


class Calendar(db.Model):
    calendar_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    calendar_name = db.Column(db.String(255))
    calendar_type = db.Column(db.Enum('holiday', 'courses', 'school_event'))

    def __repr__(self):
        return '<Calendar {}>'.format(self.calendar_name)

    # @property
    # def as_dict(self):
    #     return { 'calendar_id': self.calendar_id, 'user_id': self.user_id, 'calendar_name': self.calendar_name, 'calendar_type': self.calendar_type}


class Event(db.Model):
    event_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True, default=str(uuid.uuid4()))
    event_name = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    repeat_mode = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    desc = db.Column(db.Text)
    created_by = db.Column(CHAR(36, charset='utf8mb4'))
    notify_time = db.Column(db.Integer)  # in minutes

    def __repr__(self):
        return '<Event {}>'.format(self.event_name)

    # @property
    # def as_dict(self):
    #     return { 'event_id': self.event_id, 'event_name': self.event_name, 'latitude': self.latitude, 'longitude': self.longitude, 'start_time': self.start_time.astimezone().isoformat(),
    #              'end_time': self.end_time.astimezone().isoformat(), 'repeat_mode': self.repeat_mode, 'priority': self.priority, 'desc': self.desc}

class EventUser(db.Model):
    event_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True)
    user_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True)

    def __repr__(self):
        return '<EventUser {}{}>'.format(self.event_id, self.user_id)

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_event'
    calendar_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(CHAR(36, charset='utf8mb4'))

    def __repr__(self):
        return '<CalendarEvent {}{}>'.format(self.calendar_id, self.event_id)

    # @property
    # def as_dict(self):
    #     return { 'calendar_id': self.calendar_id, 'event_id': self.event_id }


class SharedEvent(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(CHAR(36, charset='utf8mb4'))  # , db.ForeignKey('event.event_id'))
    owner_id = db.Column(CHAR(36, charset='utf8mb4'))  # , db.ForeignKey('user.user_id'))
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    checkin_time = db.Column(db.DateTime(timezone=True))
    desc = db.Column(db.Text)

    def __repr__(self):
        return '<SharedEvent {}>'.format(self.shared_event_id)

    # @property
    # def __dict__(self):
    #     return { 'shared_event_id': self.shared_event_id, 'event_id': self.event_id, 'owner_id': self.owner_id, 'created_at': self.created_at.astimezone().isoformat(),
    #              'checkin_time': self.checkin_time.astimezone().isoformat() }


class SharedEventParticipance(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True)
    status = db.Column(db.Enum('FAIL', 'SUCCESS'))

    def __repr__(self):
        return '<SharedEventParticipance {}{}>'.format(self.shared_event_id, self.user_id)

    # @property
    # def __dict__(self):
    #     return { 'shared_event_id': self.shared_event_id, 'user_id': self.user_id, 'status': self.status }


class Group(db.Model):
    __tablename__ = 'group_table'
    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_time())
    desc = db.Column(db.Text)
    owner_id = db.Column(CHAR(36, charset='utf8mb4'))  # , db.ForeignKey('user.user_id'))

    def __repr__(self):
        return '<Group {}>'.format(self.group_name)


class GroupMember(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True)

    def __repr__(self):
        return '<GroupMember {}{}>'.format(self.group_id, self.user_id)

class GroupInvite(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), primary_key=True)
    status = db.Column(db.Enum('FAIL', 'SUCCESS','PENDING'))

    def __repr__(self):
        return '<GroupInvite {}{}>'.format(self.group_id, self.user_email)
    
class UserNotification(db.Model):
    notification_id = db.Column(CHAR(36, charset='utf8mb4'), primary_key=True, default=str(uuid.uuid4())) 
    user_id = db.Column(CHAR(36, charset='utf8mb4'))
    title = db.Column(db.String(255))
    notification_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_time())
    status = db.Column(db.Enum('UNREAD', 'READ'))  