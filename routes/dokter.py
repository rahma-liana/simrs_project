from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import query_db, execute_db
from helpers import login_required, log_audit

dokter_bp = Blueprint('dokter', __name__, url_prefix='/dokter')

@dokter_bp.route('/')
@login_required
def index():
    dokter_list = query_db("""
        SELECT d.*, p.nama_poli, p.kode_poli, COUNT(j.id) as total_jadwal
        FROM dokter d
        JOIN poli p ON d.poli_id = p.id
        LEFT JOIN jadwal_dokter j ON d.id = j.dokter_id
        GROUP BY d.id
        ORDER BY d.id ASC
    """)
    return render_template('dokter/index.html', dokter_list=dokter_list)

@dokter_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    poli_list = query_db("SELECT * FROM poli WHERE status_aktif = 'Aktif' ORDER BY nama_poli ASC")
    
    if request.method == 'POST':
        nip_sip = request.form.get('nip_sip', '').strip()
        nama_dokter = request.form.get('nama_dokter', '').strip()
        poli_id = request.form.get('poli_id')
        spesialisasi = request.form.get('spesialisasi', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', 'L')
        no_telepon = request.form.get('no_telepon', '').strip()
        email = request.form.get('email', '').strip()
        biaya_konsultasi = request.form.get('biaya_konsultasi', '50000').replace('.', '')
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        if not nip_sip or not nama_dokter or not poli_id:
            flash('Harap lengkapi NIP/SIP, Nama Dokter, dan Poliklinik.', 'danger')
            return render_template('dokter/form.html', poli_list=poli_list, form=request.form, action='tambah')
            
        existing = query_db("SELECT id FROM dokter WHERE nip_sip = %s LIMIT 1", (nip_sip,), one=True)
        if existing:
            flash(f"Dokter dengan NIP/SIP {nip_sip} sudah terdaftar.", 'danger')
            return render_template('dokter/form.html', poli_list=poli_list, form=request.form, action='tambah')
            
        try:
            execute_db(
                """INSERT INTO dokter (nip_sip, nama_dokter, poli_id, spesialisasi, jenis_kelamin, 
                                      no_telepon, email, biaya_konsultasi, status_aktif)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (nip_sip, nama_dokter, poli_id, spesialisasi, jenis_kelamin, 
                 no_telepon, email, biaya_konsultasi, status_aktif)
            )
            log_audit('Tambah Dokter', 'Dokter', f"Menambahkan dokter baru: {nama_dokter} ({nip_sip})")
            flash(f"Dokter {nama_dokter} berhasil ditambahkan!", 'success')
            return redirect(url_for('dokter.index'))
        except Exception as e:
            flash(f"Gagal menambahkan data dokter: {str(e)}", 'danger')
            
    return render_template('dokter/form.html', poli_list=poli_list, action='tambah')

@dokter_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    dokter = query_db("SELECT * FROM dokter WHERE id = %s", (id,), one=True)
    if not dokter:
        flash('Data dokter tidak ditemukan.', 'danger')
        return redirect(url_for('dokter.index'))
        
    poli_list = query_db("SELECT * FROM poli WHERE status_aktif = 'Aktif' ORDER BY nama_poli ASC")
    
    if request.method == 'POST':
        nip_sip = request.form.get('nip_sip', '').strip()
        nama_dokter = request.form.get('nama_dokter', '').strip()
        poli_id = request.form.get('poli_id')
        spesialisasi = request.form.get('spesialisasi', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', 'L')
        no_telepon = request.form.get('no_telepon', '').strip()
        email = request.form.get('email', '').strip()
        biaya_konsultasi = request.form.get('biaya_konsultasi', '50000').replace('.', '')
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        existing = query_db("SELECT id FROM dokter WHERE nip_sip = %s AND id != %s LIMIT 1", (nip_sip, id), one=True)
        if existing:
            flash(f"NIP/SIP {nip_sip} sudah digunakan oleh dokter lain.", 'danger')
            return render_template('dokter/form.html', dokter=dokter, poli_list=poli_list, action='edit')
            
        try:
            execute_db(
                """UPDATE dokter SET nip_sip=%s, nama_dokter=%s, poli_id=%s, spesialisasi=%s, 
                                     jenis_kelamin=%s, no_telepon=%s, email=%s, biaya_konsultasi=%s, 
                                     status_aktif=%s WHERE id=%s""",
                (nip_sip, nama_dokter, poli_id, spesialisasi, jenis_kelamin, 
                 no_telepon, email, biaya_konsultasi, status_aktif, id)
            )
            log_audit('Edit Dokter', 'Dokter', f"Mengubah data dokter: {nama_dokter} ({nip_sip})")
            flash(f"Data dokter {nama_dokter} berhasil diperbarui!", 'success')
            return redirect(url_for('dokter.index'))
        except Exception as e:
            flash(f"Gagal memperbarui data dokter: {str(e)}", 'danger')
            
    return render_template('dokter/form.html', dokter=dokter, poli_list=poli_list, action='edit')

@dokter_bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    dokter = query_db("SELECT * FROM dokter WHERE id = %s", (id,), one=True)
    if not dokter:
        flash('Data dokter tidak ditemukan.', 'danger')
        return redirect(url_for('dokter.index'))
        
    has_pendaftaran = query_db("SELECT id FROM pendaftaran WHERE dokter_id = %s LIMIT 1", (id,), one=True)
    if has_pendaftaran:
        flash(f"Dokter {dokter['nama_dokter']} tidak dapat dihapus karena sudah memiliki data riwayat pelayanan pasien.", 'danger')
        return redirect(url_for('dokter.index'))
        
    try:
        execute_db("DELETE FROM dokter WHERE id = %s", (id,))
        log_audit('Hapus Dokter', 'Dokter', f"Menghapus dokter: {dokter['nama_dokter']}")
        flash(f"Data dokter {dokter['nama_dokter']} berhasil dihapus.", 'success')
    except Exception as e:
        flash(f"Gagal menghapus data dokter: {str(e)}", 'danger')
        
    return redirect(url_for('dokter.index'))

@dokter_bp.route('/api/by-poli/<int:poli_id>')
@login_required
def get_by_poli(poli_id):
    """Endpoint API JSON untuk mengambil daftar dokter aktif berdasarkan poli."""
    dokters = query_db(
        "SELECT id, nama_dokter, spesialisasi, biaya_konsultasi FROM dokter WHERE poli_id = %s AND status_aktif = 'Aktif' ORDER BY nama_dokter ASC",
        (poli_id,)
    )
    return jsonify(dokters)
