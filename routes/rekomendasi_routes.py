from flask import Blueprint, jsonify

rekomendasi_bp = Blueprint('rekomendasi_bp', __name__)

@rekomendasi_bp.route('/', methods=['GET'])
def rekomendasi_produk():
    return jsonify({
        'status': True,
        'message': 'Rekomendasi produk',
        'data': [
            {'produk': 'Beras 5kg', 'skor': 0.92},
            {'produk': 'Minyak Goreng', 'skor': 0.87}
        ]
    }), 200
