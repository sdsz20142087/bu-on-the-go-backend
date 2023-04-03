import jwt
from app.main import bp
from flask import jsonify, request
from app.models import *


def authenticate(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split(' ')[1]
                user_id = jwt.decode(token, 'secret', algorithms=['HS256'])['user_id']
                # put user_id in func's args
                kwargs['user_id'] = user_id
                return func(*args, **kwargs)
            except Exception as e:
                print(e)
                return jsonify({'message': 'Invalid token.'}), 401
        else:
            return jsonify({'message': 'Token is missing.'}), 401

    wrapper.__name__ = func.__name__
    return wrapper


@bp.route('/')
def index():
    return 'Hello World'


@bp.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    full_name = request.json.get('full_name')
    # created_at = time.time()
    # print(created_at)
    password = request.json.get('password')
    user_type = request.json.get('user_type')
    user = User(email=email, full_name=full_name, password=password, user_type=user_type)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({'message': 'User creation failed.'}), 500
    return jsonify({'message': 'User created successfully.'}), 201


@bp.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.password == password:
        # generate token for the user
        token = jwt.encode({'user_id': user.user_id}, 'secret',
                           algorithm='HS256')
        return jsonify({'token': token, 'message': 'Login successful.'}), 200
    else:
        return jsonify({'message': 'Invalid credentials.'}), 401


@bp.route('/event/list', methods=['GET'])
@authenticate
def event_list(user_id):
    # get all calendars for the user
    calendars = Calendar.query.filter_by(user_id=user_id).all()
    # get all events for the user
    events = Event.query.filter(Event.calendar_id.in_([calendar.calendar_id for calendar in calendars])).all()

    return jsonify({'events': [vars(event) for event in events]}), 200


@bp.route('/event/<int:event_id>', methods=['GET'])
@authenticate
def event_details(user_id, event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'message': 'Event not found.'}), 404
    # check if the user has a calendar that has this event
    calendar = Calendar.query.filter_by(user_id=user_id).all()[0]  # TODO: handle multiple calendars
    calendar_events = CalendarEvent.query.filter_by(event_id=event_id, calendar_id=calendar.calendar_id).all()
    if len(calendar_events) > 0:
        # user has access to this event
        return jsonify({'event': vars(event)}), 200
    else:
        return jsonify({'message': 'You are not authorized to view this event.'}), 401


@bp.route('/event', methods=['POST'])
@authenticate
def create_event(user_id):
    # get user's calendars
    calendars = Calendar.query.filter_by(email=User.query.get(user_id).email).all()
    calendar = calendars[0]  # TODO: handle multiple calendars
    calendar_id = calendar.calendar_id

    event_name = request.json.get('event_name')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    start_time = request.json.get('start_time')
    end_time = request.json.get('end_time')
    repeat_mode = request.json.get('repeat_mode')
    priority = request.json.get('priority')
    desc = request.json.get('desc')
    event = Event(event_name=event_name, calendar_id=calendar_id, latitude=latitude, longitude=longitude,
                  start_time=start_time, end_time=end_time, repeat_mode=repeat_mode, priority=priority, desc=desc)
    db.session.add(event)
    db.session.commit()
    return jsonify({'message': 'Event created successfully.'}), 201


@bp.route('/event/<int:event_id>', methods=['DELETE'])
@authenticate
def delete_event(user_id, event_id):
    event = Event.query.get(event_id)
    if event:
        calendar = Calendar.query.filter_by(user_id=user_id).all()[0]  # TODO: handle multiple calendars
        calendar_events = CalendarEvent.query.filter_by(event_id=event_id, calendar_id=calendar.calendar_id).all()
        if len(calendar_events) == 0:
            return jsonify({'message': 'You are not authorized to delete this event.'}), 401
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Event not found.'}), 404


@bp.route('/shared_event/<int:event_id>', methods=['GET'])
def shared_events(event_id):
    # TODO: handle authentication
    s_events = SharedEvent.query.filter_by(event_id=event_id).all()
    return jsonify({'shared_events': [shared_event.shared_event_id for shared_event in s_events]}), 200


@bp.route('/shared_event/<int:event_id>', methods=['POST'])
def create_shared_event(event_id):
    # TODO: handle authentication
    shared_event = SharedEvent(event_id=event_id, owner_id=request.json.get('user_id'))
    db.session.add(shared_event)
    db.session.commit()
    return jsonify({'message': 'Shared event created successfully.'}), 201


@bp.route('/shared_event', methods=['DELETE'])
def delete_shared_event():
    # TODO: handle authentication
    shared_event_id = request.json.get('shared_event_id')
    shared_event = SharedEvent.query.get(shared_event_id)
    if shared_event:
        db.session.delete(shared_event)
        db.session.commit()
        return jsonify({'message': 'Shared event deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Shared event not found.'}), 404


@bp.route('/shared_event_participance/int:shared_event_id/list', methods=['GET'])
def shared_event_participance_list(shared_event_id):
    # TODO: handle authentication
    shared_event_participances = SharedEventParticipance.query.filter_by(shared_event_id=shared_event_id).all()
    return jsonify({'shared_event_participances': [shared_event_participance.status for shared_event_participance in
                                                   shared_event_participances]}), 200


@bp.route('/shared_event_participance', methods=['POST'])
def create_shared_event_participance():
    # TODO: handle authentication
    shared_event_id = request.json.get('shared_event_id')
    user_id = request.json.get('user_id')
    status = request.json.get('status')
    shared_event_participance = SharedEventParticipance(shared_event_id=shared_event_id, user_id=user_id, status=status)
    db.session.add(shared_event_participance)
    db.session.commit()
    return jsonify({'message': 'Shared event participance created successfully.'}), 201


@bp.route('/shared_event_participance', methods=['DELETE'])
def delete_shared_event_participance():
    # TODO: handle authentication
    shared_event_participance_id = request.json.get('shared_event_participance_id')
    shared_event_participance = SharedEventParticipance.query.get(shared_event_participance_id)
    if shared_event_participance:
        db.session.delete(shared_event_participance)
        db.session.commit()
        return jsonify({'message': 'Shared event participance deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Shared event participance not found.'}), 404


@bp.route('/sync/int:user_id', methods=['POST'])
def sync(user_id):
    # TODO: Implement sync endpoint
    return jsonify({'message': 'Synced successfully.'}), 200


@bp.route('/sync/int:user_id', methods=['GET'])
def sync_pull(user_id):
    # TODO: Implement sync pull endpoint
    return jsonify({'message': 'Sync pull successful.'}), 200
