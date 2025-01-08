from flask import Flask, render_template, request
from flask import Blueprint, render_template, request, jsonify
from flask_socketio import send
from service.socketio_instance import socketio  # Import socketio from the new module
from graphrag.cli.main import _query_cli, SearchType
from pathlib import Path

# Blueprint 생성
paper_route = Blueprint('paper', __name__)
chat_bp = Blueprint('chat', __name__)

# About 페이지 라우트
@paper_route.route('/paper')
def paper():
    pdf_url = request.args.get('url', 'https://arxiv.org/pdf/1706.03762')
    return render_template('paper.html', pdf_url=pdf_url)

# SocketIO 이벤트 처리
@chat_bp.route('/socket.io')
def socketio_message():
    return "Chat functionality with SocketIO"

@chat_bp.route('/chat')
def chat():
    return "Chat route is working"

@chat_bp.route('/message', methods=['POST'])
def handle_message():
    message = request.form['message']
    send(message, broadcast=True)
    return jsonify({"status": "Message sent", "message": message})

@socketio.on('message')
def handle_socket_message(msg):
    print("Received message:", msg)

    response, _ = _query_cli(
        method=SearchType.LOCAL,
        query=msg,
        root=Path("onepiece_rag"),
    )
    send(response, broadcast=True)
