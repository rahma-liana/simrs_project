from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db
from helpers import login_required, log_audit

jadwal_bp = Blueprint('jadwal', __name__, url_prefix='/jadwal')

HARI_LIST = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

@jadwal_bp.route('/')
@login_required
def index():
    filter_hari = request.args.get('hari', '')
    filter_poli = request.args.get('poli_id', '')
    
    query = """
        SELECT j.*, d.nama_dokter, d.spesialisasi, p.nama_poli, p.kode_poli
        FROM jadwal_dokter j
        JOIN dokter d ON j.dokter_id = d.id
        JOIN poli p ON d.poli_id = p.id
        WHERE 1=1
    """
    params = []
    if filter_hari:
        query += " AND j.hari = %s"
        params.append(filter_hari)
    if filter_poli:
        query += " AND p.id = %s"
        params.append(filter_poli)
        
    query += " ORDER BY FIELD(j.hari, 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'), j.jam_mulai ASC"
    jadwal_list = query_db(query, tuple(params))
    poli_list = query_db("SELECT * FROM poli WHERE status_aktif = 'Aktif' ORDER BY nama_poli ASC")
    
    return render_template('jadwal/index.html', jadwal_list=jadwal_list, hari_list=HARI_LIST, 
                           poli_list=poli_list, filter_hari=filter_hari, filter_poli=filter_poli)

@jadwal_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    dokter_list = query_db("""
        SELECT d.id, d.nama_dokter, d.spesialisasi, p.nama_poli 
        FROM dokter d 
        JOIN poli p ON d.poli_id = p.id 
        WHERE d.status_aktif = 'Aktif' 
        ORDER BY d.nama_dokter ASC
    """)
    
    if request.method == 'POST':
        dokter_id = request.form.get('dokter_id')
        hari = request.form.get('hari')
        jam_mulai = request.form.get('jam_mulai')
        jam_selesai = request.form.get('jam_selesai')
        kuota_pasien = request.form.get('kuota_pasien', 30)
        status = request.form.get('status', 'Aktif')
        
        if not dokter_id or not hari or not jam_mulai or not jam_selesai:
            flash('Harap lengkapi semua isian jadwal praktik.', 'danger')
            return render_template('jadwal/form.html', dokter_list=dokter_list, hari_list=HARI_LIST, action='tambah')
            
        try:
            execute_db(
                """INSERT INTO jadwal_dokter (dokter_id, hari, jam_mulai, jam_selesai, kuota_pasien, status)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (dokter_id, hari, jam_mulai, jam_selesai, kuota_pasien, status)
            )
            log_audit('Tambah Jadwal Dokter', 'Jadwal', f"Menambahkan jadwal dokter ID {dokter_id} hari {hari} jam {jam_mulai}-{jam_selesai}")
            flash('Jadwal praktik dokter berhasil ditambahkan!', 'success')
            return redirect(url_for('jadwal.index'))
        except Exception as e:
            flash(f"Gagal menambahkan jadwal dokter: {str(e)}", 'danger')
            
    return render_template('jadwal/form.html', dokter_list=dokter_list, hari_list=HARI_LIST, action='tambah')

@jadwal_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    jadwal = query_db("SELECT * FROM jadwal_dokter WHERE id = %s", (id,), one=True)
    if not jadwal:
        flash('Data jadwal praktik tidak ditemukan.', 'danger')
        return redirect(url_for('jadwal.index'))
        
    dokter_list = query_db("""
        SELECT d.id, d.nama_dokter, d.spesialisasi, p.nama_poli 
        FROM dokter d 
        JOIN poli p ON d.poli_id = p.id 
        WHERE d.status_aktif = 'Aktif' 
        ORDER BY d.nama_dokter ASC
    """)
    
    if request.method == 'POST':
        dokter_id = request.form.get('dokter_id')
        hari = request.form.get('hari')
        jam_mulai = request.form.get('jam_mulai')
        jam_selesai = request.form.get('jam_selesai')
        kuota_pasien = request.form.get('kuota_pasien', 30)
        status = request.form.get('status', 'Aktif')
        
        try:
            execute_db(
                """UPDATE jadwal_dokter 
                   SET dokter_id=%s, hari=%s, jam_mulai=%s, jam_selesai=%s, kuota_pasien=%s, status=%s 
                   WHERE id=%s""",
                (dokter_id, hari, jam_mulai, jam_selesai, kuota_pasien, status, id)
            )
            log_audit('Edit Jadwal Dokter', 'Jadwal', f"Mengubah jadwal dokter ID {dokter_id} ({hari})")
            flash('Jadwal praktik dokter berhasil diperbarui!', 'success')
            return redirect(url_for('jadwal.index'))
        except Exception as e:
            flash(f"Gagal memperbarui jadwal: {str(e)}", 'danger')
            
    return render_template('jadwal/form.html', jadwal=jadwal, dokter_list=dokter_list, hari_list=HARI_LIST, action='edit')

@jadwal_bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    try:
        execute_db("DELETE FROM jadwal_dokter WHERE id = %s", (id,))
        log_audit('Hapus Jadwal Dokter', 'Jadwal', f"Menghapus jadwal dokter ID {id}")
        flash('Jadwal dokter berhasil dihapus.', 'success')
    except Exception as e:
        flash(f"Gagal menghapus jadwal: {str(e)}", 'danger')
    return redirect(url_for('jadwal.index'))
