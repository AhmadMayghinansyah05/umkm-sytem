from database.db import get_connection

class Penjualan:
    @staticmethod
    def all():
        db = get_connection()
        c = db.cursor(dictionary=True)
        c.execute("SELECT * FROM penjualan")
        return c.fetchall()
