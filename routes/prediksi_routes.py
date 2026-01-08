from flask import Blueprint, jsonify, request

prediksi_bp = Blueprint('prediksi_bp', __name__)

@prediksi_bp.route('/', methods=['POST'])
def prediksi_penjualan():
    data = request.get_json()

    return jsonify({
        'status': True,
        'message': 'Prediksi penjualan berhasil',
        'hasil_prediksi': 120,
        'input': data
    }), 200
