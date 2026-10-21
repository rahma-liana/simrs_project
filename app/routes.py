from datetime import date
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db, query_all, query_one
from io import BytesIO
from openpyxl import Workbook

bp = Blueprint('main', __name__)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('main.login'))
        return fn(*args, **kwargs)
    return wrapper


@bp.route('/')
def index():
    return redirect(url_for('main.dashboard') if session.get('admin_id') else url_for('main.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_id'):
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        identity = request.form.get('identity', '').strip()
        password = request.form.get('password', '')
        user = query_one('SELECT id, username, email, password_hash, nama_lengkap FROM users WHERE (username=%s OR email=%s) AND aktif=1 LIMIT 1', (identity, identity))
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['admin_id'] = user['id']
            session['admin_name'] = user['nama_lengkap']
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO log_aktivitas (user_id, aktivitas, detail, alamat_ip) VALUES (%s,%s,%s,%s)', (user['id'], 'LOGIN', 'Admin berhasil login', request.remote_addr))
                conn.commit()
            finally:
                conn.close()
            flash('Login berhasil. Selamat datang!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Username/email atau password tidak sesuai.', 'danger')
    return render_template('login.html')


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    admin_id = session.get('admin_id')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO log_aktivitas (user_id, aktivitas, detail, alamat_ip) VALUES (%s,%s,%s,%s)', (admin_id, 'LOGOUT', 'Admin keluar dari sistem', request.remote_addr))
        conn.commit()
    finally:
        conn.close()
    session.clear()
    flash('Anda berhasil logout.', 'success')
    return redirect(url_for('main.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'pasien': query_one('SELECT COUNT(*) AS n FROM pasien WHERE deleted_at IS NULL')['n'],
        'dokter': query_one('SELECT COUNT(*) AS n FROM dokter WHERE aktif=1')['n'],
        'poli': query_one('SELECT COUNT(*) AS n FROM poli WHERE aktif=1')['n'],
        'kunjungan': query_one('SELECT COUNT(*) AS n FROM pendaftaran WHERE tanggal_kunjungan=CURDATE()')['n'],
        'antrean': query_one("SELECT COUNT(*) AS n FROM pendaftaran WHERE tanggal_kunjungan=CURDATE() AND status_antrean IN ('Menunggu','Dipanggil')")['n'],
        'transaksi': query_one('SELECT COUNT(*) AS n FROM tagihan WHERE DATE(created_at)=CURDATE()')['n'],
        'pendapatan': query_one("SELECT COALESCE(SUM(jumlah),0) AS n FROM pembayaran WHERE DATE(tanggal_bayar)=CURDATE()")['n'],
        'stok_menipis': query_one('SELECT COUNT(*) AS n FROM obat WHERE aktif=1 AND stok <= batas_stok_minimum')['n'],
    }
    antrean = query_all("SELECT p.nomor_antrean, ps.nama_lengkap, po.nama_poli, p.status_antrean FROM pendaftaran p JOIN pasien ps ON ps.id=p.pasien_id JOIN poli po ON po.id=p.poli_id WHERE p.tanggal_kunjungan=CURDATE() ORDER BY p.id DESC LIMIT 8")
    obat_tipis = query_all('SELECT nama_obat, stok, satuan FROM obat WHERE aktif=1 AND stok <= batas_stok_minimum ORDER BY stok ASC LIMIT 5')
    return render_template('dashboard.html', stats=stats, antrean=antrean, obat_tipis=obat_tipis)


@bp.route('/pasien')
@login_required
def pasien_index():
    q = request.args.get('q', '').strip()
    if q:
        pasien = query_all("SELECT * FROM pasien WHERE deleted_at IS NULL AND (nama_lengkap LIKE %s OR no_rekam_medis LIKE %s OR no_telepon LIKE %s) ORDER BY id DESC", (f'%{q}%', f'%{q}%', f'%{q}%'))
    else:
        pasien = query_all('SELECT * FROM pasien WHERE deleted_at IS NULL ORDER BY id DESC LIMIT 200')
    return render_template('pasien.html', pasien=pasien, q=q)


@bp.route('/pasien/tambah', methods=['POST'])
@login_required
def pasien_tambah():
    nama = request.form.get('nama_lengkap', '').strip()
    tanggal_lahir = request.form.get('tanggal_lahir') or None
    jk = request.form.get('jenis_kelamin')
    alamat = request.form.get('alamat', '').strip()
    telepon = request.form.get('no_telepon', '').strip()
    if not nama or jk not in ('Laki-laki', 'Perempuan'):
        flash('Nama dan jenis kelamin wajib diisi dengan benar.', 'danger')
        return redirect(url_for('main.pasien_index'))
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM pasien')
            nomor = cur.fetchone()['n'] + 1
            no_rm = f'RM-{date.today():%Y%m}-' + str(nomor).zfill(5)
            cur.execute('INSERT INTO pasien (no_rekam_medis,nama_lengkap,tanggal_lahir,jenis_kelamin,alamat,no_telepon) VALUES (%s,%s,%s,%s,%s,%s)', (no_rm, nama, tanggal_lahir, jk, alamat, telepon))
            cur.execute('INSERT INTO log_aktivitas (user_id, aktivitas, detail, alamat_ip) VALUES (%s,%s,%s,%s)', (session['admin_id'], 'TAMBAH_PASIEN', f'Menambahkan pasien {no_rm}', request.remote_addr))
        conn.commit()
        flash(f'Data pasien berhasil ditambahkan. Nomor RM: {no_rm}', 'success')
    except Exception:
        conn.rollback()
        current_app.logger.exception('Gagal menambahkan pasien')
        flash('Data pasien gagal disimpan. Periksa kembali data yang dimasukkan.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('main.pasien_index'))


@bp.route('/pasien/<int:pasien_id>/edit', methods=['POST'])
@login_required
def pasien_edit(pasien_id):
    nama = request.form.get('nama_lengkap', '').strip()
    tanggal_lahir = request.form.get('tanggal_lahir') or None
    jk = request.form.get('jenis_kelamin')
    alamat = request.form.get('alamat', '').strip()
    telepon = request.form.get('no_telepon', '').strip()
    if not nama or jk not in ('Laki-laki', 'Perempuan'):
        flash('Nama dan jenis kelamin wajib diisi.', 'danger')
        return redirect(url_for('main.pasien_index'))
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE pasien SET nama_lengkap=%s,tanggal_lahir=%s,jenis_kelamin=%s,alamat=%s,no_telepon=%s,updated_at=NOW() WHERE id=%s AND deleted_at IS NULL', (nama,tanggal_lahir,jk,alamat,telepon,pasien_id))
            cur.execute('INSERT INTO log_aktivitas (user_id, aktivitas, detail, alamat_ip) VALUES (%s,%s,%s,%s)', (session['admin_id'], 'EDIT_PASIEN', f'Memperbarui pasien ID {pasien_id}', request.remote_addr))
        conn.commit()
        flash('Data pasien berhasil diperbarui.', 'success')
    except Exception:
        conn.rollback()
        current_app.logger.exception('Gagal memperbarui pasien')
        flash('Data pasien gagal diperbarui.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('main.pasien_index'))


@bp.route('/pasien/<int:pasien_id>/hapus', methods=['POST'])
@login_required
def pasien_hapus(pasien_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE pasien SET deleted_at=NOW(), updated_at=NOW() WHERE id=%s AND deleted_at IS NULL', (pasien_id,))
            cur.execute('INSERT INTO log_aktivitas (user_id, aktivitas, detail, alamat_ip) VALUES (%s,%s,%s,%s)', (session['admin_id'], 'ARSIP_PASIEN', f'Mengarsipkan pasien ID {pasien_id}', request.remote_addr))
        conn.commit()
        flash('Data pasien diarsipkan dan tidak lagi tampil pada daftar aktif.', 'success')
    except Exception:
        conn.rollback()
        current_app.logger.exception('Gagal mengarsipkan pasien')
        flash('Data pasien gagal diarsipkan.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('main.pasien_index'))


@bp.route('/laporan/pasien.xlsx')
@login_required
def export_pasien():
    rows = query_all('SELECT no_rekam_medis,nama_lengkap,tanggal_lahir,jenis_kelamin,no_telepon,alamat FROM pasien WHERE deleted_at IS NULL ORDER BY nama_lengkap')
    wb = Workbook()
    ws = wb.active
    ws.title = 'Data Pasien'
    ws.append(['Nomor Rekam Medis','Nama Lengkap','Tanggal Lahir','Jenis Kelamin','Nomor Telepon','Alamat'])
    for r in rows:
        ws.append([r['no_rekam_medis'],r['nama_lengkap'],str(r['tanggal_lahir'] or ''),r['jenis_kelamin'],r['no_telepon'],r['alamat']])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return send_file(stream, as_attachment=True, download_name='laporan_data_pasien.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/<path:module>')
@login_required
def placeholder(module):
    allowed = {
        'dokter': ('Data Dokter', 'Kelola identitas dokter dan spesialisasi.'),
        'poli': ('Data Poli', 'Kelola unit pelayanan dan poli rumah sakit.'),
        'jadwal-dokter': ('Jadwal Dokter', 'Atur hari, jam praktik, dan kapasitas layanan.'),
        'pendaftaran': ('Pendaftaran dan Antrean', 'Daftarkan pasien dan pantau status antrean.'),
        'rekam-medis': ('Rekam Medis', 'Pencatatan pemeriksaan dan riwayat medis.'),
        'farmasi': ('Farmasi dan Obat', 'Kelola obat, stok, resep, dan pergerakan persediaan.'),
        'pembayaran': ('Kasir dan Pembayaran', 'Kelola tagihan, pembayaran, dan bukti transaksi.'),
        'laporan': ('Laporan Rumah Sakit', 'Pilih laporan untuk ditinjau, dicetak, atau diekspor.'),
        'pengaturan': ('Pengaturan Sistem', 'Kelola profil rumah sakit dan konfigurasi aplikasi.'),
    }
    if module not in allowed:
        return render_template('404.html'), 404
    title, description = allowed[module]
    return render_template('module_placeholder.html', title=title, description=description)
