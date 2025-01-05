from flask import Blueprint, render_template

# Blueprint 생성
paper_route = Blueprint('paper', __name__)

# About 페이지 라우트
@paper_route.route('/paper')
def paper():
    return render_template('paper.html')
