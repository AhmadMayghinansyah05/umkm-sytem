from models.produk import Produk
from database.db import db

def get_all_produk():
    return Produk.query.all()

def get_produk_by_id(produk_id):
    return Produk.query.get(produk_id)

def create_produk(data, umkm_id):
    produk = Produk(
        umkm_id=umkm_id,
        nama_produk=data['nama_produk'],
        harga=data['harga'],
        kategori=data.get('kategori')
    )
    db.session.add(produk)
    db.session.commit()
    return produk

def update_produk(produk_id, data):
    produk = Produk.query.get(produk_id)
    if not produk:
        return None

    produk.nama_produk = data.get('nama_produk', produk.nama_produk)
    produk.harga = data.get('harga', produk.harga)
    produk.kategori = data.get('kategori', produk.kategori)

    db.session.commit()
    return produk

def delete_produk(produk_id):
    produk = Produk.query.get(produk_id)
    if not produk:
        return False

    db.session.delete(produk)
    db.session.commit()
    return True
