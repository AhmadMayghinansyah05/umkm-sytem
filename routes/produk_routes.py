from flask import Blueprint, request, jsonify
from controllers.produk_controller import (
    store_produk,
    get_all_produk,
    get_produk_by_id,
    update_produk,
    delete_produk
)

produk_bp = Blueprint('produk_bp', __name__)

# ===============================
# CREATE
# ===============================
@produk_bp.route('/', methods=['POST'])
def create_produk():
    data = request.get_json()
    umkm_id = 1  # sementara (DEV)

    produk = store_produk(data, umkm_id)

    return jsonify({
        'status': True,
        'message': 'Produk berhasil ditambahkan',
        'data': {
            'id': produk.id,
            'nama_produk': produk.nama_produk
        }
    }), 201


# ===============================
# READ ALL
# ===============================
@produk_bp.route('/', methods=['GET'])
def get_produk():
    produk_list = get_all_produk()

    return jsonify({
        'status': True,
        'data': produk_list
    })


# ===============================
# READ BY ID
# ===============================
@produk_bp.route('/<int:id>', methods=['GET'])
def detail_produk(id):
    produk = get_produk_by_id(id)

    if not produk:
        return jsonify({'status': False, 'message': 'Produk tidak ditemukan'}), 404

    return jsonify({'status': True, 'data': produk})


# ===============================
# UPDATE
# ===============================
@produk_bp.route('/<int:id>', methods=['PUT'])
def update_produk_route(id):
    data = request.get_json()
    produk = update_produk(id, data)

    if not produk:
        return jsonify({'status': False, 'message': 'Produk tidak ditemukan'}), 404

    return jsonify({'status': True, 'message': 'Produk diperbarui'})


# ===============================
# DELETE
# ===============================
@produk_bp.route('/<int:id>', methods=['DELETE'])
def delete_produk_route(id):
    success = delete_produk(id)

    if not success:
        return jsonify({'status': False, 'message': 'Produk tidak ditemukan'}), 404

    return jsonify({'status': True, 'message': 'Produk dihapus'})
