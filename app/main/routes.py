import jwt
from app.main import bp
from flask import jsonify, request
from app.models import *


def serialize(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def authenticate(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split(' ')[1]
                # print(token)
                user_id = jwt.decode(token, 'secret', algorithms=['HS256'])['user_id']
                # put user_id in func's args
                kwargs['user_id'] = user_id
            except Exception as e:
                print(e)
                return jsonify({'message': 'Invalid token.'}), 401
            return func(*args, **kwargs)
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

    return jsonify({'events': [serialize(event) for event in events]}), 200


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
        return jsonify({'event': serialize(event)}), 200
    else:
        return jsonify({'message': 'You are not authorized to view this event.'}), 401


@bp.route('/event', methods=['POST'])
@authenticate
def create_event(user_id):
    try:
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
    except Exception as e:
        print(e)
        return jsonify({'message': 'Event creation failed.'}), 500


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
@authenticate
def shared_events(user_id, event_id):
    # shared_event = SharedEvent.query.filter_by(event_id=event_id,user_id).all()
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


@bp.route('/group/<int:group_id>', methods=['GET'])
@authenticate
def group(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is in group
        group_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if group_member:
            print(serialize(group))
            print(group.__dict__)
            data = serialize(group)
            data.pop('_sa_instance_state')
            return jsonify({'group': serialize(group)}), 200
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/group/<int:group_id>/list', methods=['GET'])  # This is used to get all members in a group
@authenticate
def group_member_list(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is in group
        group_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if group_member:
            group_members = GroupMember.query.filter_by(group_id=group_id).all()
            return jsonify({'group_members': [group_member.user_id for group_member in group_members]}), 200
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/group/<int:group_id>/list', methods=['POST'])  # This is used to add a member to a group
@authenticate
def add_group_member(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is the owner of the group
        if group.owner_id == user_id:
            user_id = request.json.get('user_id')
            group_member = GroupMember(group_id=group_id, user_id=user_id)
            db.session.add(group_member)
            db.session.commit()
            return jsonify({'message': 'Group member added successfully.'}), 201
        else:
            return jsonify({'message': 'You are not the owner of the group.'}), 403
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/group/<int:group_id>/list', methods=['DELETE'])  # This is used to remove a member from a group
@authenticate
def remove_group_member(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is the owner of the group
        if group.owner_id == user_id:
            user_id = request.json.get('user_id')
            group_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
            if group_member:
                db.session.delete(group_member)
                db.session.commit()
                return jsonify({'message': 'Group member removed successfully.'}), 200
            else:
                return jsonify({'message': 'Group member not found.'}), 404
        else:
            return jsonify({'message': 'You are not the owner of the group.'}), 403
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/group', methods=['POST'])
@authenticate
def create_group(user_id):
    # print(request.json)
    group_name = request.json.get('group_name')
    group = Group(group_name=group_name, owner_id=user_id)
    db.session.add(group)
    db.session.commit()
    # update group_member table
    group_member = GroupMember(group_id=group.group_id, user_id=user_id)
    db.session.add(group_member)
    db.session.commit()
    return jsonify({'message': 'Group created successfully.'}), 201


@bp.route('/group/<int:group_id>', methods=['DELETE'])
@authenticate
def delete_group(user_id, group_id):
    pass


@bp.route('/sync/int:user_id', methods=['POST'])
def sync(user_id):
    # TODO: Implement sync endpoint
    return jsonify({'message': 'Synced successfully.'}), 200


@bp.route('/sync/int:user_id', methods=['GET'])
def sync_pull(user_id):
    # TODO: Implement sync pull endpoint
    return jsonify({'message': 'Sync pull successful.'}), 200
