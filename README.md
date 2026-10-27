# Sistem Informasi Rumah Sakit (SIMRS) Terintegrasi

Aplikasi web Sistem Informasi Rumah Sakit (SIMRS) modern, responsif, dan terintegrasi untuk membantu pengelolaan administrasi rumah sakit secara menyeluruh, mencakup data pasien, dokter, poliklinik, jadwal praktik, pendaftaran & antrean, rekam medis klinis (EMR), farmasi & persediaan obat, kasir & pembayaran, serta pelaporan rumah sakit.

---

## 🌟 Karakteristik & Fitur Utama

- **User Role Tunggal (Admin Only)**:
  Sistem dirancang dengan satu akun peran terpusat (**Admin**) yang bertanggung jawab mengelola seluruh modul operasional dan administratif melalui satu akun login terproteksi.
- **Desain UI/UX Medis Profesional**:
  Mengusung palet warna institusi kesehatan: **Biru Medis**, **Putih Bersih**, dan **Hijau Mint Segar** berbasis Bootstrap 5 dengan antarmuka 100% Bahasa Indonesia yang intuitif dan responsif (desktop, tablet, smartphone).
- **Alur Pelayanan Pasien Terhubung (End-to-End Workflow)**:
  Pasien Didaftarkan &rarr; Karcis Antrean Terbit &rarr; Pemeriksaan Tanda Vital & Rekam Medis &rarr; Resep Obat Dibuat &rarr; Obat Diserahkan (Stok Berkurang Otomatis) &rarr; Tagihan Terhitung Otomatis (Konsultasi + Tindakan + Obat) &rarr; Kasir Menerima Pembayaran & Cetak Kuitansi Resmi.
- **Keamanan Data**:
  - Enkripsi password menggunakan hashing aman `Werkzeug` (`scrypt`).
  - Proteksi sesi login (`session`) dengan `@login_required` decorator.
  - Audit Trail / Log Aktivitas otomatis di database untuk melacak seluruh tindakan admin.
  - Relasi database MySQL dengan Foreign Key constraint integritas tinggi.
  - Fitur Backup Database SQL satu-klik.

---

## 🛠️ Teknologi yang Digunakan

- **Frontend**: HTML5, CSS3 kustom, Bootstrap 5.3, Bootstrap Icons, Chart.js (grafik dashboard), JavaScript interaktif.
- **Backend**: Python 3.13 dengan framework **Flask**.
- **Database**: **MySQL** dengan nama basis data `db_sistem_rumah_sakit`.
- **Ekspor Data**: `openpyxl` untuk pembuatan file spreadsheet Excel (.xlsx) dan modul cetak format A4/PDF siap cetak browser.
- **Server Lokal**: **Laragon** (Windows) sebagai penyedia layanan MySQL server.

---

## 📁 Struktur Folder Proyek

