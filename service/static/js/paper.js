var socket = io();

function sendMessage() {
    var input = document.getElementById('message_input');
    var message = input.value;
    console.log('Sending message:', message);
    socket.send(message);
    addMessageToChat(message, 'user');
    input.value = '';
}

function addMessageToChat(message, sender) {
    var messages = document.getElementById('messages');
    var newMessage = document.createElement('div');
    newMessage.textContent = message;
    newMessage.classList.add('message');
    if (sender === 'user') {
        newMessage.classList.add('user');
    } else {
        newMessage.classList.add('server');
    }
    messages.appendChild(newMessage);
    messages.scrollTop = messages.scrollHeight;
}

document.getElementById('send_button').addEventListener('click', sendMessage);

socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('message', function(msg) {
    console.log('Received message:', msg);
    addMessageToChat(msg, 'server');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});
