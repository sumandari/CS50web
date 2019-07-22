import os

from datetime import datetime
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, send


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

users = []
channels = []


class ChatChannel:
    channel_list = []
    def __init__(self, name):
        self.name = name
        self.user = []
        self.message = []
        ChatChannel.channel_list.append(self.name)
    
    def add_user(self, user):
        self.user.append(user)
        return print(f"{user} added")
    
    # def add_message(self, user, timestamp, text):
    #     new_message = {
    #         "timestamp": timestamp,
    #         "user": user,
    #         "message": text
    #     }
    #     if len(self.message) >= 100:
    #         self.message.pop(0)
    #     self.message.append(new_message)
    
    def add_message(self, msg):
        if len(self.message) >= 100:
            self.message.pop(0)
        self.message.append(msg)
    
    def show_message(self):
        return self.message
    
    def __del__(self):
        ChatChannel.channel_list.remove(self.name)
        return (f"{self.name} deleted")

def time_now():
    return datetime.strftime(datetime.now(), "%Y-%m-%d %X")


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/login")
def login_():
    return "login function"


@socketio.on("check user")
def check_user(data):
    print('checking user')
    if not data['user'] in users:
        users.append(data['user'])
    print(users)

@socketio.on("get channels")
def show_all_channels():
    # send list of channels
    chs_list = [ch.name for ch in channels]
    emit('show all channels', {'chs_list': chs_list})
    print('get channels')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    session_id = request.sid
    sekarang = time_now()
    msg = f"Server says {username} is joining {room} @{sekarang}!"
    print(f"{username} joining room {room} sesion id {session_id}")
    emit('receive from server', {'msg': msg}, room=data['room'])
    for channel in channels:
        if channel.name == room:
            channel.add_message(msg)
            break

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    session_id = request.sid
    sekarang = time_now()
    msg = f"Server says {username} left {room} @{sekarang}"
    print(f"{username} leaving room {room} sesion id {session_id}")
    emit('receive from room', {'msg': msg}, room=room)
    for channel in channels:
        if channel.name == room:
            channel.add_message(msg)
            break

@socketio.on('request chat log')
def chat_log(data):
    print(f"-----------------request chat log room {data['room']}")
    print(channels)
    room = data['room']
    # find index
    room_index = None
    for channel in channels:
        if channel.name == room:
            room_index = channels.index(channel)
            print(f"room index = {room_index}")
            break
    if room_index == None:
        print('your room is not exist')
        return emit('response chat log', {'msg': ['your room is closed, try another room']})
    print(f"send chat log room {room}")
    # find index of array
    msg = channels[room_index].message
    print(msg)
    emit('response chat log', {'msg': msg} )

@socketio.on("send chat")
def send_chat(data):
    user = data['user']
    room = data['room']
    now = time_now()
    msg = f"<span class='text-warning'><i><b>{user}</b> <small>@{now}</small> says</i></span>  {data['msg']}"
    emit('receive from room', {'msg': msg }, room=room)
    # save chat room into channel
    # find the location of channel in array
    for channel in channels:
        if channel.name == room:
            channel.add_message(msg)
            break


@socketio.on("submit user")
def login(data):
    display_name = data['user']
    print(f"chcek {display_name} if available")
    if display_name in users:
        emit('login user', {'stat': 'not available', 'user': display_name})
        print("NA")
    else:
        # add data display name, in order to avoid duplicate name
        users.append(display_name)
        emit('login user', {'stat': 'available', 'user': display_name})
        print("oke")


@socketio.on('submit channel')
def create_channel(data):
    new_ch = data['ch_name']
    print(new_ch)
    # check avaibility
    for ch in channels:
        if ch.name == new_ch:
            return emit('new channel', {'stat':'na', 'name_ch': new_ch})
    # create channel (room)
    channels.append(ChatChannel(new_ch))
    emit('new channel', {'stat':'ok', 'name_ch': new_ch}, broadcast=True)

# ltes try receving message
@socketio.on('my_event')
def test_message(message):
    print('stats my_event')
    session['receive_count'] = session.get('receive_count',0) + 1
    print('start emiting')
    emit('my_response', 
            {'data': message['data'], 'count': session['receive_count']}, broadcast=True)
    print('emot done')

@socketio.on('send to room')
def send_to_room(data):
    print(data)
    emit('receive from room', {'msg': data['msg']}, room=data['room'])

# Complete the Display Name, Channel Creation, and Channel List steps.
# login user menggunakan localestorage