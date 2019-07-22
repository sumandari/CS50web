// connect socketio
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
document.addEventListener('DOMContentLoaded', () => {
    // connect socketio
    // var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    
    if(!localStorage.getItem('user')) {
        $('#exampleModalCenter').modal('show');
        document.querySelector('#user').focus();
    } else {
        // if user has been visited page
        // show user display
        greeting();
        // save username in server in case server was down
        socket.emit('check user', {'user': localStorage.getItem('user')})
        // show all channels
        socket.emit('get channels');
        // if user has been vissited room, address user to the room
        if (localStorage.getItem('room')) {
            joinRoom(localStorage.getItem('room'))
        }
        // console.log('emiring')
    }


    // login event
    socket.on('login user', data => {
        console.log(data);
        const stat = data['stat']
        const user = data['user']
        if (stat == 'not available'){
            $('#exampleModalCenter').modal('show')
            document.querySelector('#exampleModalLongTitle').innerText = user + ' is not available, try another one!';
            document.querySelector('#user').focus();
            document.querySelector('#user').value = null;
        } else {
            $('#exampleModalCenter').modal('toggle');
            // remember display name
            localStorage.setItem('user', user);
            greeting();
            socket.emit('get channels');
            // console.log('logging in')
        }
    })

    socket.on('new channel', data => {
        // console.log(data)
        const li = document.createElement('li');
        const a = document.createElement('a');
        const chList = document.querySelector('#chsList')
        if (data['stat'] == 'na') {
            alert(data['name_ch'] + ' is existed, pick another name')
            return false
        }
        
        // create channel in select option
        const newRoom = document.createElement('option');
        const selectRoom = document.querySelector('select');
        newRoom.setAttribute("value", data['name_ch'])
        newRoom.innerText = data['name_ch']
        selectRoom.append(newRoom)
        // set the selected option in new channel 
        document.querySelector('option[value="'+data['name_ch']+'"]').selected = true;
    })

    socket.on('receive from room', data =>{
        // console.log('message from room' + data['msg'])
        const li = document.createElement('li');
        li.classList.add("chat-msg");
        li.innerHTML = data['msg'];
        document.querySelector('ul').append(li)

    })

    socket.on('receive from server', data =>{
        // console.log('message from server' + data['msg'])
        const li = document.createElement('li');
        li.classList.add("chat-msg");
        li.innerText = data['msg'];
        li.style.color = "red";
        document.querySelector('ul').append(li)

    })

    socket.on('response chat log', data =>  {
        let i = 0;
        let li;
        addChatLine('--------chat log--------')
        for ( i=0; i< data['msg'].length; i++ ){
            li = document.createElement('li');
            li.classList.add("chat-msg");
            li.innerHTML = data['msg'][i];
            document.querySelector('ul').append(li)
            console.log(data['msg'][i])
        }
        addChatLine('--------end log--------')
    })

    socket.on('show all channels', data => {
        const chs_list = data['chs_list'];
        // console.log(chs_list);
        let i = 0;
        for (i = 0; i < chs_list.length ; i++) {
        
            let newRoom = document.createElement('option');
            newRoom.setAttribute("value", chs_list[i])
            newRoom.innerText = chs_list[i]
            document.querySelector('select').append(newRoom)
        }
    })

    // create new channel
    document.querySelector('#createCh').onclick = () => {
        const newCh = document.querySelector('#newCh');
        if (newCh.value == '') {
            alert('name the channel, please!');
            newCh.focus()
            return false
        } else {
            socket.emit('submit channel', {'ch_name': newCh.value})
            newCh.value = null;
            // console.log(`create new channel : {newCh}`)
        }
    }

    // submit user
    document.querySelector('#login').onclick = () => {
        // console.log('submiting.....')
        const user = document.querySelector('#user').value;
        socket.emit('submit user', {'user': user})
    }

    // create new channel
    document.querySelector('form#chForm').onsubmit = event => {
        event.preventDefault();
        document.querySelector('#createCh').click();
        return false;
    }

    // chat sending message
    document.querySelector('form#sendForm').onsubmit = event => {
        const message = document.querySelector('#message');
        socket.emit('send chat', {'msg': message.value, 'user': localStorage.getItem('user'), 'room': localStorage.getItem('room')})
        event.preventDefault();
        message.value = null;
        scrollToBottom();
        return false;
    }

    // join room
    document.querySelector('#goToRoom').onclick = () => {
        const room = document.querySelector('select').value;
        joinRoom(room);
    }
})

// join room
function joinRoom(room) {
    // var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    if (room == null || room == "" ) {
        alert('choose your room, first! then we can have a good time ;)')
        return false
    } else {
        // leave previous room, if any
        if (localStorage.getItem('room')){
            socket.emit('leave', {'username': localStorage.getItem('user'), 'room': localStorage.getItem('room')})
        }
        // save room into local storage
        localStorage.setItem('room', room)
        // emit join event
        socket.emit('join', {'username': localStorage.getItem('user'), 'room': room})
        // show room name
        document.querySelector('#roomName').innerText = 'Room : ' + room;
        // clear chat area
        clearChat();
        // load previous room
        socket.emit('request chat log', {'room': room})
        console.log('emiting request chat log')
    }
}

// greeting user logged in
function greeting() {
    const user = localStorage.getItem('user')
    document.querySelector('#displayName').innerText = 'Hi, ' + user;
    document.querySelector('#message').focus();
    scrollToBottom();
}

// scrolling chat page to bottom
function scrollToBottom() {
    document.documentElement.scrollTo(0, document.body.scrollHeight + 10);
}

// clear screen chat
function clearChat() {
    let li = document.querySelectorAll('li');
    if (li){
        for (let i=0; i < li.length; i++) {
            li[i].parentNode.removeChild(li[i])
        }
    }
}

// add chat log
function addChatLine(msg) {
    let li = document.createElement('li');
    li.classList.add("chat-msg");
    li.innerHTML = msg;
    document.querySelector('ul').append(li)
  }

