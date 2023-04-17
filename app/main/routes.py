import jwt, json
from app.main import bp
from flask import jsonify, request
from app.models import *
from types import SimpleNamespace
from google.oauth2 import id_token
from google.auth.transport import requests


def serialize(obj):
    data = {}
    for c in obj.__table__.columns:
        # print(c.name, getattr(obj, c.name))
        if c.name == 'created_at':
            data[c.name] = getattr(obj, c.name).astimezone().isoformat()
        else:
            data[c.name] = getattr(obj, c.name)
    return data


def authenticate(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        print('got token:', token)
        if token:
            try:
                token = token.split(' ')[1]
                print('token:', token)
                user_id = jwt.decode(token, 'secret', algorithms=['HS256'])['user_id']
                # put user_id in func's args
                kwargs['user_id'] = user_id
            except Exception as e:
                # print the stack trace
                return jsonify({'message': 'Invalid token.'}), 401
            return func(*args, **kwargs)
        else:
            return jsonify({'message': 'Token is missing.'}), 401

    wrapper.__name__ = func.__name__
    return wrapper


@bp.route('/')
def index():
    return 'Hello World'


@bp.route('/ping', methods=['POST'])
@authenticate
def handle_ping(user_id):
    return jsonify({'message': 'pong'}), 200


@bp.route('/google_login', methods=['POST'])
def google_login():
    google_token = request.values.get('google_token')
    try:
        idinfo = id_token.verify_oauth2_token(google_token, requests.Request())
        print(idinfo)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'message': 'Invalid token.'}), 401
        # ID token is valid. Get the user's Google Account email from the decoded token.
        email = idinfo['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            # create a new user
            user = User(email=email, full_name=idinfo['name'], user_type='student')
            db.session.add(user)
            db.session.commit()
        # generate token for the user
        token = jwt.encode({'user_id': user.user_id}, 'secret',
                           algorithm='HS256').decode('utf-8')
        return jsonify({'token': "Bearer " + token, 'message': 'Login successful.', 'user': serialize(user)}), 200
    except Exception as e:
        print(e)
        return jsonify({'message': 'Invalid token.'}), 401


@bp.route('/register', methods=['POST'])
def register():
    for key in request.values:
        print(key, request.values.get(key))
    email = request.values.get('email')
    full_name = request.values.get('full_name')
    # created_at = time.time()
    # print(created_at)
    password = request.values.get('password')
    user_type = request.values.get('user_type')
    # print(email, full_name, password, user_type)
    user = User(email=email, full_name=full_name, password=password, user_type=user_type)
    try:
        db.session.add(user)
        db.session.commit()
        print('User created successfully.', serialize(user), user.created_at)
    except Exception as e:
        print(e)
        return jsonify({'message': 'User creation failed.'}), 500
    assert user.user_id != None
    return jsonify({'message': 'User created successfully.', 'user': serialize(user)}), 200


@bp.route('/login', methods=['POST'])
def login():
    email = request.values.get('email')
    password = request.values.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.password == password:
        # generate token for the user
        token = jwt.encode({'user_id': user.user_id}, 'secret',
                           algorithm='HS256').decode('utf-8')
        return jsonify({'token': "Bearer " + token, 'message': 'Login successful.', 'user': serialize(user)}), 200
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


@bp.route('/user', methods=['GET'])
@authenticate
def get_user(user_id):
    uu = request.values.get('user_id')
    u = User.query.filter(User.user_id == uu).first()
    if not u:
        return jsonify({'message': 'User not found.'}), 404
    return jsonify({'user': serialize(u),'message':'ok'}), 200

@bp.route('/event', methods=['POST'])
@authenticate
def create_event(user_id):
    try:
        # get user's calendars
        calendars = Calendar.query.filter_by(email=User.query.get(user_id).email).all()
        calendar = calendars[0]  # TODO: handle multiple calendars
        calendar_id = calendar.calendar_id
        event_name = request.values.get('event_name')
        latitude = request.values.get('latitude')
        longitude = request.values.get('longitude')
        start_time = request.values.get('start_time')
        end_time = request.values.get('end_time')
        repeat_mode = request.values.get('repeat_mode')
        priority = request.values.get('priority')
        desc = request.values.get('desc')
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
def get_shared_event(user_id, event_id):
    shared_event = SharedEvent.query.filter_by(event_id=event_id, owner_id=user_id).first()
    if not shared_event:
        return jsonify({'message': 'Shared event not found.'}), 404
    return jsonify({'shared_event': serialize(shared_event)}), 200


@bp.route('/shared_event/<int:event_id>', methods=['POST'])
@authenticate
def create_shared_event(user_id, event_id):
    # check if the user has a calendar that has this event
    calendar = Calendar.query.filter_by(user_id=user_id).all()[0]  # TODO: handle multiple calendars
    calendar_events = CalendarEvent.query.filter_by(event_id=event_id, calendar_id=calendar.calendar_id).all()
    if len(calendar_events) == 0:
        return jsonify({'message': 'You are not authorized to share this event.'}), 401
    shared_event = SharedEvent(event_id=event_id, owner_id=user_id)
    db.session.add(shared_event)
    db.session.commit()
    return jsonify({'message': 'Shared event created successfully.'}), 201


@bp.route('/shared_event', methods=['DELETE'])
@authenticate
def delete_shared_event(user_id):
    shared_event_id = request.values.get('shared_event_id')
    shared_event = SharedEvent.query.get(shared_event_id)
    if shared_event:
        owner_id = shared_event.owner_id
        if owner_id != user_id:
            return jsonify({'message': 'You are not authorized to delete this shared event.'}), 401
        db.session.delete(shared_event)
        db.session.commit()
        return jsonify({'message': 'Shared event deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Shared event not found.'}), 404


@bp.route('/shared_event_participance/int:shared_event_id/list', methods=['GET'])
@authenticate
def shared_event_participance_list(user_id, shared_event_id):
    shared_event = SharedEvent.query.get(shared_event_id)
    if not shared_event:
        return jsonify({'message': 'Shared event not found.'}), 404
    owner_id = shared_event.owner_id
    if owner_id != user_id:  # only the owner can view the list of participants
        return jsonify({'message': 'You are not authorized to view this shared event.'}), 401
    shared_event_participances = SharedEventParticipance.query.filter_by(shared_event_id=shared_event_id).all()
    return jsonify({'shared_event_participances': [serialize(shared_event_participance) for shared_event_participance in
                                                   shared_event_participances]}), 200


@bp.route('/shared_event_participance/<int:shared_event_participance_id>', methods=['GET'])
@authenticate
def get_shared_event_participance(user_id, shared_event_participance_id):
    shared_event_participance = SharedEventParticipance.query.get(shared_event_participance_id)
    if not shared_event_participance:
        return jsonify({'message': 'Shared event participance not found.'}), 404
    shared_event_id = shared_event_participance.shared_event_id
    shared_event = SharedEvent.query.get(shared_event_id)
    owner_id = shared_event.owner_id
    if owner_id != user_id and user_id != shared_event_participance.user_id:
        return jsonify({'message': 'You are not authorized to view this shared event.'}), 401
    return jsonify({'shared_event_participance': serialize(shared_event_participance)}), 200


@bp.route('/shared_event_participance/<int:shared_event_participance_id>', methods=['POST'])
@authenticate
def update_shared_event_participance(user_id, shared_event_participance_id):
    shared_event_participance = SharedEventParticipance.query.get(shared_event_participance_id)
    if not shared_event_participance:
        return jsonify({'message': 'Shared event participance not found.'}), 404
    shared_event_id = shared_event_participance.shared_event_id
    shared_event = SharedEvent.query.get(shared_event_id)
    owner_id = shared_event.owner_id
    if owner_id != user_id and user_id != shared_event_participance.user_id:
        return jsonify({'message': 'You are not authorized to edit this shared event.'}), 401
    status = request.values.get('status')
    shared_event_participance.status = status
    db.session.commit()
    return jsonify({'message': 'Shared event participance updated successfully.'}), 200


@bp.route('/shared_event_participance', methods=['POST'])
@authenticate
def create_shared_event_participance(user_id):  # only the owner or the user themselves can add/edit participants
    shared_event_id = request.values.get('shared_event_id')
    shared_event = SharedEvent.query.get(shared_event_id)
    if not shared_event:
        return jsonify({'message': 'Shared event not found.'}), 404
    owner_id = shared_event.owner_id
    if owner_id != user_id:
        if user_id != request.values.get('user_id'):
            return jsonify({'message': 'You are not authorized to add participants to this shared event.'}), 401
    user_id = request.values.get('user_id')
    status = request.values.get('status')
    shared_event_participance = SharedEventParticipance(shared_event_id=shared_event_id, user_id=user_id, status=status)
    db.session.add(shared_event_participance)
    db.session.commit()
    shared_event_participance_id = shared_event_participance.shared_event_participance_id
    return jsonify({'message': 'Shared event participance created successfully.', 'shared_event_participance_id':
        shared_event_participance_id}), 201


@bp.route('/shared_event_participance', methods=['DELETE'])
@authenticate
def delete_shared_event_participance(user_id):  # only the owner can delete participants
    shared_event_id = request.values.get('shared_event_id')
    shared_event = SharedEvent.query.get(shared_event_id)
    if not shared_event:
        return jsonify({'message': 'Shared event not found.'}), 404
    owner_id = shared_event.owner_id
    if owner_id != user_id:
        return jsonify({'message': 'You are not authorized to delete participants from this shared event.'}), 401
    shared_event_id = request.values.get('shared_event_id')
    user_id = request.values.get('user_id')
    shared_event_participance = SharedEventParticipance.query.filter_by(shared_event_id=shared_event_id,
                                                                        user_id=user_id).first()
    if shared_event_participance:
        db.session.delete(shared_event_participance)
        db.session.commit()
        return jsonify({'message': 'Shared event participance deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Shared event participance not found.'}), 404

@bp.route('/group/list',methods=['GET'])
@authenticate
def list_group(user_id):
    group_members = GroupMember.query.filter_by(user_id=user_id).all()
    group_ids = [group_member.group_id for group_member in group_members]
    groups = Group.query.filter(Group.group_id.in_(group_ids)).all()
    return jsonify({'groups': [serialize(group) for group in groups],'message':'ok'}), 200


@bp.route('/group/<int:group_id>', methods=['GET'])
@authenticate
def group(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is in group
        group_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if group_member:
            return jsonify({'group': serialize(group),'message':'ok'}), 200
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
            return jsonify({'group_members': [group_member.user_id for group_member in group_members],'message':'ok'}), 200
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/group/<int:group_id>/list', methods=['POST'])  # This is used to add a member to a group
@authenticate
def add_group_member(user_id, group_id):
    group = Group.query.get(group_id)
    if group:
        # check if user is the owner of the group
        if group.owner_id == user_id:
            user_id = request.values.get('user_id')
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
            user_id = request.values.get('user_id')
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
    # print(request.values)
    group_name = request.values.get('group_name')
    group = Group(group_name=group_name, owner_id=user_id, desc=request.values.get('desc') or "")
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
    group = Group.query.get(group_id)
    if group:
        # check if user is the owner of the group
        if group.owner_id == user_id:
            db.session.delete(group)
            db.session.commit()
            return jsonify({'message': 'Group deleted successfully.'}), 200
        else:
            return jsonify({'message': 'You are not the owner of the group.'}), 403
    else:
        return jsonify({'message': 'Group not found.'}), 404


@bp.route('/sync', methods=['POST'])
@authenticate
def sync(user_id):
    # TODO: Implement sync endpoint
    json_data = request.get_json(force=True)
    sync_data: SyncData = json.loads(json_data, object_hook=lambda d: SimpleNamespace(**d))
    db.session.begin()
    try:
        # upsert all objects in sync_data
        # put everything into one list
        all_objects = sync_data.flatten()
        db.session.add_all(all_objects)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'message': 'Sync failed.', 'data': None}), 500
    return jsonify({'message': 'Synced successfully.', 'data': None}), 200
