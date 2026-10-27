from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database import query_db, execute_db, transaction_scope
from helpers import login_required, log_audit, generate_no_rekam_medis

rekam_medis_bp = Blueprint('rekam_medis', __name__, url_prefix='/rekam-medis')

@rekam_medis_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    tgl = request.args.get('tanggal', '')
    
    query = """
        SELECT rm.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.jenis_kelamin,
               d.nama_dokter, p.no_pendaftaran, pol.nama_poli,
               r.id as resep_id, r.status_resep
        FROM rekam_medis rm
        JOIN pendaftaran p ON rm.pendaftaran_id = p.id
        JOIN pasien pas ON rm.pasien_id = pas.id
        JOIN dokter d ON rm.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        LEFT JOIN resep r ON rm.id = r.rekam_medis_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (pas.nama_lengkap LIKE %s OR pas.no_rm LIKE %s OR rm.diagnosis LIKE %s OR rm.no_rekam_medis LIKE %s)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    if tgl:
        query += " AND rm.tanggal_periksa = %s"
        params.append(tgl)
        
    query += " ORDER BY rm.id DESC"
    rekam_medis_list = query_db(query, tuple(params))
    
    return render_template('rekam_medis/index.html', rekam_medis_list=rekam_medis_list, search=search, selected_tanggal=tgl)

@rekam_medis_bp.route('/periksa/<int:pendaftaran_id>', methods=['GET', 'POST'])
@login_required
def periksa(pendaftaran_id):
    pendaftaran = query_db("""
        SELECT p.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.tanggal_lahir, 
               pas.jenis_kelamin, pas.riwayat_alergi, pas.golongan_darah,
               d.nama_dokter, d.biaya_konsultasi, pol.nama_poli
        FROM pendaftaran p
        JOIN pasien pas ON p.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        WHERE p.id = %s
    """, (pendaftaran_id,), one=True)
    
    if not pendaftaran:
        flash('Data pendaftaran kunjungan tidak ditemukan.', 'danger')
        return redirect(url_for('pendaftaran.index'))
        
    # Cek apakah sudah pernah diperiksa sebelumnya
    existing = query_db("SELECT id FROM rekam_medis WHERE pendaftaran_id = %s", (pendaftaran_id,), one=True)
    if existing:
        return redirect(url_for('rekam_medis.detail', id=existing['id']))
        
    master_tindakan = query_db("SELECT * FROM tindakan_medis WHERE status_aktif = 'Aktif' ORDER BY kategori, nama_tindakan ASC")
    
    if request.method == 'POST':
        tekanan_darah = request.form.get('tekanan_darah', '').strip()
        suhu_tubuh = request.form.get('suhu_tubuh') or None
        berat_badan = request.form.get('berat_badan') or None
        tinggi_badan = request.form.get('tinggi_badan') or None
        denyut_nadi = request.form.get('denyut_nadi') or None
        keluhan_utama = request.form.get('keluhan_utama', '').strip()
        pemeriksaan_fisik = request.form.get('pemeriksaan_fisik', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        kode_icd10 = request.form.get('kode_icd10', '').strip().upper()
        tindakan_diberikan = request.form.get('tindakan_diberikan', '').strip()
        catatan_dokter = request.form.get('catatan_dokter', '').strip()
        tindakan_ids = request.form.getlist('tindakan_ids')
        
        if not keluhan_utama or not diagnosis:
            flash('Keluhan utama dan diagnosis dokter wajib diisi.', 'danger')
            return render_template('rekam_medis/form.html', p=pendaftaran, master_tindakan=master_tindakan)
            
        no_rmed = generate_no_rekam_medis()
        now_date = datetime.now().strftime('%Y-%m-%d')
        now_time = datetime.now().strftime('%H:%M:%S')
        
        try:
            with transaction_scope() as conn:
                with conn.cursor() as cursor:
                    # 1. Simpan rekam medis
                    cursor.execute(
                        """INSERT INTO rekam_medis (no_rekam_medis, pendaftaran_id, pasien_id, dokter_id, 
                                                  tanggal_periksa, waktu_periksa, tekanan_darah, suhu_tubuh, 
                                                  berat_badan, tinggi_badan, denyut_nadi, keluhan_utama, 
                                                  pemeriksaan_fisik, diagnosis, kode_icd10, tindakan_diberikan, catatan_dokter)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (no_rmed, pendaftaran_id, pendaftaran['pasien_id'], pendaftaran['dokter_id'],
                         now_date, now_time, tekanan_darah, suhu_tubuh, berat_badan, tinggi_badan, denyut_nadi,
                         keluhan_utama, pemeriksaan_fisik, diagnosis, kode_icd10, tindakan_diberikan, catatan_dokter)
                    )
                    rm_id = cursor.lastrowid
                    
                    # 2. Simpan tindakan medis terpilih & hitung total biaya tindakan
                    total_biaya_tindakan = 0.0
                    for tid in tindakan_ids:
                        cursor.execute("SELECT tarif, nama_tindakan FROM tindakan_medis WHERE id = %s", (tid,))
                        t_item = cursor.fetchone()
                        if t_item:
                            tarif = float(t_item['tarif'])
                            total_biaya_tindakan += tarif
                            cursor.execute(
                                "INSERT INTO rekam_medis_tindakan (rekam_medis_id, tindakan_id, biaya) VALUES (%s, %s, %s)",
                                (rm_id, tid, tarif)
                            )
                            
                    # 3. Update status antrean pendaftaran menjadi 'Selesai'
                    cursor.execute("UPDATE pendaftaran SET status_antrean = 'Selesai' WHERE id = %s", (pendaftaran_id,))
                    
                    # 4. Sinkronkan ke tabel tagihan
                    cursor.execute(
                        """UPDATE tagihan 
                           SET biaya_tindakan = %s,
                               total_tagihan = biaya_pendaftaran + biaya_konsultasi + %s + biaya_obat
                           WHERE pendaftaran_id = %s""",
                        (total_biaya_tindakan, total_biaya_tindakan, pendaftaran_id)
                    )
                    
            log_audit('Input Rekam Medis', 'Rekam Medis', f"Mencatat pemeriksaan {pendaftaran['nama_pasien']} ({no_rmed})")
            flash(f"Pemeriksaan medis berhasil disimpan dengan No. {no_rmed}!", 'success')
            
            # Tanya / tawarkan langsung buat resep obat
            if request.form.get('action') == 'simpan_dan_resep':
                return redirect(url_for('farmasi.buat_resep', rekam_medis_id=rm_id))
            return redirect(url_for('rekam_medis.detail', id=rm_id))
        except Exception as e:
            flash(f"Gagal menyimpan rekam medis: {str(e)}", 'danger')
            
    return render_template('rekam_medis/form.html', p=pendaftaran, master_tindakan=master_tindakan)