```text
simrs_app/
│
├── app.py                     # Entry point aplikasi Flask & inisialisasi modul
├── config.py                  # Konfigurasi aplikasi & database MySQL Laragon
├── database.py                # Helper koneksi PyMySQL, DictCursor & transaksi atomik
├── helpers.py                 # Decorator login, generator no RM/antrean/tagihan, formatter rupiah/tanggal
├── schema_and_seed.sql        # Skrip DDL MySQL & data simulasi lengkap siap pakai
├── requirements.txt           # Daftar dependensi Python
├── README.md                  # Panduan lengkap instalasi dan penggunaan
│
├── routes/                    # Modular Blueprints (Backend Routes)
│   ├── auth.py                # Login, Logout Admin
│   ├── dashboard.py           # Statistik dashboard, grafik kunjungan & poli
│   ├── pasien.py              # CRUD data pasien, pencarian & riwayat medis
│   ├── dokter.py              # CRUD dokter & API dokter per poli
│   ├── poli.py                # CRUD poliklinik rawat jalan
│   ├── jadwal.py              # Jadwal praktik dokter mingguan & kuota
│   ├── pendaftaran.py         # Kunjungan pasien, nomor antrean & karcis
│   ├── rekam_medis.py         # Rekam medis, tanda vital, diagnosis ICD-10
│   ├── tindakan.py            # Katalog master tindakan klinis & tarif
│   ├── farmasi.py             # Master obat, mutasi stok, resep & potong stok
│   ├── kasir.py               # Tagihan otomatis, pembayaran, cetak struk/kuitansi
│   ├── laporan.py             # Laporan pasien, kunjungan, farmasi, keuangan & ekspor Excel
│   └── pengaturan.py          # Profil RS, akun admin, log aktivitas & backup SQL
│
├── static/
│   ├── css/
│   │   └── custom.css         # Styling tema medis, status badge, print stylesheet
│   └── js/
│       └── app.js             # Logika interaktif JS, modal konfirmasi, dropdown dinamis
│
└── templates/                 # Tampilan Antarmuka HTML (Jinja2)
    ├── base.html              # Layout utama (sidebar, header, alerts, modal)
    ├── auth/
    │   └── login.html         # Halaman login administrator
    ├── dashboard/
    │   └── index.html         # Dashboard statistik & grafik Chart.js
    ├── pasien/                # (index.html, form.html, detail.html)
    ├── dokter/                # (index.html, form.html)
    ├── poli/                  # (index.html, form.html)
    ├── jadwal/                # (index.html, form.html)
    ├── pendaftaran/           # (index.html, form.html, cetak_antrean.html)
    ├── rekam_medis/           # (index.html, form.html, detail.html)
    ├── tindakan/              # (index.html, form.html)
    ├── farmasi/               # (obat_index, obat_form, mutasi_index, mutasi_form, resep_index, resep_form, resep_detail)
    ├── kasir/                 # (index.html, form.html, struk.html)
    ├── laporan/               # (index.html, pasien, kunjungan, farmasi_stok, farmasi_mutasi, pendapatan, cetak views)
    ├── pengaturan/            # (index.html, log.html)
    └── errors/                # (404.html, 500.html)
```

---

## 🚀 Panduan Instalasi & Menjalankan Melalui Laragon

### Langkah 1: Jalankan Laragon & MySQL
1. Buka aplikasi **Laragon** di komputer Anda.
2. Klik tombol **"Start All"** pada Laragon untuk mengaktifkan layanan MySQL (port default 3306).
   *(Pastikan indikator MySQL menyala hijau/berjalan).*

### Langkah 2: Buat Database & Muat Data Simulasi
Buka terminal (PowerShell atau Command Prompt) dan jalankan perintah berikut untuk mengimpor skema database dan data simulasi awal:

```powershell
Get-Content "C:\Users\THINKPAD 11E\.gemini\antigravity\scratch\simrs_app\schema_and_seed.sql" -Raw | & "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -u root --default-character-set=utf8mb4
```

*Atau alternatif melalui phpMyAdmin Laragon:*
- Buka browser ke `http://localhost/phpmyadmin`
- Buka tab **Import**, pilih file `schema_and_seed.sql`, lalu klik **Go**.

### Langkah 3: Pasang Dependensi Python
Pastikan dependensi Python yang dibutuhkan telah terpasang:

```powershell
cd "C:\Users\THINKPAD 11E\.gemini\antigravity\scratch\simrs_app"
python -m pip install -r requirements.txt
```

### Langkah 4: Jalankan Aplikasi SIMRS
Jalankan backend server Flask dengan perintah:

```powershell
python app.py
```

Output pada terminal akan menampilkan:
```
============================================================
 SISTEM INFORMASI RUMAH SAKIT (SIMRS) TERINTEGRASI
 Akses Website: http://127.0.0.1:5000
 Login Admin: username=admin / password=admin123
============================================================
```

### Langkah 5: Buka Aplikasi di Browser
Buka peramban (Chrome, Edge, atau Firefox) dan kunjungi alamat:
👉 **`http://127.0.0.1:5000`**

---

## 🔐 Kredensial Login Administrator

| Parameter | Kredensial Default |
|-----------|--------------------|
| **Username** | `admin` *(atau email: `admin@rsmedika.co.id`)* |
| **Password** | `admin123` |
| **Role** | `Admin` (Akses Penuh Seluruh Modul) |

---

## 📋 Alur Pengujian Fitur Utama (Testing Guide)

