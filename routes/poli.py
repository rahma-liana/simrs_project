from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db
from helpers import login_required, log_audit

poli_bp = Blueprint('poli', __name__, url_prefix='/poli')

@poli_bp.route('/')
@login_required
def index():
    poli_list = query_db("""
        SELECT p.*, COUNT(d.id) as total_dokter 
        FROM poli p
        LEFT JOIN dokter d ON p.id = d.poli_id AND d.status_aktif = 'Aktif'
        GROUP BY p.id
        ORDER BY p.kode_poli ASC
    """)
    return render_template('poli/index.html', poli_list=poli_list)

@poli_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        kode_poli = request.form.get('kode_poli', '').strip().upper()
        nama_poli = request.form.get('nama_poli', '').strip()
        lokasi = request.form.get('lokasi', '').strip()
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        if not kode_poli or not nama_poli or not lokasi:
            flash('Harap lengkapi kode poli, nama poli, dan lokasi ruangan.', 'danger')
            return render_template('poli/form.html', form=request.form, action='tambah')
            
        existing = query_db("SELECT id FROM poli WHERE kode_poli = %s LIMIT 1", (kode_poli,), one=True)
        if existing:
            flash(f"Poli dengan kode {kode_poli} sudah ada.", 'danger')
            return render_template('poli/form.html', form=request.form, action='tambah')
            
        try:
            execute_db(
                "INSERT INTO poli (kode_poli, nama_poli, lokasi, keterangan, status_aktif) VALUES (%s, %s, %s, %s, %s)",
                (kode_poli, nama_poli, lokasi, keterangan, status_aktif)
            )
            log_audit('Tambah Poli', 'Poli', f"Menambahkan Poliklinik baru: {nama_poli} ({kode_poli})")
            flash(f"Poliklinik {nama_poli} berhasil ditambahkan!", 'success')
            return redirect(url_for('poli.index'))
        except Exception as e:
            flash(f"Gagal menambahkan data poli: {str(e)}", 'danger')
            
    return render_template('poli/form.html', action='tambah')

@poli_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    poli = query_db("SELECT * FROM poli WHERE id = %s", (id,), one=True)
    if not poli:
        flash('Data poliklinik tidak ditemukan.', 'danger')
        return redirect(url_for('poli.index'))
        
    if request.method == 'POST':
        kode_poli = request.form.get('kode_poli', '').strip().upper()
        nama_poli = request.form.get('nama_poli', '').strip()
        lokasi = request.form.get('lokasi', '').strip()
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        existing = query_db("SELECT id FROM poli WHERE kode_poli = %s AND id != %s LIMIT 1", (kode_poli, id), one=True)
        if existing:
            flash(f"Kode poli {kode_poli} sudah digunakan oleh poliklinik lain.", 'danger')
            return render_template('poli/form.html', poli=poli, action='edit')
            
        try:
            execute_db(
                "UPDATE poli SET kode_poli=%s, nama_poli=%s, lokasi=%s, keterangan=%s, status_aktif=%s WHERE id=%s",
                (kode_poli, nama_poli, lokasi, keterangan, status_aktif, id)
            )
            log_audit('Edit Poli', 'Poli', f"Mengubah data Poliklinik: {nama_poli} ({kode_poli})")
            flash(f"Data Poliklinik {nama_poli} berhasil diperbarui!", 'success')
            return redirect(url_for('poli.index'))
        except Exception as e:
            flash(f"Gagal memperbarui data poli: {str(e)}", 'danger')
            
    return render_template('poli/form.html', poli=poli, action='edit')

@poli_bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    poli = query_db("SELECT * FROM poli WHERE id = %s", (id,), one=True)
    if not poli:
        flash('Data poli tidak ditemukan.', 'danger')
        return redirect(url_for('poli.index'))
        
    has_dokter = query_db("SELECT id FROM dokter WHERE poli_id = %s LIMIT 1", (id,), one=True)
    has_pendaftaran = query_db("SELECT id FROM pendaftaran WHERE poli_id = %s LIMIT 1", (id,), one=True)
    
    if has_dokter or has_pendaftaran:
        flash(f"Poli {poli['nama_poli']} tidak dapat dihapus karena masih terhubung dengan dokter atau kunjungan pasien.", 'danger')
        return redirect(url_for('poli.index'))
        
    try:
        execute_db("DELETE FROM poli WHERE id = %s", (id,))
        log_audit('Hapus Poli', 'Poli', f"Menghapus Poliklinik: {poli['nama_poli']}")
        flash(f"Poliklinik {poli['nama_poli']} berhasil dihapus.", 'success')
    except Exception as e:
        flash(f"Gagal menghapus poli: {str(e)}", 'danger')
        
    return redirect(url_for('poli.index'))
