from app.extensions import db


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True)
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    password = db.Column(db.String(255))
    user_type = db.Column(db.Enum('student', 'teacher', 'staff'))

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Calendar(db.Model):
    calendar_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    calendar_name = db.Column(db.String(255))
    calendar_type = db.Column(db.Enum('holiday', 'courses', 'school_event'))

    def __repr__(self):
        return '<Calendar {}>'.format(self.calendar_name)


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(255))
    latitude = db.Column(db.DECIMAL)
    longitude = db.Column(db.DECIMAL)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    repeat_mode = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    desc = db.Column(db.Text)
    notify_time = db.Column(db.Integer)  # in minutes

    def __repr__(self):
        return '<Event {}>'.format(self.event_name)


class CalendarEvent(db.Model):
    __tablename__ = 'calendar_event'
    calendar_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<CalendarEvent {}{}>'.format(self.calendar_id, self.event_id)


class SharedEvent(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer)  # , db.ForeignKey('event.event_id'))
    owner_id = db.Column(db.Integer)  # , db.ForeignKey('user.user_id'))
    created_at = db.Column(db.DateTime, default=db.func.current_time())
    checkin_time = db.Column(db.DateTime)

    def __repr__(self):
        return '<SharedEvent {}>'.format(self.shared_event_id)


class SharedEventParticipance(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum('FAIL', 'SUCCESS'))

    def __repr__(self):
        return '<SharedEventParticipance {}{}>'.format(self.shared_event_id, self.user_id)


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
