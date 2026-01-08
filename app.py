from flask import (
    Flask, request, jsonify,
    render_template, redirect, url_for, session
)
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from math import sqrt
import mysql.connector

# ======= LSTM IMPORTS ======= 
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense


app = Flask(__name__)

# ================= CONFIG =================
app.config["SECRET_KEY"] = "umkm_secret_key"
app.config["JWT_SECRET_KEY"] = "jwt_umkm_secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)

jwt = JWTManager(app)

# ================= DATABASE =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="umkm_smart"
    )

# ================= LOG ACTIVITY =================
def log_activity(user_id, aktivitas):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO log_aktivitas_user
        (user_id, aktivitas, endpoint, metode_http, ip_address, created_at)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        aktivitas,
        request.path,
        request.method,
        request.remote_addr,
        datetime.now()
    ))
    db.commit()
    cur.close()
    db.close()

# ================= ROOT =================
@app.route("/")
def index():
    if session.get("role") == "admin":
        return redirect("/admin/dashboard")
    if session.get("role") == "umkm":
        return redirect("/umkm/dashboard")
    return render_template("auth/login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    # ================= WEB (GET) =================
    if request.method == "GET":
        return render_template("auth/register.html")

    # ================= POST (FORM / API) =================
    # Bisa dari form HTML atau Postman JSON
    data = request.get_json(silent=True) or request.form

    # Validasi minimal
    if not data or not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"msg": "Data tidak lengkap"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Cek email
    cur.execute("SELECT id FROM users WHERE email=%s", (data["email"],))
    if cur.fetchone():
        cur.close()
        db.close()

        # Jika dari form → kembali ke halaman register
        if not request.is_json:
            return render_template(
                "auth/register.html",
                error="Email sudah terdaftar"
            )

        return jsonify({"msg": "Email sudah terdaftar"}), 400

    # Hash password
    password_hash = generate_password_hash(data["password"])

    # Simpan user
    cur.execute("""
        INSERT INTO users (name,email,password,role,created_at)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        data["name"],
        data["email"],
        password_hash,
        "umkm",
        datetime.now()
    ))
    db.commit()
    user_id = cur.lastrowid

    # Log aktivitas
    log_activity(user_id, "register")

    cur.close()
    db.close()

    # ================= RESPONSE =================
    # Jika dari WEB → redirect
    if not request.is_json:
        return redirect(url_for("login"))

    # Jika dari API → JSON
    return jsonify({"msg": "Registrasi berhasil"}), 201

# ================= LOGIN =================
from flask import render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    # ================= TAMPILAN LOGIN (WEB) =================
    if request.method == "GET":
        return render_template("auth/login.html")

    # ================= PROSES LOGIN (POST) =================
    data = request.get_json(silent=True) or request.form

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"msg": "Email dan password wajib diisi"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM users WHERE email=%s", (data["email"],))
    user = cur.fetchone()

    if not user or not check_password_hash(user["password"], data["password"]):
        cur.close()
        db.close()

        # Jika dari WEB → tampilkan error
        if not request.is_json:
            return render_template(
                "auth/login.html",
                error="Email atau password salah"
            )

        return jsonify({"msg": "Email atau password salah"}), 401

    # ================= SESSION UNTUK WEB =================
    session["user_id"] = user["id"]
    session["role"] = user["role"]

    log_activity(user["id"], "login")

    cur.close()
    db.close()

    # ================= JWT UNTUK API =================
    token = create_access_token(identity={
        "id": user["id"],
        "role": user["role"]
    })

    # ================= RESPONSE =================
    if request.is_json:
        return jsonify({"token": token, "role": user["role"]})

    # Redirect sesuai role
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("umkm_dashboard"))

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= ADMIN =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Statistik utama
    cur.execute("SELECT COUNT(*) total FROM users")
    total_user = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) total FROM umkm")
    total_umkm = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) total FROM produk")
    total_produk = cur.fetchone()["total"]

    cur.execute("SELECT SUM(total_harga) omzet FROM penjualan")
    total_omzet = cur.fetchone()["omzet"] or 0

    # Log aktivitas terbaru
    cur.execute("""
        SELECT l.created_at, u.name, l.aktivitas, l.endpoint
        FROM log_aktivitas_user l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 10
    """)
    logs = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "admin/dashboard.html",
        total_user=total_user,
        total_umkm=total_umkm,
        total_produk=total_produk,
        total_omzet=total_omzet,
        logs=logs
    )


@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id, name, email, role, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/users.html", users=users)

@app.route("/admin/umkm")
def admin_umkm():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            u.id,
            u.nama_umkm,
            us.name AS pemilik,
            u.kategori,
            COUNT(DISTINCT pr.id) AS total_produk,
            COALESCE(SUM(pj.total_harga), 0) AS total_penjualan
        FROM umkm u
        JOIN users us ON u.user_id = us.id
        LEFT JOIN produk pr ON pr.umkm_id = u.id
        LEFT JOIN penjualan pj ON pj.produk_id = pr.id
        GROUP BY u.id, us.name, u.kategori
        ORDER BY total_penjualan DESC
    """)

    umkm = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/monitoring_umkm.html", umkm=umkm)


@app.route("/admin/produk")
def admin_produk():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT pr.nama_produk, pr.harga, pr.stok, u.nama_umkm
        FROM produk pr
        JOIN umkm u ON pr.umkm_id = u.id
        ORDER BY pr.created_at DESC
    """)
    produk = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/monitoring_produk.html", produk=produk)

@app.route("/admin/penjualan")
def admin_penjualan():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.tanggal, pr.nama_produk, u.nama_umkm,
               p.jumlah, p.total_harga
        FROM penjualan p
        JOIN produk pr ON p.produk_id = pr.id
        JOIN umkm u ON pr.umkm_id = u.id
        ORDER BY p.tanggal DESC
    """)
    penjualan = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/penjualan_global.html", penjualan=penjualan)

