import streamlit as st
import pandas as pd
import qrcode
import io
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA BMKG
# ==========================================
st.set_page_config(
    page_title="Sistem Integrasi Peminjaman & BMN - BMKG",
    page_icon="🌤️",
    layout="wide"
)

# Custom CSS Khas BMKG
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #0f4c81 0%, #1b6ca8 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    .stMetric {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #0f4c81;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. INISIALISASI DATABASE LOKAL (SESSION STATE)
# ==========================================
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"ID": "BMKG-ALT-001", "Nama": "AWS (Automatic Weather Station) Portable", "Kategori": "Meteorologi", "Stok": 3, "Gambar": None},
        {"ID": "BMKG-ALT-002", "Nama": "Seismometer Portable", "Kategori": "Geofisika", "Stok": 2, "Gambar": None},
        {"ID": "BMKG-ALT-003", "Nama": "Anemometer Digital", "Kategori": "Meteorologi", "Stok": 5, "Gambar": None},
        {"ID": "BMKG-ALT-004", "Nama": "Tide Gauge Sensor", "Kategori": "Klimatologi", "Stok": 1, "Gambar": None}
    ])

if 'peminjaman' not in st.session_state:
    st.session_state.peminjaman = pd.DataFrame(columns=[
        "Timestamp Pinjam", "Timestamp Kembali", "Nama Peminjam", "ID Alat", "Nama Alat", "Jumlah", "Status"
    ])

if 'bmn_logs' not in st.session_state:
    st.session_state.bmn_logs = pd.DataFrame(columns=[
        "Timestamp", "Jenis Transaksi", "ID BMN", "Nama BMN", "Jumlah", "Tujuan / Sumber"
    ])


