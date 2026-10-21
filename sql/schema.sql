CREATE DATABASE IF NOT EXISTS db_sistem_rumah_sakit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_sistem_rumah_sakit;

CREATE TABLE IF NOT EXISTS users (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(60) NOT NULL UNIQUE,
 email VARCHAR(150) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 nama_lengkap VARCHAR(150) NOT NULL,
 aktif TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pasien (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 no_rekam_medis VARCHAR(30) NOT NULL UNIQUE,
 nama_lengkap VARCHAR(150) NOT NULL,
 tanggal_lahir DATE NULL,
 jenis_kelamin ENUM('Laki-laki','Perempuan') NOT NULL,
 alamat VARCHAR(500) NULL,
 no_telepon VARCHAR(25) NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
 deleted_at DATETIME NULL,
 INDEX idx_pasien_nama (nama_lengkap), INDEX idx_pasien_telepon (no_telepon)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS poli (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_poli VARCHAR(20) NOT NULL UNIQUE,
 nama_poli VARCHAR(100) NOT NULL UNIQUE,
 lokasi VARCHAR(150) NULL,
 deskripsi TEXT NULL,
 aktif TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dokter (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_dokter VARCHAR(20) NOT NULL UNIQUE,
 nama_lengkap VARCHAR(150) NOT NULL,
 spesialisasi VARCHAR(100) NOT NULL,
 no_telepon VARCHAR(25) NULL,
 email VARCHAR(150) NULL,
 poli_id BIGINT UNSIGNED NULL,
 aktif TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_dokter_poli FOREIGN KEY (poli_id) REFERENCES poli(id) ON UPDATE CASCADE ON DELETE SET NULL,
 INDEX idx_dokter_nama (nama_lengkap)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS jadwal_dokter (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 dokter_id BIGINT UNSIGNED NOT NULL,
 poli_id BIGINT UNSIGNED NOT NULL,
 hari ENUM('Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu') NOT NULL,
 jam_mulai TIME NOT NULL,
 jam_selesai TIME NOT NULL,
 kuota INT UNSIGNED NOT NULL DEFAULT 20,
 aktif TINYINT(1) NOT NULL DEFAULT 1,
 CONSTRAINT fk_jadwal_dokter FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_jadwal_poli FOREIGN KEY (poli_id) REFERENCES poli(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT chk_jam_jadwal CHECK (jam_selesai > jam_mulai),
 INDEX idx_jadwal_hari (hari, aktif)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pendaftaran (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_pendaftaran VARCHAR(35) NOT NULL UNIQUE,
 pasien_id BIGINT UNSIGNED NOT NULL,
 dokter_id BIGINT UNSIGNED NOT NULL,
 poli_id BIGINT UNSIGNED NOT NULL,
 jadwal_id BIGINT UNSIGNED NULL,
 tanggal_kunjungan DATE NOT NULL,
 nomor_antrean VARCHAR(20) NOT NULL,
 status_antrean ENUM('Menunggu','Dipanggil','Sedang Diperiksa','Selesai','Dibatalkan') NOT NULL DEFAULT 'Menunggu',
 catatan TEXT NULL,
 created_by BIGINT UNSIGNED NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_daftar_pasien FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_daftar_dokter FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_daftar_poli FOREIGN KEY (poli_id) REFERENCES poli(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_daftar_jadwal FOREIGN KEY (jadwal_id) REFERENCES jadwal_dokter(id) ON UPDATE CASCADE ON DELETE SET NULL,
 CONSTRAINT fk_daftar_admin FOREIGN KEY (created_by) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
 UNIQUE KEY uq_antrean_harian (poli_id, tanggal_kunjungan, nomor_antrean),
 INDEX idx_daftar_tanggal_status (tanggal_kunjungan, status_antrean)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rekam_medis (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 pendaftaran_id BIGINT UNSIGNED NOT NULL UNIQUE,
 pasien_id BIGINT UNSIGNED NOT NULL,
 dokter_id BIGINT UNSIGNED NOT NULL,
 tanggal_pemeriksaan DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 keluhan TEXT NULL,
 hasil_pemeriksaan TEXT NULL,
 diagnosis TEXT NULL,
 catatan TEXT NULL,
 dibuat_oleh BIGINT UNSIGNED NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_rm_daftar FOREIGN KEY (pendaftaran_id) REFERENCES pendaftaran(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_rm_pasien FOREIGN KEY (pasien_id) REFERENCES pasien(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_rm_dokter FOREIGN KEY (dokter_id) REFERENCES dokter(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_rm_admin FOREIGN KEY (dibuat_oleh) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tindakan_medis (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 rekam_medis_id BIGINT UNSIGNED NOT NULL,
 nama_tindakan VARCHAR(180) NOT NULL,
 keterangan TEXT NULL,
 biaya DECIMAL(14,2) NOT NULL DEFAULT 0,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_tindakan_rm FOREIGN KEY (rekam_medis_id) REFERENCES rekam_medis(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS obat (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_obat VARCHAR(30) NOT NULL UNIQUE,
 nama_obat VARCHAR(150) NOT NULL,
 kategori VARCHAR(100) NOT NULL,
 satuan VARCHAR(40) NOT NULL,
 harga DECIMAL(14,2) NOT NULL DEFAULT 0,
 stok INT NOT NULL DEFAULT 0,
 batas_stok_minimum INT UNSIGNED NOT NULL DEFAULT 10,
 tanggal_kedaluwarsa DATE NULL,
 aktif TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_obat_nama (nama_obat), INDEX idx_obat_stok (stok, batas_stok_minimum)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resep (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_resep VARCHAR(35) NOT NULL UNIQUE,
 rekam_medis_id BIGINT UNSIGNED NOT NULL,
 disahkan_oleh VARCHAR(150) NULL COMMENT 'Nama tenaga medis berwenang yang mengesahkan resep',
 status ENUM('Draft','Disahkan','Diproses','Selesai','Dibatalkan') NOT NULL DEFAULT 'Draft',
 catatan TEXT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_resep_rm FOREIGN KEY (rekam_medis_id) REFERENCES rekam_medis(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detail_resep (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 resep_id BIGINT UNSIGNED NOT NULL,
 obat_id BIGINT UNSIGNED NOT NULL,
 dosis VARCHAR(100) NULL,
 jumlah INT UNSIGNED NOT NULL,
 aturan_pakai VARCHAR(255) NULL,
 harga_satuan DECIMAL(14,2) NOT NULL DEFAULT 0,
 CONSTRAINT fk_detail_resep FOREIGN KEY (resep_id) REFERENCES resep(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_detail_obat FOREIGN KEY (obat_id) REFERENCES obat(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tagihan (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 kode_tagihan VARCHAR(35) NOT NULL UNIQUE,
 pendaftaran_id BIGINT UNSIGNED NOT NULL,
 biaya_pemeriksaan DECIMAL(14,2) NOT NULL DEFAULT 0,
 biaya_tindakan DECIMAL(14,2) NOT NULL DEFAULT 0,
 biaya_obat DECIMAL(14,2) NOT NULL DEFAULT 0,
 diskon DECIMAL(14,2) NOT NULL DEFAULT 0,
 total DECIMAL(14,2) NOT NULL DEFAULT 0,
 status ENUM('Belum Dibayar','Sebagian','Lunas') NOT NULL DEFAULT 'Belum Dibayar',
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_tagihan_daftar FOREIGN KEY (pendaftaran_id) REFERENCES pendaftaran(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 UNIQUE KEY uq_tagihan_pendaftaran (pendaftaran_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pembayaran (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 tagihan_id BIGINT UNSIGNED NOT NULL,
 kode_pembayaran VARCHAR(35) NOT NULL UNIQUE,
 jumlah DECIMAL(14,2) NOT NULL,
 metode ENUM('Tunai','Transfer','Kartu Debit','Kartu Kredit','QRIS','Lainnya') NOT NULL,
 referensi VARCHAR(100) NULL,
 tanggal_bayar DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 dicatat_oleh BIGINT UNSIGNED NULL,
 catatan VARCHAR(255) NULL,
 CONSTRAINT fk_bayar_tagihan FOREIGN KEY (tagihan_id) REFERENCES tagihan(id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT fk_bayar_admin FOREIGN KEY (dicatat_oleh) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
 INDEX idx_pembayaran_tanggal (tanggal_bayar)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS log_aktivitas (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NULL,
 aktivitas VARCHAR(100) NOT NULL,
 detail TEXT NULL,
 alamat_ip VARCHAR(45) NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
 INDEX idx_log_created (created_at), INDEX idx_log_aktivitas (aktivitas)
) ENGINE=InnoDB;

-- Data simulasi: tidak menggunakan identitas pasien asli.
INSERT IGNORE INTO poli (kode_poli,nama_poli,lokasi,deskripsi) VALUES
('POLI-UM','Poli Umum','Lantai 1','Layanan pemeriksaan umum'),
('POLI-GIGI','Poli Gigi','Lantai 1','Layanan kesehatan gigi'),
('POLI-ANA','Poli Anak','Lantai 2','Layanan kesehatan anak');

INSERT IGNORE INTO dokter (kode_dokter,nama_lengkap,spesialisasi,no_telepon,email,poli_id) VALUES
('DOK-001','dr. Andi Pratama','Dokter Umum','081200000101','andi.simulasi@example.test',(SELECT id FROM poli WHERE kode_poli='POLI-UM')),
('DOK-002','drg. Maya Lestari','Dokter Gigi','081200000102','maya.simulasi@example.test',(SELECT id FROM poli WHERE kode_poli='POLI-GIGI')),
('DOK-003','dr. Bima Santoso','Dokter Anak','081200000103','bima.simulasi@example.test',(SELECT id FROM poli WHERE kode_poli='POLI-ANA'));

INSERT IGNORE INTO jadwal_dokter (dokter_id,poli_id,hari,jam_mulai,jam_selesai,kuota) VALUES
((SELECT id FROM dokter WHERE kode_dokter='DOK-001'),(SELECT id FROM poli WHERE kode_poli='POLI-UM'),'Senin','08:00:00','12:00:00',25),
((SELECT id FROM dokter WHERE kode_dokter='DOK-002'),(SELECT id FROM poli WHERE kode_poli='POLI-GIGI'),'Selasa','09:00:00','13:00:00',15),
((SELECT id FROM dokter WHERE kode_dokter='DOK-003'),(SELECT id FROM poli WHERE kode_poli='POLI-ANA'),'Rabu','08:00:00','11:00:00',20);

INSERT IGNORE INTO obat (kode_obat,nama_obat,kategori,satuan,harga,stok,batas_stok_minimum,tanggal_kedaluwarsa) VALUES
('OBT-001','Paracetamol 500 mg','Analgesik','tablet',500,120,20,'2027-12-31'),
('OBT-002','Vitamin C 500 mg','Vitamin','tablet',800,8,15,'2027-10-31'),
('OBT-003','Oralit','Rehidrasi','sachet',1500,40,10,'2027-08-31');
