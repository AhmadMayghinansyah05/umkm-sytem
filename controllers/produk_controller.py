from services.produk_service import (
    get_all_produk,
    get_produk_by_id,
    create_produk,
    update_produk,
    delete_produk
)

def list_produk():
    return get_all_produk()

def detail_produk(produk_id):
    return get_produk_by_id(produk_id)

def store_produk(data):
    return create_produk(data)

def edit_produk(produk_id, data):
    return update_produk(produk_id, data)

def remove_produk(produk_id):
    return delete_produk(produk_id)
