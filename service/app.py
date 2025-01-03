from flask import Flask
from routes import home_route, paper_route

# Flask 인스턴스 생성
app = Flask(__name__)

# Blueprint 등록
app.register_blueprint(home_route)
app.register_blueprint(paper_route)

if __name__ == '__main__':
    app.run(debug=True)
