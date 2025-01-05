from flask import Flask
from routes import home_route, paper_route
from flask_socketio import SocketIO

# Flask 인스턴스 생성
app = Flask(__name__)
socketio = SocketIO(app)

# Blueprint 등록
app.register_blueprint(home_route)
app.register_blueprint(paper_route)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
