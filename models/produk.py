from database.db import db

class Produk(db.Model):
    __tablename__ = 'produk'

    id = db.Column(db.Integer, primary_key=True)
    umkm_id = db.Column(db.Integer, nullable=False)
    nama_produk = db.Column(db.String(150), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    kategori = db.Column(db.String(100))
