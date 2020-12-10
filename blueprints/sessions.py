from flask import Blueprint, jsonify, request;
from playhouse.shortcuts import model_to_dict;
import models;
from pprint import pprint;

session = Blueprint('sessions', 'session');

# GET to return all rooms
@session.route('/', methods=['GET'])
def get_all_sessions():
    try:
        sessions = [model_to_dict(session) for session in models.Session.select()];
        print(sessions);
        return jsonify(data=sessions, status={"code": 200, "message": "Retrived Sessions"});
    except models.DoesNotExist:
        return jsonify(data={}, status={"code": 401, "message": "Error"});

# GET to return specifically only specified room
@session.route('/<room>', methods=['GET'])
def find_session(room):
    try: 
        found = models.Session.get_or_none(models.Session.room_name == room);
        if found:
            session = model_to_dict(models.Session.get(models.Session.room_name == room));
            return jsonify(
                data=session, 
                status={"code": 200, "message": f"Retrived Session Room {room}"});
        else:
            return jsonify(data={}, status={"code": 404, "message": f"Room {room!r} Not Found"});
    except models.DoesNotExist:
        return jsonify(data={}, status={"code": 401, "message": "Error"});

# Create a Room
@session.route('/', methods=['POST'])
def create_sessions():
    payload = request.get_json();
    print(payload, 'payload');
    session = models.Session.create(**payload);
    sess_to_dict = model_to_dict(session);
    return jsonify(data=sess_to_dict, status={"code": 201, "message": "Session Created"});

# Delete a room
@session.route('/<room>', methods=['DELETE'])
def delete_session(room):
    session = models.Session.delete().where(models.Session.room_name == room);
    num_of_rows_deleted = session.execute();
    #pprint(num_of_rows_deleted);
    if num_of_rows_deleted:
        return jsonify(
            data={},
            status={"code": "200", "message": "Successfully Deleted Room"});
    else:
        return jsonify(
            data={}, 
            status={"code": 401, "message": "Error"});

# Add A Video To The Playlist
@session.route('/<room>', methods=["PUT"])
def add_video(room):
    payload = request.get_json();
    #pprint(payload);
    try: 
        found = models.Session.get_or_none(models.Session.room_name == room);
        if found:
            session = model_to_dict(models.Session.get(models.Session.room_name == room));
            #pprint(session)
            session['playlist'].append(payload);
            #pprint(session);
            update = models.Session.update(**session).where(models.Session.room_name == room);
            update.execute();
            return jsonify(
                data=model_to_dict(models.Session.get(models.Session.room_name == room)), 
                status={"code": 200, "message": f"Added video to playlist in {room}"});
        else:
            return jsonify(
                data={}, 
                status={"code": 404, "message": f"Room {room!r} Not Found"});
    except models.DoesNotExist:
        return jsonify(
            data={}, 
            status={"code": 401, "message": "Error"});

# Delete a video from the playlist
@session.route('/<room>/nextVideo', methods=['DELETE'])
def remove_video(room):
    payload = request.get_json();
    #pprint(payload);
    try: 
        found = models.Session.get_or_none(models.Session.room_name == room);
        if found:
            session = model_to_dict(models.Session.get(models.Session.room_name == room));
            #pprint(session)
            if session['playlist'][0]:
                session['playlist'].pop(0);
                #pprint(session);
                update = models.Session.update(**session).where(models.Session.room_name == room);
                update.execute();
            return jsonify(
                data=model_to_dict(models.Session.get(models.Session.room_name == room)), 
                status={"code": 200, "message": f"Removed video from playlist in {room}"});
        else:
            return jsonify(
                data={}, 
                status={"code": 404, "message": f"Room {room!r} Not Found"});
    except models.DoesNotExist:
        return jsonify(
            data={}, 
            status={"code": 401, "message": "Error"});
