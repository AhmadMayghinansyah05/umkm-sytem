from flask import Blueprint, jsonify

log_bp = Blueprint('log_bp', __name__)

@log_bp.route('/', methods=['GET'])
def log_aktivitas():
    return jsonify({
        'status': True,
        'message': 'Log aktivitas user'
    }), 200
