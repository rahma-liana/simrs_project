from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from database import query_db, execute_db
from helpers import login_required, log_audit, generate_no_pendaftaran, generate_no_antrean, get_hospital_profile

pendaftaran_bp = Blueprint('pendaftaran', __name__, url_prefix='/pendaftaran')

@pendaftaran_bp.route('/')
@login_required
def index():
    tgl = request.args.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
    poli_id = request.args.get('poli_id', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    
    query = """
        SELECT p.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.no_telepon,
               d.nama_dokter, pol.nama_poli, pol.kode_poli,
               rm.id as rekam_medis_id, t.id as tagihan_id, t.status_pembayaran
        FROM pendaftaran p
        JOIN pasien pas ON p.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        LEFT JOIN rekam_medis rm ON p.id = rm.pendaftaran_id
        LEFT JOIN tagihan t ON p.id = t.pendaftaran_id
        WHERE 1=1
    """
    params = []
    
    if tgl:
        query += " AND p.tanggal_kunjungan = %s"
        params.append(tgl)
    if poli_id:
        query += " AND p.poli_id = %s"
        params.append(poli_id)
    if status:
        query += " AND p.status_antrean = %s"
        params.append(status)
    if search:
        query += " AND (pas.nama_lengkap LIKE %s OR pas.no_rm LIKE %s OR p.no_pendaftaran LIKE %s)"
        s = f"%{search}%"
        params.extend([s, s, s])
        
    query += """ ORDER BY 
        CASE p.status_antrean
            WHEN 'Sedang Diperiksa' THEN 1
            WHEN 'Dipanggil' THEN 2
            WHEN 'Menunggu' THEN 3
            WHEN 'Selesai' THEN 4
            ELSE 5
        END, p.no_antrean ASC"""
        
    pendaftaran_list = query_db(query, tuple(params))
    poli_list = query_db("SELECT * FROM poli WHERE status_aktif = 'Aktif' ORDER BY nama_poli ASC")
    
    # Ringkasan antrean hari ini
    summary = query_db("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status_antrean = 'Menunggu' THEN 1 ELSE 0 END) as menunggu,
            SUM(CASE WHEN status_antrean = 'Dipanggil' THEN 1 ELSE 0 END) as dipanggil,
            SUM(CASE WHEN status_antrean = 'Sedang Diperiksa' THEN 1 ELSE 0 END) as diperiksa,
            SUM(CASE WHEN status_antrean = 'Selesai' THEN 1 ELSE 0 END) as selesai
        FROM pendaftaran 
        WHERE tanggal_kunjungan = %s
    """, (tgl,), one=True)
    
    return render_template(
        'pendaftaran/index.html',
        pendaftaran_list=pendaftaran_list,
        poli_list=poli_list,
        selected_tanggal=tgl,
        selected_poli=poli_id,
        selected_status=status,
        search=search,
        summary=summary
    )

@pendaftaran_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    pasien_list = query_db("SELECT id, no_rm, nama_lengkap, no_telepon, alamat FROM pasien ORDER BY nama_lengkap ASC")
    poli_list = query_db("SELECT id, kode_poli, nama_poli FROM poli WHERE status_aktif = 'Aktif' ORDER BY nama_poli ASC")
    
    preselected_pasien_id = request.args.get('pasien_id', '')
    
    if request.method == 'POST':
        pasien_id = request.form.get('pasien_id')
        poli_id = request.form.get('poli_id')
        dokter_id = request.form.get('dokter_id')
        tanggal_kunjungan = request.form.get('tanggal_kunjungan', datetime.now().strftime('%Y-%m-%d'))
        keluhan_awal = request.form.get('keluhan_awal', '').strip()
        catatan = request.form.get('catatan', '').strip()
        
        if not pasien_id or not poli_id or not dokter_id or not tanggal_kunjungan:
            flash('Harap lengkapi Pasien, Poliklinik, Dokter, dan Tanggal Kunjungan.', 'danger')
            return render_template('pendaftaran/form.html', pasien_list=pasien_list, poli_list=poli_list)
            
        no_pendaftaran = generate_no_pendaftaran()
        no_antrean = generate_no_antrean(poli_id, tanggal_kunjungan)
        waktu_daftar = datetime.now().strftime('%H:%M:%S')
        
        try:
            reg_id, _ = execute_db(
                """INSERT INTO pendaftaran (no_pendaftaran, no_antrean, pasien_id, dokter_id, poli_id, 
                                          tanggal_kunjungan, waktu_daftar, keluhan_awal, status_antrean, catatan)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu', %s)""",
                (no_pendaftaran, no_antrean, pasien_id, dokter_id, poli_id, 
                 tanggal_kunjungan, waktu_daftar, keluhan_awal, catatan)
            )
            
            # Otomatis buat tagihan awal (biaya pendaftaran + biaya konsultasi dokter)
            hosp_profile = get_hospital_profile()
            biaya_daftar = hosp_profile.get('biaya_pendaftaran_default', 25000.00)
            
            doc = query_db("SELECT biaya_konsultasi FROM dokter WHERE id = %s", (dokter_id,), one=True)
            biaya_konsul = doc['biaya_konsultasi'] if doc else 50000.00
            total_awal = float(biaya_daftar) + float(biaya_konsul)
            
            from helpers import generate_no_tagihan
            no_tagihan = generate_no_tagihan()
            execute_db(
                """INSERT INTO tagihan (no_tagihan, pendaftaran_id, pasien_id, tanggal_tagihan, 
                                      biaya_pendaftaran, biaya_konsultasi, biaya_tindakan, biaya_obat, 
                                      total_tagihan, status_pembayaran)
                   VALUES (%s, %s, %s, %s, %s, %s, 0, 0, %s, 'Belum Dibayar')""",
                (no_tagihan, reg_id, pasien_id, tanggal_kunjungan, biaya_daftar, biaya_konsul, total_awal)
            )
            
            pasien = query_db("SELECT nama_lengkap, no_rm FROM pasien WHERE id = %s", (pasien_id,), one=True)
            log_audit('Pendaftaran Kunjungan', 'Pendaftaran', f"Mendaftarkan {pasien['nama_lengkap']} (No. Antrean: {no_antrean}, Reg: {no_pendaftaran})")
            
            flash(f"Pendaftaran berhasil! Nomor antrean: {no_antrean} ({no_pendaftaran})", 'success')
            return redirect(url_for('pendaftaran.cetak_antrean', id=reg_id))
        except Exception as e:
            flash(f"Gagal melakukan pendaftaran kunjungan: {str(e)}", 'danger')
            
    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template('pendaftaran/form.html', pasien_list=pasien_list, poli_list=poli_list, 
                           today_str=today_str, preselected_pasien_id=preselected_pasien_id)

@pendaftaran_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    status_baru = request.form.get('status_antrean')
    valid_status = ['Menunggu', 'Dipanggil', 'Sedang Diperiksa', 'Selesai', 'Dibatalkan']
    
    if status_baru not in valid_status:
        flash('Status antrean tidak valid.', 'danger')
        return redirect(url_for('pendaftaran.index'))
        
    pendaftaran = query_db("SELECT * FROM pendaftaran WHERE id = %s", (id,), one=True)
    if not pendaftaran:
        flash('Data pendaftaran tidak ditemukan.', 'danger')
        return redirect(url_for('pendaftaran.index'))
        
    try:
        execute_db("UPDATE pendaftaran SET status_antrean = %s WHERE id = %s", (status_baru, id))
        log_audit('Update Status Antrean', 'Pendaftaran', f"Antrean {pendaftaran['no_antrean']} diubah menjadi {status_baru}")
        flash(f"Status antrean {pendaftaran['no_antrean']} berhasil diubah menjadi: {status_baru}", 'success')
    except Exception as e:
        flash(f"Gagal memperbarui status antrean: {str(e)}", 'danger')
        
    return redirect(request.referrer or url_for('pendaftaran.index'))

@pendaftaran_bp.route('/<int:id>/cetak-antrean')
@login_required
def cetak_antrean(id):
    pendaftaran = query_db("""
        SELECT p.*, pas.nama_lengkap as nama_pasien, pas.no_rm,
               d.nama_dokter, pol.nama_poli, pol.lokasi
        FROM pendaftaran p
        JOIN pasien pas ON p.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        WHERE p.id = %s
    """, (id,), one=True)
    
    if not pendaftaran:
        flash('Data pendaftaran tidak ditemukan.', 'danger')
        return redirect(url_for('pendaftaran.index'))
        
    hosp = get_hospital_profile()
    return render_template('pendaftaran/cetak_antrean.html', p=pendaftaran, hosp=hosp)