@app.route("/admin/prediksi")
def admin_prediksi():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ambil hasil prediksi terbaru per produk
    cur.execute("""
        SELECT 
            pr.nama_produk,
            um.nama_umkm,
            pp.tanggal_prediksi,
            pp.hasil_prediksi,
            pp.mae,
            pp.rmse,
            pp.created_at
        FROM prediksi_penjualan pp
        JOIN produk pr ON pp.produk_id = pr.id
        JOIN umkm um ON pr.umkm_id = um.id
        ORDER BY pp.created_at DESC
        LIMIT 50
    """)

    prediksi = cur.fetchall()
    cur.close()
    db.close()

    return render_template(
        "admin/monitoring_prediksi.html",
        prediksi=prediksi
    )

@app.route("/admin/log-aktivitas")
def admin_log():
    if session.get("role") != "admin":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT l.created_at, u.name, u.role,
               l.aktivitas, l.endpoint, l.metode_http, l.ip_address
        FROM log_aktivitas_user l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
    """)
    logs = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/log_aktivitas.html", logs=logs)


# ================= UMKM DASHBOARD =================
@app.route("/umkm/dashboard")
def umkm_dashboard():
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ambil semua UMKM milik user
    cur.execute(
        "SELECT * FROM umkm WHERE user_id=%s",
        (session["user_id"],)
    )
    umkm_list = cur.fetchall()

    # UMKM aktif (jika ada)
    active_umkm = None
    if session.get("active_umkm_id"):
        cur.execute(
            "SELECT * FROM umkm WHERE id=%s",
            (session["active_umkm_id"],)
        )
        active_umkm = cur.fetchone()

    cur.close()
    db.close()

    return render_template(
        "umkm/dashboard.html",
        umkm_list=umkm_list,
        active_umkm=active_umkm
    )

# ================= UMKM DATA =================
@app.route("/umkm/data", methods=["GET", "POST"])
def umkm_data():
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute("""
            INSERT INTO umkm (user_id,nama_umkm,alamat,kategori,created_at)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            request.form["nama_umkm"],
            request.form["alamat"],
            request.form["kategori"],
            datetime.now()
        ))
        db.commit()

    cur.execute("SELECT * FROM umkm WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()
    cur.close()
    db.close()

    return render_template("umkm/umkm.html", umkm=data)

@app.route("/umkm/select/<int:umkm_id>")
def select_umkm(umkm_id):
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Validasi kepemilikan UMKM
    cur.execute("""
        SELECT id FROM umkm
        WHERE id=%s AND user_id=%s
    """, (umkm_id, session["user_id"]))

    if not cur.fetchone():
        cur.close()
        db.close()
        return redirect("/umkm/dashboard")

    session["active_umkm_id"] = umkm_id

    cur.close()
    db.close()

    return redirect("/umkm/dashboard")

@app.route("/umkm/tambah", methods=["GET", "POST"])
def tambah_umkm():
    if session.get("role") != "umkm":
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            INSERT INTO umkm (user_id, nama_umkm, alamat, kategori, created_at)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            request.form["nama_umkm"],
            request.form["alamat"],
            request.form["kategori"],
            datetime.now()
        ))
        db.commit()

        umkm_id = cur.lastrowid

        # SET UMKM AKTIF JIKA BELUM ADA
        if not session.get("active_umkm_id"):
            session["active_umkm_id"] = umkm_id

        cur.close()
        db.close()

        return redirect("/umkm/dashboard")

    return render_template("umkm/tambah_umkm.html")

