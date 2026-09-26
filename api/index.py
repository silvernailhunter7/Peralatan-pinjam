from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import qrcode
import io
import base64
app = Flask(name, template_folder='../templates')
app.secret_key = 'bmkg_secret_key_operasional'
==========================================
DATABASE IN-MEMORY / SESSION STATE
==========================================
inventory = [
{"id": "BMKG-ALT-001", "nama": "AWS (Automatic Weather Station) Portable", "kategori": "Meteorologi", "stok": 3, "gambar": None},
{"id": "BMKG-ALT-002", "nama": "Seismometer Portable", "kategori": "Geofisika", "stok": 2, "gambar": None},
{"id": "BMKG-ALT-003", "nama": "Anemometer Digital", "kategori": "Meteorologi", "stok": 5, "gambar": None},
{"id": "BMKG-ALT-004", "nama": "Tide Gauge Sensor", "kategori": "Klimatologi", "stok": 1, "gambar": None}
]
peminjaman_logs = []
bmn_logs = []
def generate_qr(data_url):
qr = qrcode.QRCode(version=1, box_size=5, border=2)
qr.add_data(data_url)
qr.make(fit=True)
img = qr.make_image(fill_color="#0f4c81", back_color="white")
buf = io.BytesIO()
img.save(buf)
return base64.b64encode(buf.getvalue()).decode('utf-8')


@app.route('/')
def home():
# Hitung statistik
total_stok = sum([item['stok'] for item in inventory])
total_dipinjam = sum([1 for log in peminjaman_logs if log['status'] == 'Dipinjam'])
total_dikembalikan = sum([1 for log in peminjaman_logs if log['status'] == 'Dikembalikan'])
# URL Universal QR
host_url = request.host_url
qr_b64 = generate_qr(host_url)

return render_template(
    'index.html',
    inventory=inventory,
    peminjaman_logs=peminjaman_logs,
    bmn_logs=bmn_logs,
    total_stok=total_stok,
    total_dipinjam=total_dipinjam,
    total_dikembalikan=total_dikembalikan,
    qr_b64=qr_b64
)


@app.route('/pinjam', methods=['POST'])
def pinjam_alat():
nama_peminjam = request.form.get('nama_peminjam')
alat_id = request.form.get('alat_id')
jumlah = int(request.form.get('jumlah', 1))
# Cari alat di inventaris
item = next((x for x in inventory if x['id'] == alat_id), None)
if item and item['stok'] >= jumlah:
    item['stok'] -= jumlah
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    peminjaman_logs.insert(0, {
        "id": len(peminjaman_logs) + 1,
        "timestamp_pinjam": timestamp,
        "timestamp_kembali": "-",
        "peminjam": nama_peminjam,
        "alat_id": item['id'],
        "nama_alat": item['nama'],
        "jumlah": jumlah,
        "status": "Dipinjam"
    })
    flash(f"Peminjaman {item['nama']} berhasil dicatat!", "success")
else:
    flash("Stok peralatan tidak mencukupi!", "danger")
    
return redirect(url_for('home'))


@app.route('/kembali', methods=['POST'])
def kembali_alat():
log_id = int(request.form.get('log_id'))
log = next((x for x in peminjaman_logs if x['id'] == log_id), None)
if log and log['status'] == 'Dipinjam':
    # Kembalikan stok
    item = next((x for x in inventory if x['id'] == log['alat_id']), None)
    if item:
        item['stok'] += log['jumlah']
        
    log['status'] = "Dikembalikan"
    log['timestamp_kembali'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flash(f"Peralatan {log['nama_alat']} berhasil dikembalikan!", "success")

return redirect(url_for('home'))


@app.route('/admin/tambah-alat', methods=['POST'])
def tambah_alat():
id_alat = request.form.get('id_alat')
nama_alat = request.form.get('nama_alat')
kategori = request.form.get('kategori')
stok = int(request.form.get('stok', 1))
file_gambar = request.files.get('gambar')
img_b64 = None
if file_gambar and file_gambar.filename != '':
    img_bytes = file_gambar.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
inventory.append({
    "id": id_alat,
    "nama": nama_alat,
    "kategori": kategori,
    "stok": stok,
    "gambar": img_b64
})
flash("Jenis peralatan baru berhasil ditambahkan!", "success")
return redirect(url_for('home'))


@app.route('/admin/bmn', methods=['POST'])
def transaksi_bmn():
jenis = request.form.get('jenis_transaksi')
id_bmn = request.form.get('id_bmn')
nama_bmn = request.form.get('nama_bmn')
jumlah = int(request.form.get('jumlah', 1))
tujuan_sumber = request.form.get('tujuan_sumber')
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
bmn_logs.insert(0, {
    "timestamp": timestamp,
    "jenis": jenis,
    "id_bmn": id_bmn,
    "nama_bmn": nama_bmn,
    "jumlah": jumlah,
    "tujuan_sumber": tujuan_sumber
})
flash(f"Transaksi BMN {jenis} berhasil dicatat!", "success")
return redirect(url_for('home'))


if name == 'main':
app.run(debug=True)
