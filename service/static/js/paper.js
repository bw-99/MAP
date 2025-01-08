var socket = io();

function sendMessage() {
    var input = document.getElementById('message_input');
    var message = input.value;
    console.log('Sending message:', message);
    socket.send(message);
    input.value = '';
}

document.getElementById('send_button').addEventListener('click', sendMessage);

socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('message', function(msg) {
    console.log('Received message:', msg);
    var messages = document.getElementById('messages');
    var newMessage = document.createElement('div');
    newMessage.textContent = msg;
    messages.appendChild(newMessage);
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});