@app.route("/umkm/edit/<int:id>", methods=["GET", "POST"])
def umkm_edit(id):
    if session.get("role") != "umkm":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Pastikan UMKM milik user
    cur.execute("""
        SELECT * FROM umkm
        WHERE id=%s AND user_id=%s
    """, (id, session["user_id"]))
    umkm = cur.fetchone()

    if not umkm:
        cur.close()
        db.close()
        return redirect("/umkm/dashboard")

    if request.method == "POST":
        cur.execute("""
            UPDATE umkm
            SET nama_umkm=%s,
                alamat=%s,
                kategori=%s
            WHERE id=%s
        """, (
            request.form["nama_umkm"],
            request.form["alamat"],
            request.form["kategori"],
            id
        ))
        db.commit()

        log_activity(session["user_id"], "edit_umkm")

        cur.close()
        db.close()
        return redirect("/umkm/dashboard")

    cur.close()
    db.close()

    return render_template("umkm/umkm_edit.html", umkm=umkm)

@app.route("/umkm/delete/<int:id>", methods=["POST"])
def umkm_delete(id):
    if session.get("role") != "umkm":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # 1. Validasi kepemilikan UMKM
    cur.execute("""
        SELECT id FROM umkm
        WHERE id=%s AND user_id=%s
    """, (id, session["user_id"]))
    umkm = cur.fetchone()

    if not umkm:
        cur.close()
        db.close()
        return redirect("/umkm/dashboard")

    # 2. Cek apakah masih ada produk
    cur.execute("SELECT COUNT(*) total FROM produk WHERE umkm_id=%s", (id,))
    if cur.fetchone()["total"] > 0:
        cur.close()
        db.close()
        return render_template(
            "umkm/dashboard.html",
            error="UMKM tidak bisa dihapus karena masih memiliki produk"
        )

    # 3. Hapus UMKM
    cur.execute("DELETE FROM umkm WHERE id=%s", (id,))
    db.commit()

    # 4. Log aktivitas
    log_activity(session["user_id"], "hapus_umkm")

    # 5. Reset UMKM aktif jika terhapus
    if session.get("active_umkm_id") == id:
        session.pop("active_umkm_id")

    cur.close()
    db.close()

    return redirect("/umkm/dashboard")


