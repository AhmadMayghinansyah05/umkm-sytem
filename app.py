from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'umkm-secret-key-2024-change-this'

# Dummy Users
USERS = {
    'pelaku@umkm.com': {'password': 'pelaku123', 'role': 'pelaku', 'name': 'Toko Berkah Jaya'},
    'admin@umkm.com': {'password': 'admin123', 'role': 'admin', 'name': 'Super Admin'}
}

# Helper Functions
def generate_sales_data():
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun']
    data = []
    base = 4200000
    for month in months:
        actual = base + random.randint(-200000, 400000)
        prediction = actual + random.randint(-100000, 100000)
        data.append({'month': month, 'actual': actual, 'prediction': prediction})
        base += 300000
    return data

def get_top_products():
    return [
        {'name': 'Kopi Arabika', 'sales': 1250000, 'growth': 12, 'stock': 45},
        {'name': 'Teh Herbal', 'sales': 980000, 'growth': 8, 'stock': 32},
        {'name': 'Keripik Singkong', 'sales': 850000, 'growth': -3, 'stock': 78},
        {'name': 'Sambal Matah', 'sales': 720000, 'growth': 15, 'stock': 23},
        {'name': 'Abon Sapi', 'sales': 650000, 'growth': 5, 'stock': 56}
    ]

def get_activities():
    return [
        {'desc': 'Penjualan Kopi Arabika - 15 unit', 'time': '10 menit lalu', 'status': 'success'},
        {'desc': 'Prediksi penjualan tersedia', 'time': '2 jam lalu', 'status': 'info'},
        {'desc': 'Stok Sambal Matah menipis', 'time': '3 jam lalu', 'status': 'warning'},
        {'desc': 'Penjualan Teh Herbal - 8 unit', 'time': '5 jam lalu', 'status': 'success'}
    ]

def get_umkm_list():
    return [
        {'name': 'Toko Berkah Jaya', 'category': 'Makanan & Minuman', 'date': '2 jam lalu', 'status': 'active', 'sales': 'Rp 45.2jt'},
        {'name': 'Warung Sari Rasa', 'category': 'Kuliner', 'date': '5 jam lalu', 'status': 'active', 'sales': 'Rp 32.8jt'},
        {'name': 'Kopi Kenangan Kita', 'category': 'Minuman', 'date': '1 hari lalu', 'status': 'pending', 'sales': 'Rp 28.5jt'},
        {'name': 'Batik Nusantara', 'category': 'Fashion', 'date': '1 hari lalu', 'status': 'active', 'sales': 'Rp 18.3jt'},
        {'name': 'Kerajinan Tangan', 'category': 'Handicraft', 'date': '2 hari lalu', 'status': 'active', 'sales': 'Rp 15.7jt'}
    ]

def get_model_performance():
    return [
        {'metric': 'Prediksi Penjualan', 'accuracy': 92, 'status': 'excellent'},
        {'metric': 'Rekomendasi Produk', 'accuracy': 88, 'status': 'good'},
        {'metric': 'Analisis Tren', 'accuracy': 85, 'status': 'good'},
        {'metric': 'Clustering Pelanggan', 'accuracy': 90, 'status': 'excellent'}
    ]

def get_recommended_products():
    return [
        {'name': 'Kopi Arabika Premium', 'category': 'Makanan & Minuman', 'match': 95},
        {'name': 'Teh Herbal Organik', 'category': 'Makanan & Minuman', 'match': 90},
        {'name': 'Snack Keripik Singkong', 'category': 'Makanan & Minuman', 'match': 85},
        {'name': 'Sambal Matah Kemasan', 'category': 'Makanan & Minuman', 'match': 80},
        {'name': 'Abon Sapi Spesial', 'category': 'Makanan & Minuman', 'match': 75},
        {'name': 'Kerupuk Udang', 'category': 'Makanan & Minuman', 'match': 70}
    ]

