from flask import Flask, g
from flask.globals import request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from pprint import pprint

import models
from blueprints.sessions import session

DEBUG = True

from dotenv import load_dotenv
load_dotenv()

import os
PORT = os.getenv("PORT")
SECRET = os.getenv("SECRET")

CORS(session, origins=['http://localhost:3000', 'https://youshare-frontend.fly.dev'])

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET
if 'ON_HEROKU' in os.environ:
    print('extra heroku configs activated')
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'

socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(session, url_prefix="/api/sessions")

CORS(app, origins=['http://localhost:3000', 'https://youshare-frontend.fly.dev'])

@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connect()

@app.after_request
def after_request(response):
    g.db.close()
    return response

# SOCKET ROUTES

# hashmap containing all rooms, which in turn keeps track of each room's votes and flags
all_rooms = {}
# indexing hashmap to find rooms by a user's session ID in request.id
all_users = {}

# helper function to add room properties object when creating rooms.
def room_dict(user):
    room_dict_filled = {
        "connected_users": [user],
        "negative_votes": 0,
        "ended_flags": 0,
        "ready_flags": 0,
        "buffer_flags": 0,
        "error": False
    }
    return room_dict_filled

# helper function to reset votes and flags for a room during videos 
def reset_votes_flags(room):
    room['negative_votes'] = 0
    room['ended_flags'] = 0
    room['ready_flags'] = 0
    room['buffer_flags'] = 0
    room['error'] = False

# when a user joins or creates a room - initial connection
@socketio.on('connection')
def on_connection(json):
    global all_rooms
    global all_users
    join_room(json['room'])
    user_dict = {
        "username": str(json['username']),
        "sessionID": request.sid
    };
    # if there is an active room, append user to coonnected room
    if json['room'] in all_rooms.keys():
        all_rooms[json["room"]]['connected_users'].append(user_dict)
    # else creates a new room with user
    else:
        all_rooms[json['room']] = room_dict(user_dict)
    all_users[request.sid] = json['room']

    #pprint(all_rooms)
    #pprint('**** User ' + str(json['username']) + " (sid: " + str(request.sid) + ") connected to room " + str(json['room']))
    emit('connection', {"connected_users": all_rooms[json["room"]]['connected_users']}, room=json['room'])
    return {"sessionID": request.sid, "username": str(json['username']), "connected_users": all_rooms[json["room"]]['connected_users']}

# removes a user from all_rooms[user's room] whenever the disconnect
@socketio.on('disconnect')
def on_disconnect():
    global all_rooms
    global all_users
    for user in all_rooms[all_users[request.sid]]["connected_users"]:
        if user["sessionID"] == request.sid:
            all_rooms[all_users[request.sid]]["connected_users"].remove(user)
            if len(all_rooms[all_users[request.sid]]["connected_users"]) == 0:
                del all_rooms[all_users[request.sid]]
            else:
                emit('connection', {"connected_users": all_rooms[all_users[request.sid]]["connected_users"]} , room=all_users[request.sid])
            break
    del all_users[request.sid]

# forwards whatever video a users adds on their front-end
# is added to the queue to everyone in the room
@socketio.on('add-playlist')
def on_playlist(json):
    #pprint(json)
    #print("its a hit for the playlist listener")
    emit('add-playlist', json, room=json['room'])

# monitors to make sure everyone can play/pause at the same time
@socketio.on('player-state')
def on_player_state(json):
    pprint(json)
    print("its a hit for the player listener")
    emit('player-state', json, room=json['room'])

# keeps track of people's voting to skip the video or not
# when at least half the room votes to skip the video, will
# skip to the next video
@socketio.on('voting')
def on_voting(json):
    #print("voting triggered")
    global all_rooms
    skip = False
    for room in all_rooms:
        if room['room_name'] == json['room']:
            room['negative_votes'] += json['negativeVotes'];
            #print(f"{room['negative_votes']} votes, must exceed vote of {len(room['connected_users']) / 2}")
            if room['negative_votes'] >= len(room['connected_users']) / 2:
                skip = True
                reset_votes_flags(room)
                emit('voting', skip, room=json['room'])
        break

# tests to make sure everyone's video has ended before telling the front end
# to progress to the next video in the queue
@socketio.on('next-video')
def on_next_video(json):
    global all_rooms
    next_video = False
    for room in all_rooms:
        if room['room_name'] == json['room']:
            room['ended_flags'] += 1
            #print(f"{room['ended_flags']} flags, must meet {len(room['connected_users'])}")
            if room['ended_flags'] == len(room['connected_users']):
                #print("condition met")
                next_video = True
                reset_votes_flags(room)
                emit('next-video', next_video, room=json['room'])
        break

# monitors 'buffer' states of users
# confirms that everyone has loaded and played the same video
# if any user encounters an error, emits force-next-video
# only after everyone has confirmed to load the same video
@socketio.on('buffer-states')
def on_buffer_states(json):
    global all_rooms;
    all_rooms[json['room']]['buffer_flags'] += 1
    if json['error']:
        all_rooms[json['room']]['error'] = True
    if all_rooms[json['room']]['buffer_flags'] == len(all_rooms[json['room']]['connected_users']) and all_rooms[json['room']]['error'] == True:
        emit('force-next-video', json, room=json['room'])

if 'ON_HEROKU' in os.environ:
    models.initialize()

if __name__ == '__main__':
    models.initialize()
    socketio.run(app.run(debug=DEBUG, port=PORT))
    # app.run(debug=DEBUG, port=PORT)
