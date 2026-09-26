import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'bmkg-secret-key-operasional'

# --- DATABASE IN-MEMORY ---
inventory = [
    {"ID": "BMKG-ALT-001", "Nama": "AWS (Automatic Weather Station) Portable", "Kategori": "Meteorologi", "Stok": 3, "Gambar": None},
    {"ID": "BMKG-ALT-002", "Nama": "Seismometer Portable", "Kategori": "Geofisika", "Stok": 2, "Gambar": None},
    {"ID": "BMKG-ALT-003", "Nama": "Anemometer Digital", "Kategori": "Meteorologi", "Stok": 5, "Gambar": None},
    {"ID": "BMKG-ALT-004", "Nama": "Tide Gauge Sensor", "Kategori": "Klimatologi", "Stok": 1, "Gambar": None}
]

peminjaman = []
bmn_logs = []

@app.route('/')
def home():
    active_peminjaman = [p for p in peminjaman if p['Status'] == 'Dipinjam']
    return render_template(
        'index.html',
        inventory=inventory,
        peminjaman=peminjaman,
        active_peminjaman=active_peminjaman,
        bmn_logs=bmn_logs
    )

@app.route('/pinjam', methods=['POST'])
def pinjam():
    nama = request.form.get('nama')
    nama_alat = request.form.get('nama_alat')
    jumlah = int(request.form.get('jumlah', 1))
    
    item = next((i for i in inventory if i['Nama'] == nama_alat), None)
    if item and item['Stok'] >= jumlah:
        item['Stok'] -= jumlah
        peminjaman.append({
            'Index': len(peminjaman),
            'TimestampPinjam': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'TimestampKembali': '-',
            'NamaPeminjam': nama,
            'IDAlat': item['ID'],
            'NamaAlat': item['Nama'],
            'Jumlah': jumlah,
            'Status': 'Dipinjam'
        })
        flash('Peminjaman berhasil dicatat!', 'success')
    else:
        flash('Stok alat tidak mencukupi!', 'danger')
    return redirect(url_for('home'))

@app.route('/kembali', methods=['POST'])
def kembali():
    idx_str = request.form.get('pilihan_transaksi')
    if idx_str is not None and idx_str.isdigit():
        idx = int(idx_str)
        if 0 <= idx < len(peminjaman) and peminjaman[idx]['Status'] == 'Dipinjam':
            tx = peminjaman[idx]
            tx['Status'] = 'Dikembalikan'
            tx['TimestampKembali'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            item = next((i for i in inventory if i['Nama'] == tx['NamaAlat']), None)
            if item:
                item['Stok'] += tx['Jumlah']
            flash('Pengembalian berhasil diproses!', 'success')
    return redirect(url_for('home'))

@app.route('/tambah_alat', methods=['POST'])
def tambah_alat():
    id_alat = request.form.get('id_alat')
    nama_alat = request.form.get('nama_alat')
    kategori = request.form.get('kategori')
    stok = int(request.form.get('stok', 1))
    
    file_gambar = request.files.get('gambar')
    gambar_b64 = None
    if file_gambar and file_gambar.filename != '':
        gambar_b64 = base64.b64encode(file_gambar.read()).decode('utf-8')
        
    inventory.append({
        "ID": id_alat,
        "Nama": nama_alat,
        "Kategori": kategori,
        "Stok": stok,
        "Gambar": gambar_b64
    })
    flash('Peralatan baru berhasil ditambahkan!', 'success')
    return redirect(url_for('home'))

@app.route('/bmn_masuk', methods=['POST'])
def bmn_masuk():
    bmn_logs.append({
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Jenis': 'MASUK',
        'ID': request.form.get('id_bmn'),
        'Nama': request.form.get('nama_bmn'),
        'Jumlah': request.form.get('jumlah'),
        'TujuanSumber': request.form.get('sumber')
    })
    flash('Pencatatan BMN Masuk berhasil!', 'success')
    return redirect(url_for('home'))

@app.route('/bmn_keluar', methods=['POST'])
def bmn_keluar():
    bmn_logs.append({
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Jenis': 'KELUAR',
        'ID': request.form.get('id_bmn'),
        'Nama': request.form.get('nama_bmn'),
        'Jumlah': request.form.get('jumlah'),
        'TujuanSumber': request.form.get('tujuan')
    })
    flash('Pencatatan BMN Keluar berhasil!', 'warning')
    return redirect(url_for('home'))

# Eksplisit untuk Vercel Serverless Function Engine
app = app

if __name__ == '__main__':
    app.run(debug=True)