# Routes
@app.route('/')
def index():
    if 'user' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS and USERS[email]['password'] == password:
            session['user'] = email
            session['role'] = USERS[email]['role']
            session['name'] = USERS[email]['name']
            
            if USERS[email]['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        
        error = 'Email atau password salah'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Pelaku UMKM Routes
@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['role'] != 'pelaku':
        return redirect(url_for('login'))
    
    return render_template('dashboard.html',
        user_name=session['name'],
        sales_data=generate_sales_data(),
        top_products=get_top_products(),
        activities=get_activities()
    )

@app.route('/input-penjualan', methods=['GET', 'POST'])
def input_penjualan():
    if 'user' not in session or session['role'] != 'pelaku':
        return redirect(url_for('login'))
    
    success = False
    if request.method == 'POST':
        success = True
    
    return render_template('input_penjualan.html', success=success, user_name=session['name'])

@app.route('/prediksi')
def prediksi():
    if 'user' not in session or session['role'] != 'pelaku':
        return redirect(url_for('login'))
    
    prediction = {
        'next_month': 63500000,
        'confidence': 92,
        'trend': 'naik',
        'sales_data': generate_sales_data()
    }
    return render_template('prediksi.html', prediction=prediction, user_name=session['name'])

@app.route('/rekomendasi')
def rekomendasi():
    if 'user' not in session or session['role'] != 'pelaku':
        return redirect(url_for('login'))
    
    return render_template('rekomendasi.html', products=get_recommended_products(), user_name=session['name'])

# Activity Log Routes - PELAKU UMKM
@app.route('/aktivitas-log')
def aktivitas_log():
    if 'user' not in session or session['role'] != 'pelaku':
        return redirect(url_for('login'))
    
    logs = [
        {'action': 'Login ke sistem', 'timestamp': '2024-12-20 08:30:15', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Input data penjualan - Rp 2,400,000', 'timestamp': '2024-12-20 09:15:42', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Lihat prediksi penjualan', 'timestamp': '2024-12-20 10:05:23', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Akses dashboard analitik', 'timestamp': '2024-12-20 11:20:18', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Lihat rekomendasi produk', 'timestamp': '2024-12-20 13:45:09', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Input data penjualan - Rp 1,800,000', 'timestamp': '2024-12-20 14:30:55', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Export laporan penjualan', 'timestamp': '2024-12-20 15:10:33', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Update profil akun', 'timestamp': '2024-12-19 16:25:47', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Gagal login - password salah', 'timestamp': '2024-12-19 08:12:05', 'ip': '192.168.1.15', 'status': 'failed'},
        {'action': 'Login ke sistem', 'timestamp': '2024-12-19 08:13:22', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Lihat dashboard', 'timestamp': '2024-12-19 09:00:11', 'ip': '192.168.1.10', 'status': 'success'},
        {'action': 'Input data penjualan - Rp 3,200,000', 'timestamp': '2024-12-19 10:45:30', 'ip': '192.168.1.10', 'status': 'success'}
    ]
    
    return render_template('aktivitas_log.html', logs=logs, user_name=session['name'])

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html',
        user_name=session['name'],
        umkm_list=get_umkm_list(),
        activities=get_activities(),
        model_performance=get_model_performance()
    )

@app.route('/admin/umkm')
def admin_umkm():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_umkm.html', umkm_list=get_umkm_list())

@app.route('/admin/products')
def admin_products():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_products.html', products=get_top_products())

# Activity Log Routes - ADMIN
@app.route('/admin/aktivitas-log')
def admin_aktivitas_log():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    logs = [
        {'user': 'admin@umkm.com', 'action': 'Login ke admin panel', 'timestamp': '2024-12-20 07:30:15', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Update model LSTM', 'timestamp': '2024-12-20 08:15:42', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Tambah UMKM baru: Warung Berkah', 'timestamp': '2024-12-20 09:05:23', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'pelaku@umkm.com', 'action': 'Login ke sistem', 'timestamp': '2024-12-20 08:30:15', 'ip': '192.168.1.10', 'status': 'success'},
        {'user': 'pelaku@umkm.com', 'action': 'Input data penjualan', 'timestamp': '2024-12-20 09:15:42', 'ip': '192.168.1.10', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Hapus produk: Kerupuk Bawang', 'timestamp': '2024-12-20 10:20:18', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Export data semua UMKM', 'timestamp': '2024-12-20 11:45:09', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'pelaku2@umkm.com', 'action': 'Gagal login - akun suspended', 'timestamp': '2024-12-20 12:30:55', 'ip': '192.168.1.20', 'status': 'failed'},
        {'user': 'admin@umkm.com', 'action': 'Monitoring sistem - CPU 45%', 'timestamp': '2024-12-20 13:10:33', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Training model recommendation', 'timestamp': '2024-12-20 14:25:47', 'ip': '192.168.1.5', 'status': 'success'},
        {'user': 'pelaku@umkm.com', 'action': 'Lihat rekomendasi produk', 'timestamp': '2024-12-20 13:45:09', 'ip': '192.168.1.10', 'status': 'success'},
        {'user': 'admin@umkm.com', 'action': 'Backup database', 'timestamp': '2024-12-19 23:00:05', 'ip': '192.168.1.5', 'status': 'success'}
    ]
    
    return render_template('admin_aktivitas_log.html', logs=logs, user_name=session['name'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)