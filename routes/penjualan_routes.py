from flask import Blueprint, jsonify, request

penjualan_bp = Blueprint('penjualan_bp', __name__)

@penjualan_bp.route('/', methods=['GET'])
def get_penjualan():
    return jsonify({
        'status': True,
        'message': 'Data penjualan'
    }), 200


@penjualan_bp.route('/', methods=['POST'])
def tambah_penjualan():
    data = request.get_json()
    return jsonify({
        'status': True,
        'message': 'Penjualan berhasil disimpan',
        'data': data
    }), 201
