from flask import Blueprint, jsonify, request

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    return jsonify({
        'status': True,
        'message': 'Login endpoint'
    })
