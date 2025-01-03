from flask import Blueprint, render_template, request, jsonify

import pandas as pd

# Blueprint 생성
home_route = Blueprint('home', __name__)

viztree_df = pd.read_parquet("onepiece_rag/output/create_final_viztree.parquet")

@home_route.route('/')
def home():
    return render_template('index.html')


@home_route.route('/viztree', methods=['GET'])
def read_viztree():
    parent_id = request.args.get("parent", default="-1")
    return_data = viztree_df[viztree_df["parent"] == parent_id].to_dict(orient="records")
    return jsonify(return_data)
