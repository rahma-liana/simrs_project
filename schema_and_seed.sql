-- =====================================================================
-- DATABASE SISTEM INFORMASI RUMAH SAKIT (SIMRS)
-- Nama Database: db_sistem_rumah_sakit
-- =====================================================================

CREATE DATABASE IF NOT EXISTS db_sistem_rumah_sakit
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_sistem_rumah_sakit;

-- Nonaktifkan pengecekan foreign key selama drop/create tabel
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tabel jika sudah ada sebelumnya
DROP TABLE IF EXISTS log_aktivitas;
DROP TABLE IF EXISTS pembayaran;
DROP TABLE IF EXISTS tagihan;
DROP TABLE IF EXISTS detail_resep;
DROP TABLE IF EXISTS resep;
DROP TABLE IF EXISTS obat_mutasi;
DROP TABLE IF EXISTS obat;
DROP TABLE IF EXISTS rekam_medis_tindakan;
DROP TABLE IF EXISTS rekam_medis;
DROP TABLE IF EXISTS tindakan_medis;
DROP TABLE IF EXISTS pendaftaran;
DROP TABLE IF EXISTS jadwal_dokter;
DROP TABLE IF EXISTS dokter;
DROP TABLE IF EXISTS poli;
DROP TABLE IF EXISTS pasien;
DROP TABLE IF EXISTS pengaturan_rs;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. TABEL users (Akun Admin)
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    no_telepon VARCHAR(20) NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'Admin',
    foto_profil VARCHAR(255) NULL,
    terakhir_login DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2. TABEL pengaturan_rs (Profil Rumah Sakit)
-- ---------------------------------------------------------------------
CREATE TABLE pengaturan_rs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_rs VARCHAR(150) NOT NULL,
    kode_rs VARCHAR(20) NULL,
    alamat TEXT NOT NULL,
    kota VARCHAR(50) NOT NULL,
    provinsi VARCHAR(50) NOT NULL,
    kode_pos VARCHAR(10) NULL,
    no_telepon VARCHAR(30) NOT NULL,
    email VARCHAR(100) NOT NULL,
    website VARCHAR(100) NULL,
    motto VARCHAR(255) NULL,
    biaya_pendaftaran_default DECIMAL(12,2) DEFAULT 20000.00,
    catatan_struk TEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3. TABEL poli (Poliklinik)