# ================= PRODUK =================
@app.route("/produk/data", methods=["GET", "POST"])
def produk_data():
    if session.get("role") != "umkm":
        return redirect("/")

    active_umkm_id = session.get("active_umkm_id")
    if not active_umkm_id:
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # ================= CREATE =================
    if request.method == "POST":
        cur.execute("""
            INSERT INTO produk
            (umkm_id, nama_produk, kategori, harga, stok, deskripsi, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            active_umkm_id,
            request.form["nama_produk"],
            request.form["kategori"],
            request.form["harga"],
            request.form["stok"],
            request.form.get("deskripsi"),
            datetime.now()
        ))
        db.commit()

    # ================= READ =================
    cur.execute("""
        SELECT * FROM produk
        WHERE umkm_id = %s
        ORDER BY created_at DESC
    """, (active_umkm_id,))
    produk = cur.fetchall()

    cur.close()
    db.close()

    return render_template("umkm/produk.html", produk=produk)

@app.route("/produk/edit/<int:id>", methods=["GET", "POST"])
def produk_edit(id):
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # ================= UPDATE =================
    if request.method == "POST":
        cur.execute("""
            UPDATE produk SET
                nama_produk=%s,
                kategori=%s,
                harga=%s,
                stok=%s,
                deskripsi=%s
            WHERE id=%s
        """, (
            request.form["nama_produk"],
            request.form["kategori"],
            request.form["harga"],
            request.form["stok"],
            request.form.get("deskripsi"),
            id
        ))
        db.commit()
        cur.close()
        db.close()
        return redirect("/produk/data")

    # ================= READ =================
    cur.execute("SELECT * FROM produk WHERE id=%s", (id,))
    produk = cur.fetchone()

    cur.close()
    db.close()

    if not produk:
        return redirect("/produk/data")

    return render_template("umkm/produk_edit.html", produk=produk)

@app.route("/produk/delete/<int:id>")
def produk_delete(id):
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM produk WHERE id=%s", (id,))
    db.commit()

    cur.close()
    db.close()

    return redirect("/produk/data")

# ================= PENJUALAN =================
@app.route("/penjualan/data")
def penjualan_data():
    if session.get("role") != "umkm":
        return redirect("/")

    if not session.get("active_umkm_id"):
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.id, pr.nama_produk, p.tanggal, p.jumlah, p.total_harga
        FROM penjualan p
        JOIN produk pr ON p.produk_id = pr.id
        WHERE pr.umkm_id = %s
        ORDER BY p.tanggal DESC
    """, (session["active_umkm_id"],))

    penjualan = cur.fetchall()
    cur.close()
    db.close()

    return render_template("umkm/penjualan.html", penjualan=penjualan)

@app.route("/penjualan/tambah", methods=["GET", "POST"])
def penjualan_tambah():
    if session.get("role") != "umkm":
        return redirect("/")

    umkm_id = session.get("active_umkm_id")
    if not umkm_id:
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ambil produk UMKM aktif
    cur.execute("SELECT id, nama_produk, harga FROM produk WHERE umkm_id=%s", (umkm_id,))
    produk_list = cur.fetchall()

    if request.method == "POST":
        produk_id = request.form["produk_id"]
        jumlah = int(request.form["jumlah"])
        tanggal = request.form["tanggal"]

        cur.execute("SELECT harga FROM produk WHERE id=%s", (produk_id,))
        harga = cur.fetchone()["harga"]

        total = harga * jumlah

        cur.execute("""
            INSERT INTO penjualan (produk_id, tanggal, jumlah, total_harga, created_at)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            produk_id, tanggal, jumlah, total, datetime.now()
        ))
        db.commit()

        log_activity(session["user_id"], "tambah_penjualan")

        cur.close()
        db.close()

        return redirect("/penjualan/data")

    cur.close()
    db.close()

    return render_template("umkm/penjualan_tambah.html", produk_list=produk_list)

@app.route("/penjualan/edit/<int:id>", methods=["GET", "POST"])
def penjualan_edit(id):
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*, pr.nama_produk, pr.harga
        FROM penjualan p
        JOIN produk pr ON p.produk_id = pr.id
        WHERE p.id=%s
    """, (id,))
    penjualan = cur.fetchone()

    if not penjualan:
        cur.close()
        db.close()
        return redirect("/penjualan/data")

    if request.method == "POST":
        jumlah = int(request.form["jumlah"])
        total = jumlah * penjualan["harga"]

        cur.execute("""
            UPDATE penjualan
            SET jumlah=%s, total_harga=%s
            WHERE id=%s
        """, (jumlah, total, id))
        db.commit()

        log_activity(session["user_id"], "edit_penjualan")

        cur.close()
        db.close()

        return redirect("/penjualan/data")

    cur.close()
    db.close()

    return render_template("umkm/penjualan_edit.html", penjualan=penjualan)

