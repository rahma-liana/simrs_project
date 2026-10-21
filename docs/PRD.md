# PRD — Sistem Informasi Manajemen Rumah Sakit (SIMRS)

## 1. Ringkasan Produk
SIMRS adalah aplikasi web internal untuk membantu administrasi rumah sakit mengelola data master, kunjungan, antrean, catatan pemeriksaan, farmasi, tagihan, pembayaran, dan laporan melalui satu database terintegrasi.

## 2. Tujuan
- Memusatkan data administrasi rumah sakit.
- Mengurangi pencatatan berulang dan kesalahan manual.
- Mempercepat pencarian data, pendaftaran, dan pembuatan laporan.
- Menyediakan jejak aktivitas untuk perubahan data penting.
- Menjaga kerahasiaan data pasien dan konsistensi transaksi.

## 3. Pengguna dan Hak Akses
Hanya ada satu role aplikasi: **Admin**. Seluruh halaman internal membutuhkan sesi login Admin. Data pasien tidak memiliki akun login. Dalam implementasi nyata, kewenangan klinis tetap harus diverifikasi secara terpisah dan tidak diasumsikan dimiliki oleh Admin.

## 4. Ruang Lingkup Modul
1. Login/logout dan sesi aman.
2. Dashboard statistik berbasis query database.
3. Data pasien.
4. Data dokter dan poli.
5. Jadwal praktik.
6. Pendaftaran dan antrean.
7. Rekam medis dan audit perubahan.
8. Obat, resep, stok, dan mutasi persediaan.
9. Tagihan, pembayaran, serta bukti transaksi.
10. Laporan dan ekspor.
11. Profil rumah sakit, akun Admin, log aktivitas, dan backup.

## 5. Alur Sistem
1. Admin membuka aplikasi dan login.
2. Backend memverifikasi username/email dan hash password.
3. Sistem membuat sesi dan mengarahkan Admin ke dashboard.
4. Dashboard membaca ringkasan dari database.
5. Admin mengelola data master pasien, dokter, poli, dan jadwal.
6. Admin mendaftarkan pasien; sistem memvalidasi jadwal dan membuat antrean unik per poli/tanggal.
7. Pemeriksaan ditautkan ke pendaftaran, pasien, dan dokter. Perubahan catatan klinis harus memiliki audit trail.
8. Resep yang telah disahkan tenaga medis berwenang dapat diproses; pengeluaran obat harus mengurangi stok dalam transaksi database yang atomik.
9. Tagihan dihitung dari komponen biaya; pembayaran tidak boleh melebihi sisa tagihan dan status diperbarui secara konsisten.
10. Admin memfilter, mencetak, atau mengekspor laporan.
11. Aktivitas penting dicatat; Admin logout untuk mengakhiri sesi.

## 6. Kebutuhan Nonfungsional
- Antarmuka Bahasa Indonesia, responsif, dan konsisten.
- Password disimpan menggunakan hashing modern.
- Query database menggunakan parameter, bukan string concatenation dari input pengguna.
- Foreign key menjaga integritas relasi.
- Data klinis dan finansial tidak dihapus sembarangan; gunakan arsip atau pembatalan yang tercatat.
- Backup dan restore perlu prosedur teruji, akses terbatas, dan perlindungan data.
- Semua tanggal/jam dan nilai uang harus konsisten.

## 7. Kriteria Penerimaan
- Login/logout berfungsi; halaman internal tidak dapat dibuka tanpa sesi.
- Dashboard menghitung data dari database.
- CRUD data master tervalidasi dan perubahan penting masuk log.
- Nomor antrean unik sesuai poli dan tanggal.
- Rekam medis terhubung dengan pasien serta kunjungan yang benar.
- Mutasi stok dan pembayaran menjaga konsistensi melalui transaksi database.
- Laporan dapat difilter dan diekspor.
- Kesalahan input ditangani dengan pesan yang aman.
- Uji keamanan, privasi, dan pemulihan backup lulus sebelum produksi.

## 8. Tahapan Implementasi
- Tahap 1: PRD, desain, struktur proyek, skema database, autentikasi, dashboard, CRUD pasien.
- Tahap 2: CRUD dokter/poli/jadwal dan pendaftaran/antrean.
- Tahap 3: rekam medis, tindakan, audit perubahan.
- Tahap 4: farmasi, resep, dan mutasi stok atomik.
- Tahap 5: tagihan, pembayaran, bukti pembayaran.
- Tahap 6: laporan PDF/Excel, pengaturan, backup/restore.
- Tahap 7: uji integrasi, uji keamanan, dan dokumentasi deployment.
