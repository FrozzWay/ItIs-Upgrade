from flask import (
    request,
    Blueprint,
    jsonify,
    current_app
)
from src.database import db
from werkzeug.utils import secure_filename
import os
import json

from src.database import db


bp = Blueprint('api', __name__)


@bp.post('/upload')
def upload_logs():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        upload_path = os.path.join(upload_folder, filename)

        if os.path.exists(upload_path):
            os.remove(upload_path)

        file.save(upload_path)

        try:
            db.init_db(upload_path)
            current_app.config['filename'] = filename
        except:
            return jsonify({"status": "wrong format"}), 200

        return jsonify({"status": "ok"}), 200
    return '', 403


@bp.get('/uploaded_filename')
def uploaded_filename():
    return jsonify({
        "filename": current_app.config['filename']
    }), 200


@bp.get('/overall_statistics')
def overall_statistics():
    response = db.overall_statistic()
    return jsonify(response), 200


@bp.get('/categories')
def categories():
    response = db.get_categories()
    return jsonify(response), 200


@bp.get('/check_db')
def check_db():
    if db.check_db():
        return '', 200
    return '', 204


@bp.get('/rep_unpayed_carts')
def rep_unpayed_carts():
    s = request.args.get('date_1')
    p = request.args.get('date_2')

    response = db.rep_unpayed_carts(s, p)
    return jsonify(response), 200


@bp.get('/rep_repeated_payments')
def rep_repeated_payments():
    s = request.args.get('date_1')
    p = request.args.get('date_2')

    amount, data = db.rep_repeated_payments(s, p)

    response = {
        "amount": amount,
        "data": data
    }
    return jsonify(response), 200


@bp.get('/rep_pattern_buy')
def rep_pattern_buy():
    category = request.args.get('category')
    item = request.args.get('item')

    response = dict(db.rep_pattern_buy(category, item))

    return json.dumps(response), 200


@bp.get('/rep_pattern_view')
def rep_pattern_view():
    category = request.args.get('category')
    item = request.args.get('item')

    response = dict(db.rep_pattern_view(category, item))

    return json.dumps(response), 200


@bp.get('/rep_time_pattern')
def rep_time_pattern():
    category = request.args.get('category')
    k = request.args.get('k')

    response = dict(db.rep_time_pattern(category, k))

    return jsonify(response), 200


@bp.get('/rep_actions_per_country')
def rep_actions_per_country():
    response = dict(db.rep_actions_per_country())
    return json.dumps(response), 200


@bp.get('/server_load_per_hour')
def rep_server_load_per_hour():
    avg, statistics = db.rep_server_load_per_hour()
    response = {"statistics": [], "avg": avg}
    for row in statistics:
        response['statistics'].append(
            {
                'month': row[3],
                'day': row[1],
                'hour': row[2],
                'requests_amount': row[0]
            }
        )
    return jsonify(response), 200