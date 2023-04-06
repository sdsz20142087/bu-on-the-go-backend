from app.extensions import db
import datetime, time

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True)
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    password = db.Column(db.String(255))
    user_type = db.Column(db.Enum('student', 'teacher', 'staff'))

    def __repr__(self):
        return '<User {}>'.format(self.email)
    
    @property
    def as_dict(self):
        return { 'user_id': self.user_id, 'email': self.email, 'full_name': self.full_name, 'created_at': self.created_at.astimezone().isoformat(), 'user_type': self.user_type}


class Calendar(db.Model):
    calendar_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    calendar_name = db.Column(db.String(255))
    calendar_type = db.Column(db.Enum('holiday', 'courses', 'school_event'))

    def __repr__(self):
        return '<Calendar {}>'.format(self.calendar_name)

    @property
    def as_dict(self):
        return { 'calendar_id': self.calendar_id, 'user_id': self.user_id, 'calendar_name': self.calendar_name, 'calendar_type': self.calendar_type}

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(255))
    latitude = db.Column(db.DECIMAL)
    longitude = db.Column(db.DECIMAL)
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    repeat_mode = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    desc = db.Column(db.Text)
    notify_time = db.Column(db.Integer)  # in minutes

    def __repr__(self):
        return '<Event {}>'.format(self.event_name)
    
    @property
    def as_dict(self):
        return { 'event_id': self.event_id, 'event_name': self.event_name, 'latitude': self.latitude, 'longitude': self.longitude, 'start_time': self.start_time.astimezone().isoformat(),
                 'end_time': self.end_time.astimezone().isoformat(), 'repeat_mode': self.repeat_mode, 'priority': self.priority, 'desc': self.desc}


class CalendarEvent(db.Model):
    __tablename__ = 'calendar_event'
    calendar_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<CalendarEvent {}{}>'.format(self.calendar_id, self.event_id)
    
    @property
    def as_dict(self):
        return { 'calendar_id': self.calendar_id, 'event_id': self.event_id }


class SharedEvent(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer)  # , db.ForeignKey('event.event_id'))
    owner_id = db.Column(db.Integer)  # , db.ForeignKey('user.user_id'))
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    checkin_time = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return '<SharedEvent {}>'.format(self.shared_event_id)

    @property
    def __dict__(self):
        return { 'shared_event_id': self.shared_event_id, 'event_id': self.event_id, 'owner_id': self.owner_id, 'created_at': self.created_at.astimezone().isoformat(),
                 'checkin_time': self.checkin_time.astimezone().isoformat() }

class SharedEventParticipance(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum('FAIL', 'SUCCESS'))

    def __repr__(self):
        return '<SharedEventParticipance {}{}>'.format(self.shared_event_id, self.user_id)

    @property
    def __dict__(self):
        return { 'shared_event_id': self.shared_event_id, 'user_id': self.user_id, 'status': self.status }


class Group(db.Model):
    __tablename__ = 'group_table'
    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_time())
    owner_id = db.Column(db.Integer)  # , db.ForeignKey('user.user_id'))

    def __repr__(self):
        return '<Group {}>'.format(self.group_name)


class GroupMember(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<GroupMember {}{}>'.format(self.group_id, self.user_id)