@app.route("/penjualan/delete/<int:id>")
def penjualan_delete(id):
    if session.get("role") != "umkm":
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM penjualan WHERE id=%s", (id,))
    db.commit()

    log_activity(session["user_id"], "hapus_penjualan")

    cur.close()
    db.close()

    return redirect("/penjualan/data")

#   ================= UMKM LOG AKTIVITAS =================
@app.route("/umkm/log-aktivitas")
def umkm_log():
    if session.get("role") != "umkm":
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT created_at, aktivitas, endpoint, metode_http, ip_address
        FROM log_aktivitas_user
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session["user_id"],))

    logs = cur.fetchall()

    cur.close()
    db.close()

    return render_template("umkm/log_aktivitas.html", logs=logs)

# ================= LSTM PREDICTION MODEL =================
@app.route("/prediksi/penjualan", methods=["GET"])
def umkm_prediksi_penjualan():
    if session.get("role") != "umkm":
        return redirect("/login")

    if not session.get("active_umkm_id"):
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # histori penjualan UMKM aktif
    cur.execute("""
        SELECT tanggal, SUM(jumlah) AS total
        FROM penjualan p
        JOIN produk pr ON p.produk_id = pr.id
        WHERE pr.umkm_id = %s
        GROUP BY tanggal
        ORDER BY tanggal ASC
    """, (session["active_umkm_id"],))
    data = cur.fetchall()

    # prediksi terakhir
    cur.execute("""
        SELECT hasil_prediksi, mae, rmse, tanggal_prediksi
        FROM prediksi_penjualan
        ORDER BY created_at DESC
        LIMIT 1
    """)
    prediksi = cur.fetchone()

    cur.close()
    db.close()

    return render_template(
        "umkm/prediksi_penjualan.html",
        data=data,
        prediksi=prediksi["hasil_prediksi"] if prediksi else 0,
        mae=prediksi["mae"] if prediksi else "-",
        rmse=prediksi["rmse"] if prediksi else "-",
        tanggal_prediksi=prediksi["tanggal_prediksi"] if prediksi else "-"
    )    

