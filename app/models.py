from app.extensions import db


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255))
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP)
    password = db.Column(db.String(255))
    user_type = db.Column(db.Enum('student', 'teacher', 'staff'))

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Calendar(db.Model):
    calendar_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255))
    calendar_name = db.Column(db.String(255))
    calendar_type = db.Column(db.Enum('holiday', 'courses', 'school_event'))

    def __repr__(self):
        return '<Calendar {}>'.format(self.calendar_name)


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(255))
    latitude = db.Column(db.DECIMAL)
    longitude = db.Column(db.DECIMAL)
    start_time = db.Column(db.TIMESTAMP)
    end_time = db.Column(db.TIMESTAMP)
    repeat_mode = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    desc = db.Column(db.Text)

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
    owner_id = db.Column(db.String(255))  # , db.ForeignKey('user.email'))
    created_at = db.Column(db.TIMESTAMP)
    checkin_time = db.Column(db.TIMESTAMP)

    def __repr__(self):
        return '<SharedEvent {}>'.format(self.shared_event_id)


class SharedEventParticipance(db.Model):
    shared_event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum('FAIL', 'SUCCESS'))

    def __repr__(self):
        return '<SharedEventParticipance {}{}>'.format(self.shared_event_id, self.user_id)

# if __name__ == '__main__':
#     print(app.config['SQLALCHEMY_DATABASE_URI'])
#     with app.app_context():
#         db.create_all()
