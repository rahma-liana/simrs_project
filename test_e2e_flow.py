import sys
from app import create_app
from database import query_db

def run_e2e():
    print("=== PENGUJIAN END-TO-END WORKFLOW SIMRS ===")
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # 1. Login Admin
    login_res = client.post('/login', data={'username_or_email': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert login_res.status_code == 200
    print("[1/6] Login Admin Berhasil")

    # 2. Tambah Pasien Baru
    post_pasien = client.post('/pasien/tambah', data={
        'no_rm': '',
        'nik': '3171999988880009',
        'nama_lengkap': 'Pasien Uji Integrasi',
        'jenis_kelamin': 'L',
        'tempat_lahir': 'Jakarta',
        'tanggal_lahir': '1990-01-01',
        'alamat': 'Jl. Percobaan No. 99',
        'no_telepon': '089912345678',
        'golongan_darah': 'O',
        'pekerjaan': 'Software Engineer',
        'riwayat_alergi': 'Tidak ada',
        'kontak_darurat_nama': 'Keluarga Pasien',
        'kontak_darurat_telp': '089912345679'
    }, follow_redirects=True)
    assert post_pasien.status_code == 200
    p = query_db("SELECT id, no_rm FROM pasien WHERE nik = '3171999988880009'", one=True)
    assert p is not None
    print(f"[2/6] Pasien Baru Terdaftar: {p['no_rm']}")

    # 3. Pendaftaran Kunjungan & Buat Antrean
    post_reg = client.post('/pendaftaran/tambah', data={
        'pasien_id': p['id'],
        'poli_id': 1, # Poli Umum
        'dokter_id': 4, # dr. Budi Santoso
        'tanggal_kunjungan': '2026-10-21',
        'keluhan_awal': 'Flu dan batuk berdahak 2 hari',
        'catatan': 'Pemeriksaan rutin'
    }, follow_redirects=True)
    assert post_reg.status_code == 200
    reg = query_db("SELECT id, no_pendaftaran, no_antrean FROM pendaftaran WHERE pasien_id = %s ORDER BY id DESC LIMIT 1", (p['id'],), one=True)
    assert reg is not None
    print(f"[3/6] Kunjungan Terdaftar! No. Antrean: {reg['no_antrean']} (Reg: {reg['no_pendaftaran']})")

    # 4. Input Pemeriksaan Rekam Medis & Tindakan
    post_rm = client.post(f"/rekam-medis/periksa/{reg['id']}", data={
        'tekanan_darah': '120/80',
        'suhu_tubuh': '37.2',
        'berat_badan': '70',
        'tinggi_badan': '175',
        'denyut_nadi': '82',
        'keluhan_utama': 'Flu, batuk, pilek 2 hari',
        'pemeriksaan_fisik': 'Faring sedikit hiperemis',
        'diagnosis': 'Common Cold / ISPA Ringan',
        'kode_icd10': 'J00',
        'tindakan_ids': ['1'], # Pemeriksaan umum (Rp 30.000)
        'catatan_dokter': 'Banyak minum air hangat dan istirahat.',
        'action': 'simpan_dan_resep'
    }, follow_redirects=True)
    assert post_rm.status_code == 200
    rm = query_db("SELECT id, no_rekam_medis FROM rekam_medis WHERE pendaftaran_id = %s", (reg['id'],), one=True)
    assert rm is not None
    print(f"[4/6] Rekam Medis Disimpan: {rm['no_rekam_medis']}")

    # 5. Buat Resep Obat & Penyerahan (Otomatis Potong Stok)
    stok_paracetamol_awal = query_db("SELECT stok_saat_ini FROM obat WHERE id = 1", one=True)['stok_saat_ini']
    post_resep = client.post(f"/farmasi/resep/buat/{rm['id']}", data={
        'obat_ids[]': ['1'], # Paracetamol
        'jumlah[]': ['10'],
        'aturan_pakai[]': ['3 x 1 tablet sehari sesudah makan'],
        'catatan': 'Habiskan'
    }, follow_redirects=True)
    assert post_resep.status_code == 200
    rsp = query_db("SELECT id, no_resep FROM resep WHERE rekam_medis_id = %s", (rm['id'],), one=True)
    assert rsp is not None
    
    # Eksekusi Serahkan Obat & Potong Stok
    post_serah = client.post(f"/farmasi/resep/{rsp['id']}/serahkan", follow_redirects=True)
    assert post_serah.status_code == 200
    stok_paracetamol_akhir = query_db("SELECT stok_saat_ini FROM obat WHERE id = 1", one=True)['stok_saat_ini']
    assert stok_paracetamol_akhir == stok_paracetamol_awal - 10, f"Stok tidak terpotong! Awal: {stok_paracetamol_awal}, Akhir: {stok_paracetamol_akhir}"
    print(f"[5/6] Resep {rsp['no_resep']} Diserahkan! Stok obat terpotong otomatis dari {stok_paracetamol_awal} -> {stok_paracetamol_akhir}")

    # 6. Kasir Pembayaran & Cetak Kuitansi
    tagihan = query_db("SELECT id, total_tagihan, status_pembayaran FROM tagihan WHERE pendaftaran_id = %s", (reg['id'],), one=True)
    assert tagihan is not None
    assert float(tagihan['total_tagihan']) > 0
    
    post_bayar = client.post(f"/kasir/tagihan/{tagihan['id']}/bayar", data={
        'jumlah_bayar': str(int(tagihan['total_tagihan'])),
        'metode_pembayaran': 'QRIS',
        'no_referensi': 'QRIS-TEST-SUCCESS',
        'keterangan': 'Pembayaran simulasi e2e'
    }, follow_redirects=True)
    assert post_bayar.status_code == 200
    tagihan_lunas = query_db("SELECT status_pembayaran FROM tagihan WHERE id = %s", (tagihan['id'],), one=True)
    assert tagihan_lunas['status_pembayaran'] == 'Lunas'
    print(f"[6/6] Pembayaran Kasir Berhasil! Tagihan ID {tagihan['id']} berstatus: {tagihan_lunas['status_pembayaran']}")

    # 7. Test Backup Database Endpoint
    res_backup = client.get('/pengaturan/backup')
    assert res_backup.status_code == 200
    assert b"CREATE TABLE" in res_backup.data
    print("[BONUS] Fitur Unduh Backup SQL Database berfungsi sempurna!")

    print("\n=== SEMUA ALUR END-TO-END TERVALIDASI SUKSES 100%! ===")
    return True

if __name__ == '__main__':
    ok = run_e2e()
    sys.exit(0 if ok else 1)
