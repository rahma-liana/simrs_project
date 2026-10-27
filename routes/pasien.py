from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db
from helpers import login_required, log_audit, generate_no_rm

pasien_bp = Blueprint('pasien', __name__, url_prefix='/pasien')

@pasien_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    if search:
        query = """
            SELECT * FROM pasien 
            WHERE no_rm LIKE %s OR nama_lengkap LIKE %s OR nik LIKE %s OR no_telepon LIKE %s
            ORDER BY id DESC
        """
        param = f"%{search}%"
        pasien_list = query_db(query, (param, param, param, param))
    else:
        pasien_list = query_db("SELECT * FROM pasien ORDER BY id DESC")
        
    return render_template('pasien/index.html', pasien_list=pasien_list, search=search)

@pasien_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        no_rm = request.form.get('no_rm', '').strip() or generate_no_rm()
        nik = request.form.get('nik', '').strip()
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '')
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '')
        alamat = request.form.get('alamat', '').strip()
        no_telepon = request.form.get('no_telepon', '').strip()
        golongan_darah = request.form.get('golongan_darah', '-')
        pekerjaan = request.form.get('pekerjaan', '').strip()
        riwayat_alergi = request.form.get('riwayat_alergi', '').strip()
        kontak_darurat_nama = request.form.get('kontak_darurat_nama', '').strip()
        kontak_darurat_telp = request.form.get('kontak_darurat_telp', '').strip()
        
        # Validasi sederhana
        if not nik or not nama_lengkap or not tanggal_lahir or not no_telepon:
            flash('Harap lengkapi semua bidang wajib (NIK, Nama, Tanggal Lahir, No. Telepon).', 'danger')
            return render_template('pasien/form.html', form=request.form, action='tambah', auto_no_rm=no_rm)
            
        # Cek duplikasi NIK atau No. RM
        existing = query_db("SELECT id FROM pasien WHERE nik = %s OR no_rm = %s LIMIT 1", (nik, no_rm), one=True)
        if existing:
            flash('Pasien dengan NIK atau No. Rekam Medis tersebut sudah terdaftar di sistem.', 'danger')
            return render_template('pasien/form.html', form=request.form, action='tambah', auto_no_rm=generate_no_rm())
            
        try:
            execute_db(
                """INSERT INTO pasien (no_rm, nik, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, 
                                      alamat, no_telepon, golongan_darah, pekerjaan, riwayat_alergi, 
                                      kontak_darurat_nama, kontak_darurat_telp)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (no_rm, nik, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, 
                 alamat, no_telepon, golongan_darah, pekerjaan, riwayat_alergi, 
                 kontak_darurat_nama, kontak_darurat_telp)
            )
            log_audit('Tambah Pasien', 'Pasien', f"Menambahkan pasien baru {nama_lengkap} (No. RM: {no_rm})")
            flash(f"Pasien {nama_lengkap} berhasil didaftarkan dengan No. RM {no_rm}!", 'success')
            return redirect(url_for('pasien.index'))
        except Exception as e:
            flash(f"Gagal menambahkan data pasien: {str(e)}", 'danger')
            
    auto_no_rm = generate_no_rm()
    return render_template('pasien/form.html', action='tambah', auto_no_rm=auto_no_rm)

@pasien_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    pasien = query_db("SELECT * FROM pasien WHERE id = %s", (id,), one=True)
    if not pasien:
        flash('Data pasien tidak ditemukan.', 'danger')
        return redirect(url_for('pasien.index'))
        
    if request.method == 'POST':
        nik = request.form.get('nik', '').strip()
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '')
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '')
        alamat = request.form.get('alamat', '').strip()
        no_telepon = request.form.get('no_telepon', '').strip()
        golongan_darah = request.form.get('golongan_darah', '-')
        pekerjaan = request.form.get('pekerjaan', '').strip()
        riwayat_alergi = request.form.get('riwayat_alergi', '').strip()
        kontak_darurat_nama = request.form.get('kontak_darurat_nama', '').strip()
        kontak_darurat_telp = request.form.get('kontak_darurat_telp', '').strip()
        
        # Cek duplikasi NIK selain id ini
        existing = query_db("SELECT id FROM pasien WHERE nik = %s AND id != %s LIMIT 1", (nik, id), one=True)
        if existing:
            flash('NIK tersebut sudah terdaftar pada pasien lain.', 'danger')
            return render_template('pasien/form.html', form=request.form, action='edit', pasien=pasien)
            
        try:
            execute_db(
                """UPDATE pasien SET nik=%s, nama_lengkap=%s, jenis_kelamin=%s, tempat_lahir=%s, 
                                     tanggal_lahir=%s, alamat=%s, no_telepon=%s, golongan_darah=%s, 
                                     pekerjaan=%s, riwayat_alergi=%s, kontak_darurat_nama=%s, kontak_darurat_telp=%s
                   WHERE id=%s""",
                (nik, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, 
                 alamat, no_telepon, golongan_darah, pekerjaan, riwayat_alergi, 
                 kontak_darurat_nama, kontak_darurat_telp, id)
            )
            log_audit('Edit Pasien', 'Pasien', f"Mengubah data pasien {nama_lengkap} (No. RM: {pasien['no_rm']})")
            flash(f"Data pasien {nama_lengkap} berhasil diperbarui!", 'success')
            return redirect(url_for('pasien.detail', id=id))
        except Exception as e:
            flash(f"Gagal memperbarui data pasien: {str(e)}", 'danger')
            
    return render_template('pasien/form.html', action='edit', pasien=pasien)

@pasien_bp.route('/<int:id>')
@login_required
def detail(id):
    pasien = query_db("SELECT * FROM pasien WHERE id = %s", (id,), one=True)
    if not pasien:
        flash('Data pasien tidak ditemukan.', 'danger')
        return redirect(url_for('pasien.index'))
        
    # Riwayat Kunjungan
    kunjungan = query_db(
        """SELECT p.*, d.nama_dokter, pol.nama_poli 
           FROM pendaftaran p
           JOIN dokter d ON p.dokter_id = d.id
           JOIN poli pol ON p.poli_id = pol.id
           WHERE p.pasien_id = %s
           ORDER BY p.tanggal_kunjungan DESC, p.waktu_daftar DESC""",
        (id,)
    )
    
    # Riwayat Rekam Medis
    rekam_medis = query_db(
        """SELECT rm.*, d.nama_dokter, p.no_pendaftaran, pol.nama_poli
           FROM rekam_medis rm
           JOIN pendaftaran p ON rm.pendaftaran_id = p.id
           JOIN dokter d ON rm.dokter_id = d.id
           JOIN poli pol ON p.poli_id = pol.id
           WHERE rm.pasien_id = %s
           ORDER BY rm.tanggal_periksa DESC, rm.waktu_periksa DESC""",
        (id,)
    )
    
    return render_template('pasien/detail.html', pasien=pasien, kunjungan=kunjungan, rekam_medis=rekam_medis)

@pasien_bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    pasien = query_db("SELECT * FROM pasien WHERE id = %s", (id,), one=True)
    if not pasien:
        flash('Data pasien tidak ditemukan.', 'danger')
        return redirect(url_for('pasien.index'))
        
    # Periksa apakah pasien memiliki riwayat kunjungan atau rekam medis
    has_kunjungan = query_db("SELECT id FROM pendaftaran WHERE pasien_id = %s LIMIT 1", (id,), one=True)
    if has_kunjungan:
        flash(f"Pasien {pasien['nama_lengkap']} tidak dapat dihapus karena sudah memiliki riwayat kunjungan dan rekam medis di rumah sakit.", 'danger')
        return redirect(url_for('pasien.index'))
        
    try:
        execute_db("DELETE FROM pasien WHERE id = %s", (id,))
        log_audit('Hapus Pasien', 'Pasien', f"Menghapus pasien {pasien['nama_lengkap']} (No. RM: {pasien['no_rm']})")
        flash(f"Data pasien {pasien['nama_lengkap']} berhasil dihapus dari sistem.", 'success')
    except Exception as e:
        flash(f"Gagal menghapus data pasien: {str(e)}", 'danger')
        
    return redirect(url_for('pasien.index'))
