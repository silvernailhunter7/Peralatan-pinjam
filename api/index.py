import base64
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = 'bmkg-secret-key-operasional'

# --- DATABASE IN-MEMORY ---
inventory = [
    {"ID": "BMKG-ALT-001", "Nama": "AWS (Automatic Weather Station) Portable", "Kategori": "Meteorologi", "Stok": 3},
    {"ID": "BMKG-ALT-002", "Nama": "Seismometer Portable", "Kategori": "Geofisika", "Stok": 2},
    {"ID": "BMKG-ALT-003", "Nama": "Anemometer Digital", "Kategori": "Meteorologi", "Stok": 5},
    {"ID": "BMKG-ALT-004", "Nama": "Tide Gauge Sensor", "Kategori": "Klimatologi", "Stok": 1}
]

peminjaman = []
bmn_logs = []

# --- TEMPLATE HTML INLINE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Peminjaman Peralatan & BMN - BMKG</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-100 text-slate-800 font-sans min-h-screen pb-12">

    <!-- HEADER TEMA BMKG -->
    <header class="bg-gradient-to-r from-sky-900 via-blue-800 to-sky-900 text-white shadow-lg mb-8">
        <div class="max-w-7xl mx-auto px-4 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center space-x-4">
                <img src="https://www.bmkg.go.id/asset/img/logo/logo-bmkg.png" alt="Logo BMKG" class="h-16 bg-white p-1 rounded-full shadow">
                <div>
                    <h1 class="text-xl md:text-2xl font-bold tracking-wide">SISTEM INTEGRASI PEMINJAMAN & BMN</h1>
                    <p class="text-sky-200 text-sm">Badan Meteorologi, Klimatologi, dan Geofisika</p>
                </div>
            </div>
            <div class="bg-sky-950/60 px-4 py-2 rounded-lg border border-sky-400/30 text-xs text-sky-200">
                <i class="fas fa-circle text-emerald-400 animate-pulse mr-1"></i> Status: <span class="font-semibold text-white">Online Vercel</span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 space-y-8">

        <!-- NOTIFIKASI FLASH -->
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="p-4 rounded-lg text-sm font-semibold shadow-md {% if category == 'success' %}bg-emerald-100 text-emerald-800 border-l-4 border-emerald-500{% elif category == 'warning' %}bg-amber-100 text-amber-800 border-l-4 border-amber-500{% else %}bg-rose-100 text-rose-800 border-l-4 border-rose-500{% endif %}">
                <i class="fas fa-info-circle mr-2"></i> {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- METRICS -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                    <p class="text-xs text-slate-500 font-semibold uppercase">Total Stok Alat</p>
                    <p class="text-2xl font-bold text-sky-900 mt-1">{{ inventory | sum(attribute='Stok') }} Unit</p>
                </div>
                <div class="bg-sky-100 p-3 rounded-lg text-sky-800"><i class="fas fa-boxes text-xl"></i></div>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                    <p class="text-xs text-slate-500 font-semibold uppercase">Sedang Dipinjam</p>
                    <p class="text-2xl font-bold text-amber-600 mt-1">{{ active_peminjaman | length }} Transaksi</p>
                </div>
                <div class="bg-amber-100 p-3 rounded-lg text-amber-800"><i class="fas fa-hand-holding text-xl"></i></div>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                    <p class="text-xs text-slate-500 font-semibold uppercase">Jenis Alat</p>
                    <p class="text-2xl font-bold text-slate-800 mt-1">{{ inventory | length }} Kategori</p>
                </div>
                <div class="bg-slate-100 p-3 rounded-lg text-slate-700"><i class="fas fa-microchip text-xl"></i></div>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                    <p class="text-xs text-slate-500 font-semibold uppercase">Log BMN</p>
                    <p class="text-2xl font-bold text-emerald-600 mt-1">{{ bmn_logs | length }} Catatan</p>
                </div>
                <div class="bg-emerald-100 p-3 rounded-lg text-emerald-800"><i class="fas fa-clipboard-list text-xl"></i></div>
            </div>
        </section>

        <!-- PORTAL PEMINJAMAN & PENGEMBALIAN -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div class="flex items-center justify-between border-b pb-4 mb-6">
                    <h2 class="text-lg font-bold text-sky-900"><i class="fas fa-qrcode mr-2"></i> Portal Layanan Peralatan</h2>
                    <span class="text-xs bg-sky-100 text-sky-800 font-semibold px-3 py-1 rounded-full">Universal Portal</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <!-- Form Pinjam -->
                    <form action="/pinjam" method="POST" class="space-y-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                        <h3 class="font-bold text-slate-700 text-sm flex items-center"><i class="fas fa-arrow-up-from-bracket text-sky-700 mr-2"></i> Form Peminjaman Alat</h3>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Peminjam / Personel</label>
                            <input type="text" name="nama" required class="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-sky-500 outline-none" placeholder="Masukkan Nama Lengkap">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Pilih Peralatan Operasional</label>
                            <select name="nama_alat" required class="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-sky-500 outline-none bg-white">
                                {% for item in inventory %}
                                <option value="{{ item.Nama }}">{{ item.Nama }} (Sisa: {{ item.Stok }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Jumlah Unit</label>
                            <input type="number" name="jumlah" min="1" value="1" required class="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-sky-500 outline-none">
                        </div>
                        <button type="submit" class="w-full bg-sky-800 hover:bg-sky-900 text-white font-semibold py-2 rounded-lg text-sm transition"><i class="fas fa-paper-plane mr-1"></i> Submit Peminjaman</button>
                    </form>

                    <!-- Form Kembali -->
                    <form action="/kembali" method="POST" class="space-y-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                        <h3 class="font-bold text-slate-700 text-sm flex items-center"><i class="fas fa-arrow-down-to-bracket text-emerald-700 mr-2"></i> Form Pengembalian Alat</h3>
                        {% if active_peminjaman %}
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Pilih Transaksi Aktif</label>
                            <select name="pilihan_transaksi" required class="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none bg-white">
                                {% for p in active_peminjaman %}
                                <option value="{{ p.Index }}">{{ p.NamaPeminjam }} - {{ p.NamaAlat }} ({{ p.Jumlah }} Unit)</option>
                                {% endfor %}
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-2 rounded-lg text-sm transition"><i class="fas fa-check-circle mr-1"></i> Proses Pengembalian</button>
                        {% else %}
                        <div class="p-6 text-center text-slate-400 text-xs border-2 border-dashed border-slate-200 rounded-lg">
                            Tidak ada alat yang sedang dipinjam saat ini.
                        </div>
                        {% endif %}
                    </form>
                </div>
            </div>

            <!-- TAMPILAN QR UNIVERSAL -->
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col items-center justify-center text-center">
                <h3 class="font-bold text-sky-900 mb-2">QR Code Portal Layanan</h3>
                <p class="text-xs text-slate-500 mb-4">Scan QR code ini via HP untuk langsung mengakses portal peminjaman & pengembalian alat.</p>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl mb-3 shadow-inner">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https://pinjam-peralatan-ten.vercel.app" alt="QR Code Portal" class="w-44 h-44">
                </div>
                <span class="text-[10px] text-slate-400 font-mono">BMKG Universal QR Code System</span>
            </div>
        </section>

        <!-- TRACKER TABEL STOK & LOG -->
        <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
            <div>
                <h3 class="font-bold text-sky-900 mb-4 flex items-center"><i class="fas fa-list-check mr-2"></i> Status Ketersediaan Stok Alat BMKG</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-slate-600 border">
                        <thead class="text-xs uppercase bg-sky-900 text-white">
                            <tr>
                                <th class="px-4 py-3">ID Alat</th>
                                <th class="px-4 py-3">Nama Peralatan Operasional</th>
                                <th class="px-4 py-3">Kategori</th>
                                <th class="px-4 py-3">Sisa Stok</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            {% for item in inventory %}
                            <tr class="hover:bg-slate-50">
                                <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ item.ID }}</td>
                                <td class="px-4 py-3 font-semibold text-slate-800">{{ item.Nama }}</td>
                                <td class="px-4 py-3"><span class="bg-sky-100 text-sky-800 text-xs font-semibold px-2.5 py-0.5 rounded">{{ item.Kategori }}</span></td>
                                <td class="px-4 py-3 font-bold {% if item.Stok > 0 %}text-emerald-600{% else %}text-rose-600{% endif %}">{{ item.Stok }} Unit</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div>
                <h3 class="font-bold text-sky-900 mb-4 flex items-center"><i class="fas fa-history mr-2"></i> Riwayat Transaksi Peminjaman & Pengembalian</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-slate-600 border">
                        <thead class="text-xs uppercase bg-slate-800 text-white">
                            <tr>
                                <th class="px-4 py-3">Timestamp Pinjam</th>
                                <th class="px-4 py-3">Timestamp Kembali</th>
                                <th class="px-4 py-3">Peminjam</th>
                                <th class="px-4 py-3">Nama Alat</th>
                                <th class="px-4 py-3">Jumlah</th>
                                <th class="px-4 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            {% for p in peminjaman | reverse %}
                            <tr class="hover:bg-slate-50">
                                <td class="px-4 py-3 font-mono text-xs">{{ p.TimestampPinjam }}</td>
                                <td class="px-4 py-3 font-mono text-xs">{{ p.TimestampKembali }}</td>
                                <td class="px-4 py-3 font-semibold">{{ p.NamaPeminjam }}</td>
                                <td class="px-4 py-3">{{ p.NamaAlat }}</td>
                                <td class="px-4 py-3">{{ p.Jumlah }}</td>
                                <td class="px-4 py-3">
                                    {% if p.Status == 'Dipinjam' %}
                                    <span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-0.5 rounded">Dipinjam</span>
                                    {% else %}
                                    <span class="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-0.5 rounded">Dikembalikan</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="6" class="text-center py-4 text-slate-400 text-xs">Belum ada riwayat transaksi peminjaman.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ADMIN MODUL BMN -->
        <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 class="text-lg font-bold text-sky-900 mb-6 pb-2 border-b"><i class="fas fa-boxes-packing mr-2"></i> Admin BMN (Barang Masuk & Keluar)</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
                <!-- BMN Masuk -->
                <form action="/bmn_masuk" method="POST" class="space-y-4 bg-emerald-50/50 p-4 rounded-xl border border-emerald-200">
                    <h3 class="font-bold text-emerald-800 text-sm"><i class="fas fa-plus-circle mr-1"></i> Form Catat BMN Masuk</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <input type="text" name="id_bmn" required placeholder="Kode BMN" class="px-3 py-2 text-sm border rounded-lg">
                        <input type="text" name="nama_bmn" required placeholder="Nama BMN" class="px-3 py-2 text-sm border rounded-lg">
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <input type="number" name="jumlah" min="1" value="1" required placeholder="Jumlah Unit" class="px-3 py-2 text-sm border rounded-lg">
                        <input type="text" name="sumber" required placeholder="Sumber Pengadaan" class="px-3 py-2 text-sm border rounded-lg">
                    </div>
                    <button type="submit" class="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-2 rounded-lg text-sm">Simpan BMN Masuk</button>
                </form>

                <!-- BMN Keluar -->
                <form action="/bmn_keluar" method="POST" class="space-y-4 bg-amber-50/50 p-4 rounded-xl border border-amber-200">
                    <h3 class="font-bold text-amber-800 text-sm"><i class="fas fa-minus-circle mr-1"></i> Form Catat BMN Keluar</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <input type="text" name="id_bmn" required placeholder="Kode BMN" class="px-3 py-2 text-sm border rounded-lg">
                        <input type="text" name="nama_bmn" required placeholder="Nama BMN" class="px-3 py-2 text-sm border rounded-lg">
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <input type="number" name="jumlah" min="1" value="1" required placeholder="Jumlah Unit" class="px-3 py-2 text-sm border rounded-lg">
                        <input type="text" name="tujuan" required placeholder="Tujuan Penyaluran" class="px-3 py-2 text-sm border rounded-lg">
                    </div>
                    <button type="submit" class="w-full bg-amber-700 hover:bg-amber-800 text-white font-semibold py-2 rounded-lg text-sm">Simpan BMN Keluar</button>
                </form>
            </div>

            <!-- Tabel BMN Logs -->
            <h3 class="font-bold text-slate-700 text-sm mb-3">Tabel Mutasi Transaksi BMN</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-600 border">
                    <thead class="text-xs uppercase bg-slate-100 text-slate-700">
                        <tr>
                            <th class="px-4 py-2">Timestamp</th>
                            <th class="px-4 py-2">Jenis</th>
                            <th class="px-4 py-2">Kode BMN</th>
                            <th class="px-4 py-2">Nama BMN</th>
                            <th class="px-4 py-2">Jumlah</th>
                            <th class="px-4 py-2">Sumber / Tujuan</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200">
                        {% for log in bmn_logs | reverse %}
                        <tr class="hover:bg-slate-50">
                            <td class="px-4 py-2 font-mono text-xs">{{ log.Timestamp }}</td>
                            <td class="px-4 py-2 font-bold {% if log.Jenis == 'MASUK' %}text-emerald-600{% else %}text-amber-600{% endif %}">{{ log.Jenis }}</td>
                            <td class="px-4 py-2 font-mono text-xs">{{ log.ID }}</td>
                            <td class="px-4 py-2">{{ log.Nama }}</td>
                            <td class="px-4 py-2">{{ log.Jumlah }}</td>
                            <td class="px-4 py-2">{{ log.TujuanSumber }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="6" class="text-center py-4 text-slate-400 text-xs">Belum ada riwayat transaksi BMN.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>

    </main>

    <footer class="mt-12 text-center text-xs text-slate-400">
        <p>&copy; BMKG - Sistem Operasional Peminjaman Peralatan & Manajemen BMN</p>
    </footer>

</body>
</html>
"""

@app.route('/')
def home():
    try:
        active_peminjaman = [p for p in peminjaman if p.get('Status') == 'Dipinjam']
        return render_template_string(
            HTML_TEMPLATE,
            inventory=inventory,
            peminjaman=peminjaman,
            active_peminjaman=active_peminjaman,
            bmn_logs=bmn_logs
        )
    except Exception as e:
        return f"System Error: {str(e)}", 500

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

# Error Handler global untuk mencegah 500 Unhandled Exception
@app.errorhandler(500)
def server_error(e):
    return f"<h3>Internal Error Tercatat</h3><p>{str(e)}</p>", 500

if __name__ == '__main__':
    app.run(debug=True)