1. **Login & Dashboard**:
   - Masukkan username `admin` dan password `admin123`.
   - Periksa kartu statistik pada dashboard (jumlah pasien, kunjungan hari ini, antrean aktif, pendapatan, dan obat menipis yang diambil langsung dari database MySQL).
   - Amati grafik garis tren kunjungan 7 hari terakhir dan diagram donat distribusi poli.

2. **Manajemen Pasien**:
   - Buka menu **Data Pasien**.
   - Klik **Tambah Pasien Baru**, amati No. RM unik (`RM-YYYYMM-XXXX`) yang otomatis dihasilkan.
   - Isi biodata pasien, NIK, golongan darah, dan riwayat alergi, lalu klik Simpan.
   - Uji fitur pencarian pasien instan berdasarkan nama atau nomor RM.

3. **Poli, Dokter & Jadwal**:
   - Buka menu **Data Dokter**, amati daftar dokter spesialis beserta tarif jasa konsultasi.
   - Buka menu **Jadwal Dokter** untuk melihat jadwal praktik mingguan dan kuota harian.

4. **Pendaftaran Kunjungan & Antrean**:
   - Buka menu **Pendaftaran dan Antrean** &rarr; **Daftarkan Kunjungan Baru**.
   - Pilih pasien dan poliklinik tujuan. Perhatikan dropdown dokter otomatis menyesuaikan dengan poli yang dipilih.
   - Klik Daftarkan. Sistem otomatis menghasilkan nomor antrean unik (misal: `U-003`, `G-002`) dan menampilkan **Karcis Antrean** siap cetak.
   - Anda dapat memperbarui status antrean secara langsung: *Menunggu* &rarr; *Dipanggil* &rarr; *Sedang Diperiksa* &rarr; *Selesai*.

5. **Pemeriksaan Rekam Medis (EMR)**:
   - Dari antrean pasien, klik tombol **Periksa**.
   - Masukkan tanda vital (Tekanan Darah, Suhu Badan, Berat Badan, Nadi).
   - Tuliskan keluhan utama dan hasil pemeriksaan fisik.
   - Tentukan diagnosis dokter dan kode ICD-10.
   - Centang tindakan medis yang dilakukan (misal: *Pemeriksaan Umum*, *Pembersihan Karang Gigi*, atau *Jahit Luka*). Biaya tindakan akan otomatis terintegrasi ke tagihan kasir!
   - Klik **Simpan & Buat Resep Obat**.

6. **Farmasi, Resep & Pengurangan Stok Otomatis**:
   - Tambahkan item obat yang diresepkan beserta dosis aturan pakai.
   - Klik Simpan Resep.
   - Buka rincian resep, lalu klik tombol **"Serahkan Obat & Potong Stok"**.
   - Sistem akan memvalidasi kecukupan stok dan memotong stok obat di database secara permanen serta mencatat riwayat mutasi keluar.

7. **Kasir, Pembayaran & Bukti Struk**:
   - Buka menu **Kasir & Pembayaran**.
   - Pilih tagihan pasien bersangkutan. Perhatikan komponen biaya terakumulasi otomatis: *Biaya Registrasi + Konsultasi Dokter + Tindakan Medis + Obat Farmasi*.
   - Pilih metode pembayaran (*Tunai, QRIS, Transfer, atau Kartu*), masukkan jumlah bayar, lalu klik Simpan Pembayaran.
   - Sistem mencatat transaksi, memperbarui status tagihan menjadi **Lunas**, dan mencetak **Struk Kuitansi Resmi** dengan stempel cap LUNAS.

8. **Laporan Rumah Sakit & Ekspor Excel**:
   - Buka menu **Laporan RS**.
   - Pilih Laporan Pasien, Kunjungan, Stok Obat, Mutasi, atau Pendapatan.
   - Tentukan filter rentang tanggal.
   - Klik **Ekspor ke Excel** untuk mengunduh berkas `.xlsx` terformat rapi, atau klik **Cetak Laporan** untuk cetak A4/PDF.

9. **Pengaturan, Audit Log & Backup Database**:
   - Buka menu **Pengaturan** untuk memperbarui profil nama rumah sakit atau alamat.
   - Buka sub-menu **Log Aktivitas** untuk melihat rekam jejak audit tindakan admin.
   - Klik tombol **"Unduh Cadangan Database (.SQL)"** untuk mengunduh dump cadangan database sistem sewaktu-waktu.