-- ---------------------------------------------------------------------
CREATE TABLE poli (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kode_poli VARCHAR(20) NOT NULL UNIQUE,
    nama_poli VARCHAR(100) NOT NULL,
    lokasi VARCHAR(100) NOT NULL,
    keterangan TEXT NULL,
    status_aktif ENUM('Aktif', 'Nonaktif') DEFAULT 'Aktif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 4. TABEL dokter (Data Dokter)
-- ---------------------------------------------------------------------
CREATE TABLE dokter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nip_sip VARCHAR(50) NOT NULL UNIQUE,
    nama_dokter VARCHAR(120) NOT NULL,
    poli_id INT NOT NULL,
    spesialisasi VARCHAR(100) NOT NULL,
    jenis_kelamin ENUM('L', 'P') NOT NULL,
    no_telepon VARCHAR(20) NOT NULL,
    email VARCHAR(100) NULL,
    biaya_konsultasi DECIMAL(12,2) NOT NULL DEFAULT 50000.00,
    status_aktif ENUM('Aktif', 'Nonaktif') DEFAULT 'Aktif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poli_id) REFERENCES poli(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 5. TABEL jadwal_dokter (Jadwal Praktik Dokter)
-- ---------------------------------------------------------------------
CREATE TABLE jadwal_dokter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dokter_id INT NOT NULL,
    hari ENUM('Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu') NOT NULL,
    jam_mulai TIME NOT NULL,
    jam_selesai TIME NOT NULL,
    kuota_pasien INT NOT NULL DEFAULT 30,
    status ENUM('Aktif', 'Libur') DEFAULT 'Aktif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 6. TABEL pasien (Data Pasien)
-- ---------------------------------------------------------------------
CREATE TABLE pasien (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_rm VARCHAR(30) NOT NULL UNIQUE,
    nik VARCHAR(20) NOT NULL UNIQUE,
    nama_lengkap VARCHAR(120) NOT NULL,
    jenis_kelamin ENUM('L', 'P') NOT NULL,
    tempat_lahir VARCHAR(60) NOT NULL,
    tanggal_lahir DATE NOT NULL,
    alamat TEXT NOT NULL,
    no_telepon VARCHAR(25) NOT NULL,
    golongan_darah ENUM('A', 'B', 'AB', 'O', '-') DEFAULT '-',
    pekerjaan VARCHAR(60) NULL,
    riwayat_alergi TEXT NULL,
    kontak_darurat_nama VARCHAR(100) NULL,
    kontak_darurat_telp VARCHAR(25) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (nama_lengkap),
    INDEX (no_rm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 7. TABEL pendaftaran (Kunjungan & Antrean Pasien)
-- ---------------------------------------------------------------------
CREATE TABLE pendaftaran (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran VARCHAR(40) NOT NULL UNIQUE,
    no_antrean VARCHAR(20) NOT NULL,
    pasien_id INT NOT NULL,
    dokter_id INT NOT NULL,
    poli_id INT NOT NULL,
    tanggal_kunjungan DATE NOT NULL,
    waktu_daftar TIME NOT NULL,
    keluhan_awal TEXT NULL,
    status_antrean ENUM('Menunggu', 'Dipanggil', 'Sedang Diperiksa', 'Selesai', 'Dibatalkan') DEFAULT 'Menunggu',
    catatan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (poli_id) REFERENCES poli(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX (tanggal_kunjungan),
    INDEX (status_antrean)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 8. TABEL tindakan_medis (Katalog Prosedur Medis)
-- ---------------------------------------------------------------------
CREATE TABLE tindakan_medis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kode_tindakan VARCHAR(20) NOT NULL UNIQUE,
    nama_tindakan VARCHAR(120) NOT NULL,
    kategori VARCHAR(60) NOT NULL DEFAULT 'Umum',
    tarif DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    keterangan TEXT NULL,
    status_aktif ENUM('Aktif', 'Nonaktif') DEFAULT 'Aktif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 9. TABEL rekam_medis (Catatan Pemeriksaan Pasien)
-- ---------------------------------------------------------------------
CREATE TABLE rekam_medis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_rekam_medis VARCHAR(40) NOT NULL UNIQUE,
    pendaftaran_id INT NOT NULL UNIQUE,
    pasien_id INT NOT NULL,
    dokter_id INT NOT NULL,
    tanggal_periksa DATE NOT NULL,
    waktu_periksa TIME NOT NULL,
    tekanan_darah VARCHAR(20) NULL,
    suhu_tubuh DECIMAL(4,1) NULL,
    berat_badan DECIMAL(5,1) NULL,
    tinggi_badan DECIMAL(5,1) NULL,
    denyut_nadi INT NULL,
    keluhan_utama TEXT NOT NULL,
    pemeriksaan_fisik TEXT NULL,
    diagnosis TEXT NOT NULL,
    kode_icd10 VARCHAR(20) NULL,
    tindakan_diberikan TEXT NULL,
    catatan_dokter TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pendaftaran_id) REFERENCES pendaftaran(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX (tanggal_periksa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 10. TABEL rekam_medis_tindakan (Rincian Tindakan per Pemeriksaan)
-- ---------------------------------------------------------------------
CREATE TABLE rekam_medis_tindakan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rekam_medis_id INT NOT NULL,
    tindakan_id INT NOT NULL,
    biaya DECIMAL(12,2) NOT NULL,
    catatan VARCHAR(255) NULL,
    FOREIGN KEY (rekam_medis_id) REFERENCES rekam_medis(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (tindakan_id) REFERENCES tindakan_medis(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 11. TABEL obat (Master Data Obat & Persediaan)
-- ---------------------------------------------------------------------
CREATE TABLE obat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kode_obat VARCHAR(30) NOT NULL UNIQUE,
    nama_obat VARCHAR(120) NOT NULL,
    kategori VARCHAR(60) NOT NULL,
    satuan VARCHAR(30) NOT NULL,
    harga_beli DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    harga_jual DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    stok_saat_ini INT NOT NULL DEFAULT 0,
    stok_minimum INT NOT NULL DEFAULT 10,
    tanggal_kadaluwarsa DATE NOT NULL,
    keterangan TEXT NULL,
    status_aktif ENUM('Aktif', 'Nonaktif') DEFAULT 'Aktif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (nama_obat),
    INDEX (kategori)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 12. TABEL obat_mutasi (Pencatatan Obat Masuk & Keluar)
-- ---------------------------------------------------------------------
CREATE TABLE obat_mutasi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    obat_id INT NOT NULL,
    jenis_mutasi ENUM('Masuk', 'Keluar') NOT NULL,
    jumlah INT NOT NULL,
    stok_sebelum INT NOT NULL,
    stok_sesudah INT NOT NULL,
    tanggal DATE NOT NULL,
    no_referensi VARCHAR(50) NULL,
    keterangan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (obat_id) REFERENCES obat(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX (tanggal),
    INDEX (jenis_mutasi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 13. TABEL resep (Data Resep Dokter)
-- ---------------------------------------------------------------------
CREATE TABLE resep (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_resep VARCHAR(40) NOT NULL UNIQUE,
    rekam_medis_id INT NOT NULL UNIQUE,
    pasien_id INT NOT NULL,
    dokter_id INT NOT NULL,
    tanggal_resep DATE NOT NULL,
    status_resep ENUM('Menunggu', 'Diproses', 'Selesai', 'Dibatalkan') DEFAULT 'Menunggu',
    total_harga_obat DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    catatan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rekam_medis_id) REFERENCES rekam_medis(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 14. TABEL detail_resep (Rincian Obat dalam Resep)
-- ---------------------------------------------------------------------
CREATE TABLE detail_resep (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resep_id INT NOT NULL,
    obat_id INT NOT NULL,
    jumlah INT NOT NULL,
    harga_satuan DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    aturan_pakai VARCHAR(150) NOT NULL,
    FOREIGN KEY (resep_id) REFERENCES resep(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (obat_id) REFERENCES obat(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 15. TABEL tagihan (Rincian Tagihan Pasien)
-- ---------------------------------------------------------------------
CREATE TABLE tagihan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_tagihan VARCHAR(40) NOT NULL UNIQUE,
    pendaftaran_id INT NOT NULL UNIQUE,
    pasien_id INT NOT NULL,
    tanggal_tagihan DATE NOT NULL,
    biaya_pendaftaran DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    biaya_konsultasi DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    biaya_tindakan DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    biaya_obat DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_tagihan DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status_pembayaran ENUM('Belum Dibayar', 'Sebagian', 'Lunas') DEFAULT 'Belum Dibayar',
    catatan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pendaftaran_id) REFERENCES pendaftaran(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX (status_pembayaran),
    INDEX (tanggal_tagihan)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 16. TABEL pembayaran (Catatan Pembayaran Tagihan)
-- ---------------------------------------------------------------------
CREATE TABLE pembayaran (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_pembayaran VARCHAR(40) NOT NULL UNIQUE,
    tagihan_id INT NOT NULL,
    tanggal_bayar DATETIME NOT NULL,
    jumlah_bayar DECIMAL(12,2) NOT NULL,
    metode_pembayaran ENUM('Tunai', 'Transfer Bank', 'QRIS', 'Kartu Debit/Kredit') NOT NULL DEFAULT 'Tunai',
    no_referensi VARCHAR(60) NULL,
    keterangan TEXT NULL,
    kasir_nama VARCHAR(100) NOT NULL DEFAULT 'Admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tagihan_id) REFERENCES tagihan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 17. TABEL log_aktivitas (Audit Trail Aktivitas Admin)
-- ---------------------------------------------------------------------
CREATE TABLE log_aktivitas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(50) NOT NULL,
    aktivitas VARCHAR(100) NOT NULL,
    modul VARCHAR(50) NOT NULL,
    detail TEXT NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX (modul),
    INDEX (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =====================================================================
-- DATA SIMULASI (SEEDING DATA LENGKAP & REALISTIS)
-- =====================================================================

-- 1. Inisialisasi Akun Admin (Password default: admin123)
INSERT INTO users (username, email, password_hash, nama_lengkap, no_telepon, role)
VALUES (
    'admin',
    'admin@rsmedika.co.id',
    'scrypt:32768:8:1$R4EsIPeu59VWgHfM$d46d673db70de1297420dfe287245de1b90378c7b471bc5633098065c308269a350c33e2fc8fbe6cfad195dc7f495a179be4116831bbb1aaa3d96f46cec59c26',
    'Administrator Utama',
    '081234567890',
    'Admin'
);

-- 2. Inisialisasi Profil Rumah Sakit
INSERT INTO pengaturan_rs (nama_rs, kode_rs, alamat, kota, provinsi, kode_pos, no_telepon, email, website, motto, biaya_pendaftaran_default, catatan_struk)
VALUES (
    'RS Medika Sehat Sentosa',
    'RS-MEDIKA-01',
    'Jl. Kesehatan Raya No. 45, Menteng',
    'Jakarta Pusat',
    'DKI Jakarta',
    '10310',
    '(021) 3901234 / 0812-9876-5432',
    'kontak@rsmedikasehat.co.id',
    'www.rsmedikasehat.co.id',
    'Melayani dengan Sepenuh Hati, Mengutamakan Keselamatan dan Kesembuhan Anda',
    25000.00,
    'Terima kasih atas kepercayaan Anda memilih RS Medika Sehat Sentosa. Semoga lekas sembuh! Harap simpan bukti pembayaran ini untuk keperluan verifikasi.'
);

-- 3. Inisialisasi Poliklinik
INSERT INTO poli (kode_poli, nama_poli, lokasi, keterangan) VALUES
('POL-UMUM', 'Poli Umum', 'Gedung A, Lantai 1', 'Pelayanan pemeriksaan kesehatan umum dan konsultasi primer'),
('POL-GIGI', 'Poli Gigi & Mulut', 'Gedung A, Lantai 2', 'Pelayanan kesehatan gigi, penambalan, pencabutan, dan scaling'),
('POL-ANAK', 'Poli Anak & Tumbuh Kembang', 'Gedung B, Lantai 1', 'Pelayanan kesehatan anak, imunisasi, dan pemantauan nutrisi'),
('POL-DALAM', 'Poli Penyakit Dalam', 'Gedung B, Lantai 2', 'Pelayanan spesialis organ dalam, diabetes, hipertensi, dan geriatri'),
('POL-MATA', 'Poli Mata', 'Gedung A, Lantai 2', 'Pemeriksaan penglihatan, refraksi kacamata, dan kesehatan mata'),
('POL-KANDUNGAN', 'Poli Kebidanan & Kandungan', 'Gedung B, Lantai 3', 'Pelayanan ibu hamil, USG kandungan, dan program KB');

-- 4. Inisialisasi Dokter
INSERT INTO dokter (nip_sip, nama_dokter, poli_id, spesialisasi, jenis_kelamin, no_telepon, email, biaya_konsultasi) VALUES
('SIP.01/DU/2021', 'dr. Andi Pratama, Sp.PD', 4, 'Spesialis Penyakit Dalam', 'L', '081311112222', 'dr.andi@rsmedika.co.id', 85000.00),
('SIP.02/DU/2020', 'dr. Siti Rahmawati, Sp.A', 3, 'Spesialis Anak', 'P', '081322223333', 'dr.siti@rsmedika.co.id', 75000.00),
('SIP.03/DU/2022', 'drg. Hendra Wijaya', 2, 'Dokter Gigi Umum', 'L', '081333334444', 'drg.hendra@rsmedika.co.id', 65000.00),
('SIP.04/DU/2019', 'dr. Budi Santoso', 1, 'Dokter Umum', 'L', '081344445555', 'dr.budi@rsmedika.co.id', 50000.00),
('SIP.05/DU/2023', 'dr. Maya Kartika, Sp.M', 5, 'Spesialis Mata', 'P', '081355556666', 'dr.maya@rsmedika.co.id', 75000.00),
('SIP.06/DU/2018', 'dr. Ratna Dewi, Sp.OG', 6, 'Spesialis Obstetri & Ginekologi', 'P', '081366667777', 'dr.ratna@rsmedika.co.id', 90000.00);

-- 5. Inisialisasi Jadwal Dokter
INSERT INTO jadwal_dokter (dokter_id, hari, jam_mulai, jam_selesai, kuota_pasien) VALUES
(1, 'Senin', '08:00:00', '12:00:00', 25),
(1, 'Rabu', '08:00:00', '12:00:00', 25),
(1, 'Jumat', '08:00:00', '12:00:00', 25),
(2, 'Senin', '13:00:00', '17:00:00', 20),
(2, 'Selasa', '13:00:00', '17:00:00', 20),
(2, 'Kamis', '13:00:00', '17:00:00', 20),
(3, 'Senin', '09:00:00', '14:00:00', 15),
(3, 'Rabu', '09:00:00', '14:00:00', 15),
(3, 'Sabtu', '09:00:00', '13:00:00', 15),
(4, 'Senin', '08:00:00', '16:00:00', 40),
(4, 'Selasa', '08:00:00', '16:00:00', 40),
(4, 'Rabu', '08:00:00', '16:00:00', 40),
(4, 'Kamis', '08:00:00', '16:00:00', 40),
(4, 'Jumat', '08:00:00', '16:00:00', 40),
(5, 'Selasa', '08:30:00', '12:30:00', 20),
(5, 'Kamis', '08:30:00', '12:30:00', 20),
(6, 'Rabu', '13:00:00', '17:00:00', 20),
(6, 'Sabtu', '08:00:00', '12:00:00', 20);

-- 6. Inisialisasi Data Pasien
INSERT INTO pasien (no_rm, nik, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, alamat, no_telepon, golongan_darah, pekerjaan, riwayat_alergi, kontak_darurat_nama, kontak_darurat_telp) VALUES
('RM-202610-0001', '3171012305880001', 'Ahmad Fauzi', 'L', 'Jakarta', '1988-05-23', 'Jl. Salemba Tengah No. 12, Senen, Jakarta Pusat', '081801234567', 'O', 'Karyawan Swasta', 'Alergi Penisilin', 'Nurul (Istri)', '081801234568'),
('RM-202610-0002', '3171024508920002', 'Dewi Lestari', 'P', 'Bandung', '1992-08-15', 'Jl. Cempaka Putih Timur No. 8, Jakarta Pusat', '081912345678', 'A', 'Guru', 'Tidak ada', 'Bambang (Suami)', '081912345679'),
('RM-202610-0003', '3171031102950003', 'Rian Hidayat', 'L', 'Surabaya', '1995-02-11', 'Jl. Percetakan Negara IX No. 22, Jakarta Pusat', '082123456789', 'B', 'Wiraswasta', 'Alergi Debu', 'Hendra (Kakak)', '082123456780'),
('RM-202610-0004', '3171046711010004', 'Siti Nurhaliza', 'P', 'Bogor', '2001-11-27', 'Jl. Rawasari Barat Blok B No. 4, Jakarta Pusat', '085734567890', 'AB', 'Mahasiswa', 'Alergi Seafood', 'Aminah (Ibu)', '085734567891'),
('RM-202610-0005', '3171052003750005', 'Bambang Sudarsono', 'L', 'Yogyakarta', '1975-03-20', 'Jl. Kramat Raya No. 102, Jakarta Pusat', '081245678901', 'O', 'PNS', 'Tidak ada', 'Sri (Istri)', '081245678902'),
('RM-202610-0006', '3171065507150006', 'Anisa Kirana (Anak)', 'P', 'Jakarta', '2018-07-15', 'Jl. Salemba Tengah No. 12, Senen, Jakarta Pusat', '081801234567', 'O', 'Pelajar', 'Tidak ada', 'Ahmad Fauzi (Ayah)', '081801234567'),
('RM-202610-0007', '3171071209840007', 'Eko Prasetyo', 'L', 'Semarang', '1984-09-12', 'Jl. Johar Baru V No. 17, Jakarta Pusat', '087856789012', 'A', 'Arsitek', 'Alergi Sulfa', 'Dian (Istri)', '087856789013');

-- 7. Inisialisasi Master Tindakan Medis
INSERT INTO tindakan_medis (kode_tindakan, nama_tindakan, kategori, tarif, keterangan) VALUES
('TND-001', 'Pemeriksaan & Konsultasi Medis', 'Umum', 30000.00, 'Pemeriksaan tanda vital dan diagnosis dasar'),
('TND-002', 'Perawatan & Pembersihan Luka Ringan', 'Bedah Minor', 45000.00, 'Pembersihan luka lecet atau sayat dan aplikasi antiseptik'),
('TND-003', 'Jahit Luka (Hecting 1-3 Simpul)', 'Bedah Minor', 95000.00, 'Penjahitan luka terbuka termasuk anestesi lokal'),
('TND-004', 'Inhalasi Terapi Nebulizer', 'Respirasi', 65000.00, 'Pemberian obat uap untuk melegakan saluran pernapasan'),
('TND-005', 'Pemeriksaan EKG Jantung', 'Diagnostik', 80000.00, 'Rekam detak dan gelombang aktivitas listrik jantung'),
('TND-006', 'Pembersihan Karang Gigi (Scaling Penuh)', 'Gigi', 180000.00, 'Scaling kalkulus rahang atas dan bawah'),
('TND-007', 'Pencabutan Gigi Tetap', 'Gigi', 120000.00, 'Pencabutan gigi dewasa dengan anestesi lokal'),
('TND-008', 'Pemeriksaan Refraksi & Tajam Penglihatan', 'Mata', 40000.00, 'Tes kartu Snellen dan koreksi lensa optik'),
('TND-009', 'Pemeriksaan USG 2D Kandungan', 'Kebidanan', 150000.00, 'Pemeriksaan sonografi perkembangan janin');

-- 8. Inisialisasi Master Obat & Stok
INSERT INTO obat (kode_obat, nama_obat, kategori, satuan, harga_beli, harga_jual, stok_saat_ini, stok_minimum, tanggal_kadaluwarsa, keterangan) VALUES
('OBT-001', 'Paracetamol 500 mg', 'Analgesik & Antipiretik', 'Tablet', 500.00, 1000.00, 250, 50, '2028-06-30', 'Pereda nyeri dan demam ringan hingga sedang'),
('OBT-002', 'Amoxicillin 500 mg', 'Antibiotik', 'Kapsul', 1200.00, 2500.00, 120, 40, '2027-12-31', 'Antibiotik spektrum luas untuk infeksi bakteri'),
('OBT-003', 'Cetirizine 10 mg', 'Antihistamin', 'Tablet', 800.00, 1800.00, 80, 25, '2028-04-15', 'Mengatasi gejala alergi, bersin, dan gatal-gatal'),
('OBT-004', 'Omeprazole 20 mg', 'Antasida & Saluran Cerna', 'Kapsul', 1500.00, 3000.00, 6, 20, '2027-09-20', 'STOK MENIPIS - Menurunkan produksi asam lambung berlebih'),
('OBT-005', 'Metformin 500 mg', 'Antidiabetes', 'Tablet', 700.00, 1500.00, 95, 30, '2028-01-10', 'Obat lini pertama terapi diabetes melitus tipe 2'),
('OBT-006', 'Amlodipine 10 mg', 'Antihipertensi', 'Tablet', 900.00, 2000.00, 8, 25, '2027-11-25', 'STOK MENIPIS - Penurun tekanan darah tinggi'),
('OBT-007', 'OBH Sirup Obat Batuk 100 ml', 'Saluran Napas', 'Botol', 12000.00, 18000.00, 35, 10, '2027-08-30', 'Meredakan batuk berdahak dan melegakan tenggorokan'),
('OBT-008', 'Ibuprofen 400 mg', 'Analgesik & NSAID', 'Tablet', 1000.00, 2200.00, 150, 30, '2028-03-18', 'Anti inflamasi dan pereda nyeri peradangan sendi/gigi'),
('OBT-009', 'Antasida Doen Tablet Kunyah', 'Antasida & Saluran Cerna', 'Tablet', 400.00, 800.00, 5, 20, '2027-10-12', 'STOK MENIPIS - Menetralkan keasaman lambung seketika'),
('OBT-010', 'Vitamin C 500 mg', 'Vitamin & Suplemen', 'Tablet', 600.00, 1200.00, 300, 50, '2028-12-31', 'Meningkatkan daya tahan tubuh dan pemulihan'),
('OBT-011', 'Ventolin Inhaler 100 mcg', 'Respirasi & Asma', 'Pcs', 95000.00, 135000.00, 12, 5, '2028-05-20', 'Bronkodilator cepat untuk serangan sesak napas / asma'),
('OBT-012', 'Ciprofloxacin 500 mg', 'Antibiotik', 'Tablet', 2500.00, 5000.00, 45, 15, '2027-07-15', 'Antibiotik infeksi saluran kemih dan pencernaan');

-- 9. Inisialisasi Mutasi Obat Masuk & Keluar
INSERT INTO obat_mutasi (obat_id, jenis_mutasi, jumlah, stok_sebelum, stok_sesudah, tanggal, no_referensi, keterangan) VALUES
(1, 'Masuk', 300, 0, 300, CURDATE() - INTERVAL 10 DAY, 'PO-202610-001', 'Penerimaan stok awal dari Distributor Kimia Farma'),
(2, 'Masuk', 150, 0, 150, CURDATE() - INTERVAL 10 DAY, 'PO-202610-001', 'Penerimaan stok awal dari Distributor Kimia Farma'),
(4, 'Keluar', 14, 20, 6, CURDATE() - INTERVAL 1 DAY, 'MUT-OUT-001', 'Penyerahan resep pasien rawat jalan'),
(6, 'Keluar', 17, 25, 8, CURDATE() - INTERVAL 1 DAY, 'MUT-OUT-002', 'Penyerahan resep poli penyakit dalam');

-- 10. Inisialisasi Kunjungan & Pendaftaran (Hari Ini & Kemarin)
INSERT INTO pendaftaran (no_pendaftaran, no_antrean, pasien_id, dokter_id, poli_id, tanggal_kunjungan, waktu_daftar, keluhan_awal, status_antrean, catatan) VALUES
('REG-202610-0001', 'U-001', 1, 4, 1, CURDATE() - INTERVAL 1 DAY, '08:15:00', 'Demam tinggi 3 hari, sakit kepala dan menggigil', 'Selesai', 'Selesai diperiksa dan obat telah diambil'),
('REG-202610-0002', 'G-001', 2, 3, 2, CURDATE() - INTERVAL 1 DAY, '09:30:00', 'Gigi geraham belakang ngilu dan berdarah saat sikat', 'Selesai', 'Tindakan scaling karang gigi'),
('REG-202610-0003', 'D-001', 5, 1, 4, CURDATE(), '08:00:00', 'Kontrol rutin tekanan darah dan nyeri ulu hati', 'Sedang Diperiksa', 'Pasien sedang di ruang periksa dr. Andi'),
('REG-202610-0004', 'A-001', 6, 2, 3, CURDATE(), '08:30:00', 'Batuk berdahak dan pilek sejak kemarin', 'Dipanggil', 'Menuju ruang dokter spesialis anak'),
('REG-202610-0005', 'U-002', 3, 4, 1, CURDATE(), '09:00:00', 'Luka robek pada telapak tangan kiri kena kaca', 'Menunggu', 'Pasien menunggu di ruang tunggu Poli Umum'),
('REG-202610-0006', 'M-001', 4, 5, 5, CURDATE(), '09:45:00', 'Mata kanan merah dan berair gatal', 'Menunggu', 'Antrean urutan ke-1 Poli Mata');

-- 11. Inisialisasi Rekam Medis untuk Kunjungan yang Sudah Selesai
INSERT INTO rekam_medis (no_rekam_medis, pendaftaran_id, pasien_id, dokter_id, tanggal_periksa, waktu_periksa, tekanan_darah, suhu_tubuh, berat_badan, tinggi_badan, denyut_nadi, keluhan_utama, pemeriksaan_fisik, diagnosis, kode_icd10, tindakan_diberikan, catatan_dokter) VALUES
(
    'RMED-202610-0001',
    1,
    1,
    4,
    CURDATE() - INTERVAL 1 DAY,
    '08:40:00',
    '120/80',
    38.4,
    68.5,
    172.0,
    88,
    'Demam tinggi sejak 3 hari lalu, meriang disertai pusing dan lemas.',
    'Faring hiperemis ringan (+), tonsil T1-T1 tenang, sklera ikterik (-), ronki (-).',
    'Infeksi Saluran Pernapasan Akut (ISPA) dengan Febris Akut',
    'J06.9',
    'Pemeriksaan fisik umum dan edukasi hidrasi aktif',
    'Istirahat total 3 hari, minum air putih hangat minimal 2 liter per hari. Jika demam > 39C segera kembali.'
),
(
    'RMED-202610-0002',
    2,
    2,
    3,
    CURDATE() - INTERVAL 1 DAY,
    '10:00:00',
    '115/75',
    36.6,
    54.0,
    158.0,
    76,
    'Gigi geraham rahang bawah sering ngilu dan gusi berdarah.',
    'Gingivitis marginalis (+), akumulasi kalkulus subgingiva regio anterior dan posterior mandibula.',
    'Gingivitis Kronis ec Kalkulus Dental',
    'K05.1',
    'Pembersihan karang gigi (Scaling) rahang atas dan bawah',
    'Edukasi cara menyikat gigi memutar, kurangi makanan manis dan kontrol berkala 6 bulan sekali.'
);

-- 12. Inisialisasi Tindakan pada Rekam Medis
INSERT INTO rekam_medis_tindakan (rekam_medis_id, tindakan_id, biaya, catatan) VALUES
(1, 1, 30000.00, 'Pemeriksaan tanda vital dan diagnosis umum'),
(2, 6, 180000.00, 'Pembersihan karang gigi penuh rahang atas dan bawah');

-- 13. Inisialisasi Resep Dokter
INSERT INTO resep (no_resep, rekam_medis_id, pasien_id, dokter_id, tanggal_resep, status_resep, total_harga_obat, catatan) VALUES
('RSP-202610-0001', 1, 1, 4, CURDATE() - INTERVAL 1 DAY, 'Selesai', 47000.00, 'Diminum sesudah makan secara teratur'),
('RSP-202610-0002', 2, 2, 3, CURDATE() - INTERVAL 1 DAY, 'Selesai', 32000.00, 'Gunakan obat kumur dan pereda ngilu');

-- 14. Inisialisasi Detail Resep Obat
INSERT INTO detail_resep (resep_id, obat_id, jumlah, harga_satuan, subtotal, aturan_pakai) VALUES
(1, 1, 10, 1000.00, 10000.00, '3 x 1 tablet sehari bila demam/nyeri'),
(1, 2, 10, 2500.00, 25000.00, '3 x 1 kapsul sehari habiskan (antibiotik)'),
(1, 10, 10, 1200.00, 12000.00, '1 x 1 tablet sehari pagi hari'),
(2, 8, 10, 2200.00, 22000.00, '3 x 1 tablet sehari bila terasa nyeri'),
(2, 1, 10, 1000.00, 10000.00, '3 x 1 tablet sehari');

-- 15. Inisialisasi Tagihan Pasien
INSERT INTO tagihan (no_tagihan, pendaftaran_id, pasien_id, tanggal_tagihan, biaya_pendaftaran, biaya_konsultasi, biaya_tindakan, biaya_obat, total_tagihan, status_pembayaran, catatan) VALUES
('INV-202610-0001', 1, 1, CURDATE() - INTERVAL 1 DAY, 25000.00, 50000.00, 30000.00, 47000.00, 152000.00, 'Lunas', 'Pembayaran via QRIS Berhasil'),
('INV-202610-0002', 2, 2, CURDATE() - INTERVAL 1 DAY, 25000.00, 65000.00, 180000.00, 32000.00, 302000.00, 'Lunas', 'Pembayaran Tunai di Kasir 1');

-- 16. Inisialisasi Pembayaran Kasir
INSERT INTO pembayaran (no_pembayaran, tagihan_id, tanggal_bayar, jumlah_bayar, metode_pembayaran, no_referensi, keterangan, kasir_nama) VALUES
('PAY-202610-0001', 1, NOW() - INTERVAL 1 DAY, 152000.00, 'QRIS', 'QRIS-83921094', 'Lunas diterima melalui QRIS Mandiri', 'Admin'),
('PAY-202610-0002', 2, NOW() - INTERVAL 1 DAY, 302000.00, 'Tunai', 'CASH-99120', 'Uang pas diterima kasir', 'Admin');

-- 17. Inisialisasi Log Aktivitas Admin
INSERT INTO log_aktivitas (user_id, username, aktivitas, modul, detail, ip_address) VALUES
(1, 'admin', 'Inisialisasi Sistem', 'Sistem', 'Instalasi dan migrasi database awal SIMRS berhasil', '127.0.0.1'),
(1, 'admin', 'Pendaftaran Pasien', 'Pendaftaran', 'Mendaftarkan kunjungan pasien Ahmad Fauzi ke Poli Umum', '127.0.0.1'),
(1, 'admin', 'Input Rekam Medis', 'Rekam Medis', 'Pencatatan pemeriksaan fisik dan diagnosis pasien Ahmad Fauzi', '127.0.0.1'),
(1, 'admin', 'Penyerahan Obat Resep', 'Farmasi', 'Resep RSP-202610-0001 diserahkan kepada pasien Ahmad Fauzi', '127.0.0.1'),
(1, 'admin', 'Penerimaan Pembayaran', 'Kasir', 'Menerima pembayaran lunas INV-202610-0001 sejumlah Rp 152.000', '127.0.0.1');
