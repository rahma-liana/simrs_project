# SIMRS Sehat Bersama — Starter Project

Proyek awal Sistem Informasi Manajemen Rumah Sakit berbasis Flask dan MySQL. Antarmuka berbahasa Indonesia, menggunakan Bootstrap 5, serta dirancang responsif untuk desktop dan ponsel.

## Status implementasi

**Sudah tersedia pada tahap awal:** login Admin dengan password hash, proteksi halaman internal, logout, dashboard berbasis query database, CRUD dasar pasien (tambah/edit/arsip), pencarian pasien, ekspor data pasien ke Excel, log login/logout/perubahan pasien, skema relasional untuk modul utama, data simulasi poli/dokter/jadwal/obat.

**Belum selesai dan belum boleh digunakan untuk operasional rumah sakit:** CRUD dokter/poli/jadwal, pendaftaran dan antrean, rekam medis dan audit perubahan klinis, mutasi stok serta pemrosesan resep, tagihan dan pembayaran, laporan lengkap PDF/Excel, pengaturan profil, pencadangan/pemulihan, dan pengujian keamanan menyeluruh. Menu untuk modul tersebut saat ini berupa halaman penanda rancangan, bukan fitur transaksi aktif.

## Struktur folder

```text
simrs_project/
├── app/
│   ├── __init__.py             # konfigurasi Flask
│   ├── db.py                   # koneksi MySQL
│   ├── routes.py               # route dan logika aplikasi
│   ├── templates/              # template Jinja2
│   └── static/
│       ├── css/style.css       # tema biru, putih, hijau muda
│       └── js/app.js           # interaksi UI
├── sql/schema.sql              # database, tabel, relasi, data simulasi
├── docs/PRD.md                 # rancangan produk dan alur
├── .env.example                # contoh konfigurasi lokal
├── init_admin.py               # pembuatan Admin dengan password hash
├── requirements.txt
└── run.py
```

## Cara menjalankan melalui Laragon (Windows)

1. Salin folder proyek ke folder kerja, misalnya `C:\laragon\www\simrs_project`.
2. Buka Laragon lalu jalankan **Start All**. Pastikan MySQL aktif. Aplikasi Flask menggunakan port `5000` secara default, sehingga biasanya tidak bentrok dengan Apache/Nginx Laragon.
3. Buka HeidiSQL atau phpMyAdmin dari Laragon dan impor `sql/schema.sql`. File ini membuat database `db_sistem_rumah_sakit`, tabel relasional, dan data simulasi.
4. Buka terminal pada folder proyek. Buat virtual environment dan aktifkan:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. Salin `.env.example` menjadi `.env`, lalu sesuaikan `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, dan `DB_NAME` dengan konfigurasi MySQL Laragon. Ganti `FLASK_SECRET_KEY` dengan nilai acak yang panjang. Jangan publikasikan file `.env`.
6. Buat akun Admin secara interaktif. Password tidak ditulis ke source code dan disimpan sebagai hash:

   ```powershell
   py init_admin.py
   ```

   Gunakan password unik minimal 12 karakter dan simpan dengan aman.
7. Jalankan aplikasi:

   ```powershell
   py run.py
   ```

8. Buka `http://127.0.0.1:5000` di browser dan login memakai akun Admin yang dibuat pada langkah 6.

## Relasi database utama

- `poli` 1—N `dokter` dan `jadwal_dokter`.
- `dokter` 1—N `jadwal_dokter` dan `pendaftaran`.
- `pasien` 1—N `pendaftaran` dan `rekam_medis`.
- `pendaftaran` 1—0/1 `rekam_medis` dan 1—0/1 `tagihan`.
- `rekam_medis` 1—N `tindakan_medis` dan `resep`.
- `resep` 1—N `detail_resep`; `obat` 1—N `detail_resep`.
- `tagihan` 1—N `pembayaran` untuk mendukung pembayaran sebagian.
- `users` 1—N `log_aktivitas` dan mencatat Admin pembuat data terkait.

## Pengujian awal

- Impor SQL tanpa error.
- Buat akun Admin lewat `init_admin.py`.
- Login benar berhasil; password salah ditolak.
- Buka `/dashboard` tanpa login harus dialihkan ke halaman login.
- Tambahkan, cari, edit, dan arsipkan data pasien.
- Ekspor daftar pasien ke Excel.
- Pastikan angka dashboard berubah mengikuti data database.

## Catatan keamanan dan penggunaan

Ini adalah starter untuk pengembangan dan pembelajaran, bukan SIMRS siap produksi. Perlindungan token CSRF dasar sudah diterapkan pada formulir POST. Sebelum penggunaan nyata, tambahkan pembatasan percobaan login, kebijakan password dan pemulihan akun, HTTPS, manajemen secret, backup terenkripsi, audit log yang tidak mudah dimanipulasi, validasi transaksi atomik, pengujian akses, serta tinjauan kepatuhan perlindungan data kesehatan. Data simulasi di SQL bukan data pasien asli. Admin tidak otomatis berwenang mengesahkan diagnosis atau resep.
