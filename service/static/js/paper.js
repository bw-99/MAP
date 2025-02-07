var socket = io();

function sendMessage() {
    var input = document.getElementById('message_input');
    var message = input.value;
    var selectedText = window.getSelection().toString();
    if (selectedText) {
        message = `"${selectedText}"\n\n${message}`;
    }
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

function showReplyButton(event) {
    var selectedText = window.getSelection().toString();
    var replyButton = document.getElementById('reply_button');
    if (selectedText) {
        replyButton.style.display = 'block';
        replyButton.style.left = event.pageX + 'px';
        replyButton.style.top = event.pageY + 'px';
    } else {
        replyButton.style.display = 'none';
    }
}

function handleIframeSelection() {
    var iframe = document.getElementById('pdf_iframe');
    iframe.onload = function() {
        var iframeDocument = iframe.contentDocument || iframe.contentWindow.document;

        iframeDocument.addEventListener('mouseup', function(event) {
            var selectedText = iframeDocument.getSelection().toString();
            if (selectedText) {
                var replyButton = document.getElementById('reply_button');
                replyButton.style.display = 'block';
                var rect = iframe.getBoundingClientRect();
                replyButton.style.left = rect.left + event.clientX + 'px';
                replyButton.style.top = rect.top + event.clientY + 'px';
            } else {
                document.getElementById('reply_button').style.display = 'none';
            }
        });
    };
}

document.getElementById('send_button').addEventListener('click', sendMessage);
document.addEventListener('mouseup', showReplyButton);

document.getElementById('reply_button').addEventListener('click', function() {
    var selectedText = window.getSelection().toString();
    if (!selectedText) {
        var iframe = document.getElementById('pdf_iframe');
        var iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
        selectedText = iframeDocument.getSelection().toString();
    }
    var input = document.getElementById('message_input');
    input.value = `"${selectedText}"\n\n` + input.value;
    document.getElementById('reply_button').style.display = 'none';
});

socket.on('connect', function() {
    console.log('Connected to server');
    handleIframeSelection();
});

socket.on('message', function(msg) {
    console.log('Received message:', msg);
    addMessageToChat(msg, 'server');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});