# ==========================================
# 3. HEADER UTAMA TEMA BMKG
# ==========================================
st.markdown("""
    <div class="main-header">
        <h1>🌤️ SISTEM INTEGRASI PEMINJAMAN PERALATAN & MANAJEMEN BMN</h1>
        <h3>Badan Meteorologi, Klimatologi, dan Geofisika</h3>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# 4. SIDEBAR NAVIGASI
# ==========================================
st.sidebar.image("https://www.bmkg.go.id/asset/img/logo/logo-bmkg.png", width=120)
st.sidebar.title("Navigasi Operasional")
menu = st.sidebar.radio(
    "Pilih Modul:",
    ["📌 Portal Universal (Scan QR)", "📊 Dashboard Tracker Peralatan", "⚙️ Admin Kelola Alat", "📦 Admin BMN (Barang Masuk/Keluar)"]
)


# ==========================================
# MODUL 1: PORTAL UNIVERSAL (PEMINJAMAN & PENGEMBALIAN VIA QR)
# ==========================================
if menu == "📌 Portal Universal (Scan QR)":
    
    col_portal, col_qr = st.columns([2, 1])
    
    with col_portal:
        st.subheader("📲 Portal Layanan Peralatan Operasional")
        st.caption("Pilih jenis transaksi layanan peralatan yang ingin dilakukan di bawah ini.")
        
        jenis_layanan = st.radio(
            "Pilih Aksi Transaksi:",
            ["📤 Meminjam Peralatan", "📥 Mengembalikan Peralatan"],
            horizontal=True
        )
        
        st.markdown("---")
        
        # --- A. MEMINJAM PERALATAN ---
        if jenis_layanan == "📤 Meminjam Peralatan":
            st.markdown("#### Form Peminjaman Alat")
            with st.form("form_peminjaman"):
                nama_peminjam = st.text_input("Nama Lengkap Peminjam / Personel")
                
                opsi_alat = st.session_state.inventory["Nama"].tolist()
                alat_dipilih = st.selectbox("Cari & Pilih Jenis Peralatan BMKG:", opsi_alat)
                
                jumlah_pinjam = st.number_input("Jumlah Unit Dipinjam", min_value=1, step=1)
                
                submit_pinjam = st.form_submit_button("🚀 Ajukan Peminjaman")
                
                if submit_pinjam:
                    if not nama_peminjam.strip():
                        st.error("Nama Peminjam wajib diisi!")
                    else:
                        idx = st.session_state.inventory[st.session_state.inventory["Nama"] == alat_dipilih].index[0]
                        stok_tersedia = st.session_state.inventory.loc[idx, "Stok"]
                        
                        if jumlah_pinjam <= stok_tersedia:
                            st.session_state.inventory.loc[idx, "Stok"] -= jumlah_pinjam
                            
                            timestamp_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            id_alat = st.session_state.inventory.loc[idx, "ID"]
                            
                            new_log = pd.DataFrame([{
                                "Timestamp Pinjam": timestamp_sekarang,
                                "Timestamp Kembali": "-",
                                "Nama Peminjam": nama_peminjam,
                                "ID Alat": id_alat,
                                "Nama Alat": alat_dipilih,
                                "Jumlah": jumlah_pinjam,
                                "Status": "Dipinjam"
                            }])
                            st.session_state.peminjaman = pd.concat([st.session_state.peminjaman, new_log], ignore_index=True)
                            
                            st.success(f"Peminjaman berhasil dicatat pada {timestamp_sekarang}!")
                            st.rerun()
                        else:
                            st.error("Stok alat tidak mencukupi untuk peminjaman ini!")

        # --- B. MENGEMBALIKAN PERALATAN ---
        elif jenis_layanan == "📥 Mengembalikan Peralatan":
            st.markdown("#### Form Pengembalian Alat")
            
            df_dipinjam = st.session_state.peminjaman[st.session_state.peminjaman["Status"] == "Dipinjam"]
            
            if df_dipinjam.empty:
                st.info("Saat ini tidak ada peralatan yang sedang dipinjam.")
            else:
                with st.form("form_pengembalian"):
                    opsi_pengembalian = df_dipinjam.apply(
                        lambda x: f"{x.name} | {x['Nama Peminjam']} - {x['Nama Alat']} ({x['Jumlah']} Unit) - Tgl: {x['Timestamp Pinjam']}",
                        axis=1
                    ).tolist()
                    
                    pilihan_transaksi = st.selectbox("Cari & Pilih Transaksi Peminjaman yang Akan Dikembalikan:", opsi_pengembalian)
                    
                    submit_kembali = st.form_submit_button("✅ Proses Pengembalian Alat")
                    
                    if submit_kembali:
                        idx_peminjaman = int(pilihan_transaksi.split(" | ")[0])
                        
                        nama_alat = st.session_state.peminjaman.loc[idx_peminjaman, "Nama Alat"]
                        jumlah_kembali = st.session_state.peminjaman.loc[idx_peminjaman, "Jumlah"]
                        
                        idx_inv = st.session_state.inventory[st.session_state.inventory["Nama"] == nama_alat].index[0]
                        st.session_state.inventory.loc[idx_inv, "Stok"] += jumlah_kembali
                        
                        timestamp_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.peminjaman.loc[idx_peminjaman, "Status"] = "Dikembalikan"
                        st.session_state.peminjaman.loc[idx_peminjaman, "Timestamp Kembali"] = timestamp_sekarang
                        
                        st.success(f"Peralatan {nama_alat} berhasil dikembalikan pada {timestamp_sekarang}!")
                        st.rerun()

    with col_qr:
        st.subheader("📱 QR Code Universal")
        st.write("Scan QR ini untuk langsung mengakses Portal Layanan via HP.")
        
        qr_data = "https://bmkg-peminjaman.vercel.app"
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="#0f4c81", back_color="white")
        
        buf = io.BytesIO()
        img_qr.save(buf)
        st.image(buf.getvalue(), caption="Scan QR Universal", width=220)


# ==========================================
# MODUL 2: DASHBOARD TRACKER PERALATAN
# ==========================================
elif menu == "📊 Dashboard Tracker Peralatan":
    st.title("📊 Tracker Pemantauan Peralatan & Peminjaman")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    total_alat = st.session_state.inventory["Stok"].sum()
    total_dipinjam = len(st.session_state.peminjaman[st.session_state.peminjaman["Status"] == "Dipinjam"])
    total_kembali = len(st.session_state.peminjaman[st.session_state.peminjaman["Status"] == "Dikembalikan"])
    
    col_m1.metric("Total Unit Tersedia", f"{total_alat} Unit")
    col_m2.metric("Sedang Dipinjam", f"{total_dipinjam} Transaksi")
    col_m3.metric("Selesai Dikembalikan", f"{total_kembali} Transaksi")
    col_m4.metric("Status Sistem", "🟢 Operasional")
    
    st.markdown("---")
    
    st.subheader("📋 Status Stok Peralatan Operasional BMKG")
    st.dataframe(st.session_state.inventory[["ID", "Nama", "Kategori", "Stok"]], use_container_width=True)
    
    st.subheader("⏱️ Riwayat Transaksi Peminjaman & Pengembalian")
    if not st.session_state.peminjaman.empty:
        st.dataframe(
            st.session_state.peminjaman.sort_values(by="Timestamp Pinjam", ascending=False),
            use_container_width=True
        )
    else:
        st.info("Belum ada riwayat transaksi peralatan.")


# ==========================================
# MODUL 3: ADMIN KELOLA ALAT
# ==========================================
elif menu == "⚙️ Admin Kelola Alat":
    st.title("⚙️ Pengelolaan Inventaris Peralatan")
    
    st.subheader("➕ Tambah Jenis & Upload Gambar Peralatan")
    with st.form("form_tambah_alat"):
        col_a, col_b = st.columns(2)
        with col_a:
            id_baru = st.text_input("ID / Kode Peralatan (Contoh: BMKG-ALT-005)")
            nama_baru = st.text_input("Nama Peralatan Operasional")
            kategori_baru = st.selectbox("Kategori BMKG", ["Meteorologi", "Klimatologi", "Geofisika", "Pendukung Operasional"])
        with col_b:
            stok_baru = st.number_input("Jumlah Stok Awal", min_value=1, step=1)
            gambar_upload = st.file_uploader("Upload Foto Alat", type=["jpg", "jpeg", "png"])
            
        submit_tambah = st.form_submit_button("Simpan Alat Baru")
        
        if submit_tambah:
            img_bytes = None
            if gambar_upload is not None:
                img_bytes = gambar_upload.read()
                
            new_item = pd.DataFrame([{
                "ID": id_baru,
                "Nama": nama_baru,
                "Kategori": kategori_baru,
                "Stok": stok_baru,
                "Gambar": img_bytes
            }])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
            st.success("Peralatan baru berhasil ditambahkan!")
            st.rerun()

    st.markdown("---")
    
    st.subheader("🖼️ Katalog & Visual Peralatan Terdaftar")
    cols = st.columns(3)
    for idx, row in st.session_state.inventory.iterrows():
        with cols[idx % 3]:
            st.markdown(f"**{row['Nama']}**")
            st.caption(f"ID: {row['ID']} | Kategori: {row['Kategori']}")
            st.write(f"Sisa Stok: **{row['Stok']}** Unit")
            if row['Gambar'] is not None:
                st.image(row['Gambar'], use_column_width=True)
            else:
                st.info("Gambar belum diunggah.")


# ==========================================
# MODUL 4: ADMIN BMN (BARANG MASUK / KELUAR)
# ==========================================
elif menu == "📦 Admin BMN (Barang Masuk/Keluar)":
    st.title("📦 Pencatatan Transaksi BMN (Barang Milik Negara)")
    
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.subheader("📥 Pencatatan BMN Masuk")
        with st.form("form_bmn_masuk"):
            id_bmn = st.text_input("ID / Kode BMN")
            nama_bmn = st.text_input("Nama Barang BMN")
            jml_masuk = st.number_input("Jumlah Unit", min_value=1, step=1)
            sumber = st.text_input("Sumber / Asal Pengadaan BMN")
            
            if st.form_submit_button("Catat BMN Masuk"):
                timestamp_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_masuk = pd.DataFrame([{
                    "Timestamp": timestamp_sekarang,
                    "Jenis Transaksi": "MASUK",
                    "ID BMN": id_bmn,
                    "Nama BMN": nama_bmn,
                    "Jumlah": jml_masuk,
                    "Tujuan / Sumber": sumber
                }])
                st.session_state.bmn_logs = pd.concat([st.session_state.bmn_logs, log_masuk], ignore_index=True)
                st.success("Transaksi BMN Masuk berhasil dicatat!")
                st.rerun()

    with col_out:
        st.subheader("📤 Pencatatan BMN Keluar")
        with st.form("form_bmn_keluar"):
            id_bmn_out = st.text_input("ID / Kode BMN ")
            nama_bmn_out = st.text_input("Nama Barang BMN ")
            jml_keluar = st.number_input("Jumlah Unit ", min_value=1, step=1)
            tujuan = st.text_input("Tujuan Penyaluran / Unit Kerja / Stasiun")
            
            if st.form_submit_button("Catat BMN Keluar"):
                timestamp_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_keluar = pd.DataFrame([{
                    "Timestamp": timestamp_sekarang,
                    "Jenis Transaksi": "KELUAR",
                    "ID BMN": id_bmn_out,
                    "Nama BMN": nama_bmn_out,
                    "Jumlah": jml_keluar,
                    "Tujuan / Sumber": tujuan
                }])
                st.session_state.bmn_logs = pd.concat([st.session_state.bmn_logs, log_keluar], ignore_index=True)
                st.warning("Transaksi BMN Keluar berhasil dicatat!")
                st.rerun()

    st.markdown("---")
    
    st.subheader("📋 Tabel Riwayat Transaksi BMN (Barang Masuk & Keluar)")
    if not st.session_state.bmn_logs.empty:
        st.dataframe(
            st.session_state.bmn_logs.sort_values(by="Timestamp", ascending=False),
            use_container_width=True
        )
    else:
        st.info("Belum ada riwayat transaksi BMN.")