# ================= LSTM PREDICTION MODEL =================
def lstm_predict_sales(sales_series, n_steps=7, epochs=50):
    """
    sales_series: list total penjualan harian
    """

    if len(sales_series) < n_steps + 1:
        return None, None, None

    # ===== NORMALIZATION =====
    scaler = MinMaxScaler(feature_range=(0, 1))
    data = scaler.fit_transform(
        np.array(sales_series).reshape(-1, 1)
    )

    # ===== CREATE SEQUENCE =====
    X, y = [], []
    for i in range(len(data) - n_steps):
        X.append(data[i:i+n_steps])
        y.append(data[i+n_steps])

    X = np.array(X)
    y = np.array(y)

    # ===== TRAIN TEST SPLIT =====
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # ===== MODEL =====
    model = Sequential()
    model.add(LSTM(50, activation='relu', input_shape=(n_steps, 1)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    model.fit(X_train, y_train, epochs=epochs, verbose=0)

    # ===== EVALUATION =====
    y_pred = model.predict(X_test, verbose=0)

    y_test_inv = scaler.inverse_transform(y_test)
    y_pred_inv = scaler.inverse_transform(y_pred)

    mae = mean_absolute_error(y_test_inv, y_pred_inv)
    rmse = sqrt(mean_squared_error(y_test_inv, y_pred_inv))

    # ===== NEXT DAY PREDICTION =====
    last_sequence = data[-n_steps:]
    next_pred = model.predict(
        last_sequence.reshape(1, n_steps, 1),
        verbose=0
    )
    next_pred_inv = scaler.inverse_transform(next_pred)[0][0]

    return float(next_pred_inv), float(mae), float(rmse)

# ================= GENERATE PREDIKSI PENJUALAN =================
@app.route("/prediksi/penjualan/generate", methods=["POST"])
def generate_prediksi_penjualan():
    if session.get("role") != "umkm":
        return redirect("/login")

    umkm_id = session.get("active_umkm_id")
    if not umkm_id:
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # ===== AMBIL DATA TIME SERIES =====
    cur.execute("""
        SELECT tanggal, SUM(jumlah) AS total
        FROM penjualan p
        JOIN produk pr ON p.produk_id = pr.id
        WHERE pr.umkm_id = %s
        GROUP BY tanggal
        ORDER BY tanggal ASC
    """, (umkm_id,))
    rows = cur.fetchall()

    if len(rows) < 10:
        cur.close()
        db.close()
        return redirect("/prediksi/penjualan")

    sales_series = [r["total"] for r in rows]

    # ===== LSTM PROCESS =====
    hasil, mae, rmse = lstm_predict_sales(sales_series)

    if hasil is None:
        cur.close()
        db.close()
        return redirect("/prediksi/penjualan")

    # ===== SIMPAN KE DATABASE =====
    cur.execute("""
        INSERT INTO prediksi_penjualan
        (produk_id, tanggal_prediksi, hasil_prediksi, mae, rmse, created_at)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        None,
        datetime.now().date(),
        hasil,
        mae,
        rmse,
        datetime.now()
    ))
    db.commit()

    log_activity(session["user_id"], "generate_prediksi_penjualan_lstm")

    cur.close()
    db.close()

    return redirect("/prediksi/penjualan")


# ================= REKOMENDASI PRODUK =================
@app.route("/rekomendasi/produk", methods=["GET"])
def umkm_rekomendasi_produk():
    if session.get("role") != "umkm":
        return redirect("/login")

    if not session.get("active_umkm_id"):
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT r.created_at, p.nama_produk,
               r.rekomendasi, r.alasan
        FROM rekomendasi_produk r
        JOIN produk p ON r.produk_id = p.id
        WHERE p.umkm_id = %s
        ORDER BY r.created_at DESC
    """, (session["active_umkm_id"],))

    rekomendasi = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "umkm/rekomendasi_produk.html",
        rekomendasi=rekomendasi
    )

@app.route("/rekomendasi/produk/generate", methods=["POST"])
def generate_rekomendasi_produk():
    if session.get("role") != "umkm":
        return redirect("/login")

    umkm_id = session.get("active_umkm_id")
    if not umkm_id:
        return redirect("/umkm/dashboard")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ambil data produk + penjualan 30 hari
    cur.execute("""
        SELECT p.id, p.nama_produk, p.stok,
               IFNULL(SUM(j.jumlah), 0) AS total_jual
        FROM produk p
        LEFT JOIN penjualan j
            ON p.id = j.produk_id
            AND j.tanggal >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        WHERE p.umkm_id = %s
        GROUP BY p.id
    """, (umkm_id,))
    produk_list = cur.fetchall()

    for p in produk_list:
        rekomendasi = ""
        alasan = ""

        if p["total_jual"] >= 50 and p["stok"] < 20:
            rekomendasi = "Tambah Stok"
            alasan = "Produk sangat laku dan stok mulai menipis"

        elif p["total_jual"] >= 50:
            rekomendasi = "Pertahankan Stok"
            alasan = "Produk laris dan stabil"

        elif p["total_jual"] < 10:
            rekomendasi = "Promosikan Produk"
            alasan = "Penjualan rendah dalam 30 hari terakhir"

        else:
            rekomendasi = "Evaluasi Produk"
            alasan = "Performa penjualan sedang"

        cur.execute("""
            INSERT INTO rekomendasi_produk
            (produk_id, rekomendasi, alasan, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (p["id"], rekomendasi, alasan))

    db.commit()
    cur.close()
    db.close()

    return redirect("/rekomendasi/produk")


# ================= API (TETAP ADA) =================
@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard_api():
    user = get_jwt_identity()

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) total FROM produk")
    total_produk = cur.fetchone()["total"]

    cur.execute("SELECT SUM(total_harga) omzet FROM penjualan")
    omzet = cur.fetchone()["omzet"] or 0

    cur.close()
    db.close()

    return jsonify({
        "role": user["role"],
        "total_produk": total_produk,
        "total_omzet": float(omzet)
    })

# ================= RUN =================
if __name__ == "__main__":
    print("REGISTERED ROUTES:")
    print(app.url_map)
    app.run(debug=True)