@rekam_medis_bp.route('/<int:id>')
@login_required
def detail(id):
    rm = query_db("""
        SELECT rm.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.tanggal_lahir, 
               pas.jenis_kelamin, pas.riwayat_alergi, pas.golongan_darah, pas.alamat, pas.no_telepon,
               d.nama_dokter, d.nip_sip, pol.nama_poli, p.no_pendaftaran, p.no_antrean,
               t.id as tagihan_id, t.total_tagihan, t.status_pembayaran
        FROM rekam_medis rm
        JOIN pendaftaran p ON rm.pendaftaran_id = p.id
        JOIN pasien pas ON rm.pasien_id = pas.id
        JOIN dokter d ON rm.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        LEFT JOIN tagihan t ON p.id = t.pendaftaran_id
        WHERE rm.id = %s
    """, (id,), one=True)
    
    if not rm:
        flash('Data rekam medis tidak ditemukan.', 'danger')
        return redirect(url_for('rekam_medis.index'))
        
    tindakan_list = query_db("""
        SELECT rmt.*, tm.nama_tindakan, tm.kategori, tm.kode_tindakan
        FROM rekam_medis_tindakan rmt
        JOIN tindakan_medis tm ON rmt.tindakan_id = tm.id
        WHERE rmt.rekam_medis_id = %s
    """, (id,))
    
    resep = query_db("SELECT * FROM resep WHERE rekam_medis_id = %s", (id,), one=True)
    detail_resep_list = []
    if resep:
        detail_resep_list = query_db("""
            SELECT dr.*, o.nama_obat, o.satuan, o.kode_obat
            FROM detail_resep dr
            JOIN obat o ON dr.obat_id = o.id
            WHERE dr.resep_id = %s
        """, (resep['id'],))
        
    return render_template('rekam_medis/detail.html', rm=rm, tindakan_list=tindakan_list, resep=resep, detail_resep=detail_resep_list)
