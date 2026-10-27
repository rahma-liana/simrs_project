from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db
from helpers import login_required, log_audit

tindakan_bp = Blueprint('tindakan', __name__, url_prefix='/tindakan')

@tindakan_bp.route('/')
@login_required
def index():
    tindakan_list = query_db("SELECT * FROM tindakan_medis ORDER BY id ASC")
    return render_template('tindakan/index.html', tindakan_list=tindakan_list)

@tindakan_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        kode_tindakan = request.form.get('kode_tindakan', '').strip().upper()
        nama_tindakan = request.form.get('nama_tindakan', '').strip()
        kategori = request.form.get('kategori', 'Umum').strip()
        tarif = request.form.get('tarif', '0').replace('.', '')
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        if not kode_tindakan or not nama_tindakan or not tarif:
            flash('Harap lengkapi Kode Tindakan, Nama Tindakan, dan Tarif.', 'danger')
            return render_template('tindakan/form.html', form=request.form, action='tambah')
            
        existing = query_db("SELECT id FROM tindakan_medis WHERE kode_tindakan = %s LIMIT 1", (kode_tindakan,), one=True)
        if existing:
            flash(f"Tindakan dengan kode {kode_tindakan} sudah ada.", 'danger')
            return render_template('tindakan/form.html', form=request.form, action='tambah')
            
        try:
            execute_db(
                """INSERT INTO tindakan_medis (kode_tindakan, nama_tindakan, kategori, tarif, keterangan, status_aktif)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (kode_tindakan, nama_tindakan, kategori, tarif, keterangan, status_aktif)
            )
            log_audit('Tambah Tindakan Medis', 'Tindakan', f"Menambahkan tindakan medis: {nama_tindakan} ({kode_tindakan})")
            flash(f"Tindakan medis {nama_tindakan} berhasil ditambahkan!", 'success')
            return redirect(url_for('tindakan.index'))
        except Exception as e:
            flash(f"Gagal menambahkan tindakan medis: {str(e)}", 'danger')
            
    return render_template('tindakan/form.html', action='tambah')

@tindakan_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tindakan = query_db("SELECT * FROM tindakan_medis WHERE id = %s", (id,), one=True)
    if not tindakan:
        flash('Data tindakan tidak ditemukan.', 'danger')
        return redirect(url_for('tindakan.index'))
        
    if request.method == 'POST':
        kode_tindakan = request.form.get('kode_tindakan', '').strip().upper()
        nama_tindakan = request.form.get('nama_tindakan', '').strip()
        kategori = request.form.get('kategori', 'Umum').strip()
        tarif = request.form.get('tarif', '0').replace('.', '')
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        try:
            execute_db(
                """UPDATE tindakan_medis 
                   SET kode_tindakan=%s, nama_tindakan=%s, kategori=%s, tarif=%s, keterangan=%s, status_aktif=%s
                   WHERE id=%s""",
                (kode_tindakan, nama_tindakan, kategori, tarif, keterangan, status_aktif, id)
            )
            log_audit('Edit Tindakan Medis', 'Tindakan', f"Mengubah tindakan: {nama_tindakan} ({kode_tindakan})")
            flash(f"Tindakan medis {nama_tindakan} berhasil diperbarui!", 'success')
            return redirect(url_for('tindakan.index'))
        except Exception as e:
            flash(f"Gagal memperbarui tindakan: {str(e)}", 'danger')
            
    return render_template('tindakan/form.html', tindakan=tindakan, action='edit')

@tindakan_bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    has_usage = query_db("SELECT id FROM rekam_medis_tindakan WHERE tindakan_id = %s LIMIT 1", (id,), one=True)
    if has_usage:
        flash('Tindakan ini tidak dapat dihapus karena sudah tercatat dalam riwayat rekam medis pasien.', 'danger')
        return redirect(url_for('tindakan.index'))
    try:
        execute_db("DELETE FROM tindakan_medis WHERE id = %s", (id,))
        flash('Tindakan medis berhasil dihapus.', 'success')
    except Exception as e:
        flash(f"Gagal menghapus tindakan: {str(e)}", 'danger')
    return redirect(url_for('tindakan.index'))
