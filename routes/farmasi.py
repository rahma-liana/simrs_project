from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database import query_db, execute_db, transaction_scope
from helpers import login_required, log_audit, generate_no_resep

farmasi_bp = Blueprint('farmasi', __name__, url_prefix='/farmasi')

# -------------------------------------------------------------
# 1. MASTER OBAT & STOK
# -------------------------------------------------------------
@farmasi_bp.route('/obat')
@login_required
def obat_index():
    search = request.args.get('search', '').strip()
    kategori = request.args.get('kategori', '')
    filter_stok = request.args.get('filter_stok', '')
    
    query = "SELECT * FROM obat WHERE 1=1"
    params = []
    
    if search:
        query += " AND (nama_obat LIKE %s OR kode_obat LIKE %s)"
        s = f"%{search}%"
        params.extend([s, s])
    if kategori:
        query += " AND kategori = %s"
        params.append(kategori)
    if filter_stok == 'menipis':
        query += " AND stok_saat_ini <= stok_minimum"
        
    query += " ORDER BY nama_obat ASC"
    obat_list = query_db(query, tuple(params))
    
    kategori_list = query_db("SELECT DISTINCT kategori FROM obat WHERE kategori IS NOT NULL AND kategori != '' ORDER BY kategori ASC")
    
    return render_template('farmasi/obat_index.html', obat_list=obat_list, kategori_list=kategori_list,
                           search=search, selected_kategori=kategori, filter_stok=filter_stok)

@farmasi_bp.route('/obat/tambah', methods=['GET', 'POST'])
@login_required
def obat_tambah():
    if request.method == 'POST':
        kode_obat = request.form.get('kode_obat', '').strip().upper()
        nama_obat = request.form.get('nama_obat', '').strip()
        kategori = request.form.get('kategori', '').strip()
        satuan = request.form.get('satuan', '').strip()
        harga_beli = request.form.get('harga_beli', '0').replace('.', '')
        harga_jual = request.form.get('harga_jual', '0').replace('.', '')
        stok_saat_ini = int(request.form.get('stok_saat_ini', 0))
        stok_minimum = int(request.form.get('stok_minimum', 10))
        tanggal_kadaluwarsa = request.form.get('tanggal_kadaluwarsa')
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        if not kode_obat or not nama_obat or not satuan or not tanggal_kadaluwarsa:
            flash('Harap lengkapi Kode Obat, Nama, Satuan, dan Tanggal Kadaluwarsa.', 'danger')
            return render_template('farmasi/obat_form.html', form=request.form, action='tambah')
            
        existing = query_db("SELECT id FROM obat WHERE kode_obat = %s LIMIT 1", (kode_obat,), one=True)
        if existing:
            flash(f"Obat dengan kode {kode_obat} sudah terdaftar.", 'danger')
            return render_template('farmasi/obat_form.html', form=request.form, action='tambah')
            
        try:
            with transaction_scope() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO obat (kode_obat, nama_obat, kategori, satuan, harga_beli, harga_jual, 
                                           stok_saat_ini, stok_minimum, tanggal_kadaluwarsa, keterangan, status_aktif)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (kode_obat, nama_obat, kategori, satuan, harga_beli, harga_jual, 
                         stok_saat_ini, stok_minimum, tanggal_kadaluwarsa, keterangan, status_aktif)
                    )
                    obat_id = cursor.lastrowid
                    
                    # Jika ada stok awal > 0, catat mutasi masuk
                    if stok_saat_ini > 0:
                        cursor.execute(
                            """INSERT INTO obat_mutasi (obat_id, jenis_mutasi, jumlah, stok_sebelum, stok_sesudah, tanggal, no_referensi, keterangan)
                               VALUES (%s, 'Masuk', %s, 0, %s, CURDATE(), 'INIT-STOCK', 'Pencatatan stok awal obat')""",
                            (obat_id, stok_saat_ini, stok_saat_ini)
                        )
                        
            log_audit('Tambah Obat', 'Farmasi', f"Menambahkan obat {nama_obat} ({kode_obat}) stok awal {stok_saat_ini}")
            flash(f"Data obat {nama_obat} berhasil ditambahkan!", 'success')
            return redirect(url_for('farmasi.obat_index'))
        except Exception as e:
            flash(f"Gagal menambahkan obat: {str(e)}", 'danger')
            
    return render_template('farmasi/obat_form.html', action='tambah')

@farmasi_bp.route('/obat/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def obat_edit(id):
    obat = query_db("SELECT * FROM obat WHERE id = %s", (id,), one=True)
    if not obat:
        flash('Data obat tidak ditemukan.', 'danger')
        return redirect(url_for('farmasi.obat_index'))
        
    if request.method == 'POST':
        kode_obat = request.form.get('kode_obat', '').strip().upper()
        nama_obat = request.form.get('nama_obat', '').strip()
        kategori = request.form.get('kategori', '').strip()
        satuan = request.form.get('satuan', '').strip()
        harga_beli = request.form.get('harga_beli', '0').replace('.', '')
        harga_jual = request.form.get('harga_jual', '0').replace('.', '')
        stok_minimum = int(request.form.get('stok_minimum', 10))
        tanggal_kadaluwarsa = request.form.get('tanggal_kadaluwarsa')
        keterangan = request.form.get('keterangan', '').strip()
        status_aktif = request.form.get('status_aktif', 'Aktif')
        
        try:
            execute_db(
                """UPDATE obat SET kode_obat=%s, nama_obat=%s, kategori=%s, satuan=%s, 
                                  harga_beli=%s, harga_jual=%s, stok_minimum=%s, 
                                  tanggal_kadaluwarsa=%s, keterangan=%s, status_aktif=%s
                   WHERE id=%s""",
                (kode_obat, nama_obat, kategori, satuan, harga_beli, harga_jual, 
                 stok_minimum, tanggal_kadaluwarsa, keterangan, status_aktif, id)
            )
            log_audit('Edit Obat', 'Farmasi', f"Mengubah data obat {nama_obat} ({kode_obat})")
            flash(f"Data obat {nama_obat} berhasil diperbarui!", 'success')
            return redirect(url_for('farmasi.obat_index'))
        except Exception as e:
            flash(f"Gagal memperbarui data obat: {str(e)}", 'danger')
            
    return render_template('farmasi/obat_form.html', obat=obat, action='edit')

# -------------------------------------------------------------
# 2. MUTASI OBAT (MASUK & KELUAR)
# -------------------------------------------------------------
@farmasi_bp.route('/mutasi')
@login_required
def mutasi_index():
    tgl_mulai = request.args.get('tgl_mulai', '')
    tgl_selesai = request.args.get('tgl_selesai', '')
    jenis = request.args.get('jenis', '')
    
    query = """
        SELECT m.*, o.kode_obat, o.nama_obat, o.satuan
        FROM obat_mutasi m
        JOIN obat o ON m.obat_id = o.id
        WHERE 1=1
    """
    params = []
    if tgl_mulai:
        query += " AND m.tanggal >= %s"
        params.append(tgl_mulai)
    if tgl_selesai:
        query += " AND m.tanggal <= %s"
        params.append(tgl_selesai)
    if jenis:
        query += " AND m.jenis_mutasi = %s"
        params.append(jenis)
        
    query += " ORDER BY m.id DESC LIMIT 100"
    mutasi_list = query_db(query, tuple(params))
    
    return render_template('farmasi/mutasi_index.html', mutasi_list=mutasi_list, 
                           tgl_mulai=tgl_mulai, tgl_selesai=tgl_selesai, jenis=jenis)

@farmasi_bp.route('/mutasi/tambah', methods=['GET', 'POST'])
@login_required
def mutasi_tambah():
    obat_list = query_db("SELECT id, kode_obat, nama_obat, satuan, stok_saat_ini FROM obat WHERE status_aktif = 'Aktif' ORDER BY nama_obat ASC")
    
    if request.method == 'POST':
        obat_id = request.form.get('obat_id')
        jenis_mutasi = request.form.get('jenis_mutasi')
        jumlah = int(request.form.get('jumlah', 0))
        tanggal = request.form.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
        no_referensi = request.form.get('no_referensi', '').strip()
        keterangan = request.form.get('keterangan', '').strip()
        
        if not obat_id or not jenis_mutasi or jumlah <= 0:
            flash('Harap pilih obat, jenis mutasi, dan jumlah yang valid (> 0).', 'danger')
            return render_template('farmasi/mutasi_form.html', obat_list=obat_list)
            
        try:
            with transaction_scope() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM obat WHERE id = %s FOR UPDATE", (obat_id,))
                    obat = cursor.fetchone()
                    if not obat:
                        flash('Obat tidak ditemukan.', 'danger')
                        return redirect(url_for('farmasi.mutasi_index'))
                        
                    stok_sebelum = obat['stok_saat_ini']
                    
                    if jenis_mutasi == 'Masuk':
                        stok_sesudah = stok_sebelum + jumlah
                    else: # Keluar
                        if stok_sebelum < jumlah:
                            flash(f"Stok tidak mencukupi! Stok saat ini {stok_sebelum} {obat['satuan']}, pengurangan diminta {jumlah} {obat['satuan']}.", 'danger')
                            return render_template('farmasi/mutasi_form.html', obat_list=obat_list)
                        stok_sesudah = stok_sebelum - jumlah
                        
                    # Update stok obat
                    cursor.execute("UPDATE obat SET stok_saat_ini = %s WHERE id = %s", (stok_sesudah, obat_id))
                    
                    # Simpan riwayat mutasi
                    cursor.execute(
                        """INSERT INTO obat_mutasi (obat_id, jenis_mutasi, jumlah, stok_sebelum, stok_sesudah, tanggal, no_referensi, keterangan)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (obat_id, jenis_mutasi, jumlah, stok_sebelum, stok_sesudah, tanggal, no_referensi, keterangan)
                    )
                    
            log_audit('Mutasi Obat', 'Farmasi', f"Mutasi {jenis_mutasi} {jumlah} {obat['satuan']} untuk obat {obat['nama_obat']}")
            flash(f"Mutasi obat berhasil dicatat! Stok {obat['nama_obat']} kini {stok_sesudah} {obat['satuan']}.", 'success')
            return redirect(url_for('farmasi.mutasi_index'))
        except Exception as e:
            flash(f"Gagal mencatat mutasi obat: {str(e)}", 'danger')
            
    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template('farmasi/mutasi_form.html', obat_list=obat_list, today_str=today_str)

# -------------------------------------------------------------
# 3. RESEP DOKTER & PENYERAHAN OBAT
# -------------------------------------------------------------
@farmasi_bp.route('/resep')
@login_required
def resep_index():
    status = request.args.get('status', '')
    query = """
        SELECT r.*, pas.nama_lengkap as nama_pasien, pas.no_rm, 
               d.nama_dokter, rm.no_rekam_medis, rm.diagnosis
        FROM resep r
        JOIN pasien pas ON r.pasien_id = pas.id
        JOIN dokter d ON r.dokter_id = d.id
        JOIN rekam_medis rm ON r.rekam_medis_id = rm.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND r.status_resep = %s"
        params.append(status)
    query += " ORDER BY r.id DESC"
    
    resep_list = query_db(query, tuple(params))
    return render_template('farmasi/resep_index.html', resep_list=resep_list, selected_status=status)

@farmasi_bp.route('/resep/buat/<int:rekam_medis_id>', methods=['GET', 'POST'])
@login_required
def buat_resep(rekam_medis_id):
    rm = query_db("""
        SELECT rm.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.riwayat_alergi,
               d.nama_dokter, p.id as pendaftaran_id
        FROM rekam_medis rm
        JOIN pasien pas ON rm.pasien_id = pas.id
        JOIN dokter d ON rm.dokter_id = d.id
        JOIN pendaftaran p ON rm.pendaftaran_id = p.id
        WHERE rm.id = %s
    """, (rekam_medis_id,), one=True)
    
    if not rm:
        flash('Data pemeriksaan rekam medis tidak ditemukan.', 'danger')
        return redirect(url_for('rekam_medis.index'))
        
    existing_resep = query_db("SELECT id FROM resep WHERE rekam_medis_id = %s", (rekam_medis_id,), one=True)
    if existing_resep:
        return redirect(url_for('farmasi.resep_detail', id=existing_resep['id']))
        
    obat_list = query_db("SELECT id, kode_obat, nama_obat, satuan, harga_jual, stok_saat_ini FROM obat WHERE status_aktif = 'Aktif' ORDER BY nama_obat ASC")
    
    if request.method == 'POST':
        obat_ids = request.form.getlist('obat_ids[]')
        jumlah_list = request.form.getlist('jumlah[]')
        aturan_pakai_list = request.form.getlist('aturan_pakai[]')
        catatan = request.form.get('catatan', '').strip()
        
        if not obat_ids or len(obat_ids) == 0:
            flash('Harap tambahkan setidaknya satu item obat ke dalam resep.', 'danger')
            return render_template('farmasi/resep_form.html', rm=rm, obat_list=obat_list)
            
        no_resep = generate_no_resep()
        now_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with transaction_scope() as conn:
                with conn.cursor() as cursor:
                    # Simpan header resep
                    cursor.execute(
                        """INSERT INTO resep (no_resep, rekam_medis_id, pasien_id, dokter_id, tanggal_resep, status_resep, total_harga_obat, catatan)
                           VALUES (%s, %s, %s, %s, %s, 'Menunggu', 0, %s)""",
                        (no_resep, rekam_medis_id, rm['pasien_id'], rm['dokter_id'], now_date, catatan)
                    )
                    resep_id = cursor.lastrowid
                    
                    total_harga = 0.0
                    for i in range(len(obat_ids)):
                        oid = obat_ids[i]
                        jml = int(jumlah_list[i]) if (i < len(jumlah_list) and jumlah_list[i]) else 1
                        aturan = aturan_pakai_list[i] if i < len(aturan_pakai_list) else '-'
                        
                        cursor.execute("SELECT harga_jual FROM obat WHERE id = %s", (oid,))
                        o_row = cursor.fetchone()
                        if o_row:
                            harga = float(o_row['harga_jual'])
                            subtotal = harga * jml
                            total_harga += subtotal
                            cursor.execute(
                                """INSERT INTO detail_resep (resep_id, obat_id, jumlah, harga_satuan, subtotal, aturan_pakai)
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                (resep_id, oid, jml, harga, subtotal, aturan)
                            )
                            
                    # Update total di resep
                    cursor.execute("UPDATE resep SET total_harga_obat = %s WHERE id = %s", (total_harga, resep_id))
                    
                    # Sinkronkan biaya obat ke tagihan kasir
                    cursor.execute(
                        """UPDATE tagihan 
                           SET biaya_obat = %s,
                               total_tagihan = biaya_pendaftaran + biaya_konsultasi + biaya_tindakan + %s
                           WHERE pendaftaran_id = %s""",
                        (total_harga, total_harga, rm['pendaftaran_id'])
                    )
                    
            log_audit('Buat Resep Dokter', 'Farmasi', f"Membuat resep {no_resep} untuk pasien {rm['nama_pasien']}")
            flash(f"Resep obat {no_resep} berhasil dibuat!", 'success')
            return redirect(url_for('farmasi.resep_detail', id=resep_id))
        except Exception as e:
            flash(f"Gagal membuat resep: {str(e)}", 'danger')
            
    return render_template('farmasi/resep_form.html', rm=rm, obat_list=obat_list)

@farmasi_bp.route('/resep/<int:id>')
@login_required
def resep_detail(id):
    resep = query_db("""
        SELECT r.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.riwayat_alergi,
               d.nama_dokter, rm.no_rekam_medis, rm.diagnosis, p.no_pendaftaran, p.id as pendaftaran_id,
               t.id as tagihan_id, t.status_pembayaran
        FROM resep r
        JOIN pasien pas ON r.pasien_id = pas.id
        JOIN dokter d ON r.dokter_id = d.id
        JOIN rekam_medis rm ON r.rekam_medis_id = rm.id
        JOIN pendaftaran p ON rm.pendaftaran_id = p.id
        LEFT JOIN tagihan t ON p.id = t.pendaftaran_id
        WHERE r.id = %s
    """, (id,), one=True)
    
    if not resep:
        flash('Data resep tidak ditemukan.', 'danger')
        return redirect(url_for('farmasi.resep_index'))
        
    items = query_db("""
        SELECT dr.*, o.kode_obat, o.nama_obat, o.satuan, o.stok_saat_ini
        FROM detail_resep dr
        JOIN obat o ON dr.obat_id = o.id
        WHERE dr.resep_id = %s
    """, (id,))
    
    return render_template('farmasi/resep_detail.html', resep=resep, items=items)

@farmasi_bp.route('/resep/<int:id>/serahkan', methods=['POST'])
@login_required
def serahkan_resep(id):
    """Memvalidasi dan memproses penyerahan obat: memotong stok obat otomatis & catat mutasi."""
    resep = query_db("SELECT * FROM resep WHERE id = %s", (id,), one=True)
    if not resep:
        flash('Data resep tidak ditemukan.', 'danger')
        return redirect(url_for('farmasi.resep_index'))
        
    if resep['status_resep'] == 'Selesai':
        flash('Resep ini sudah berstatus Selesai dan obat telah diserahkan sebelumnya.', 'info')
        return redirect(url_for('farmasi.resep_detail', id=id))
        
    items = query_db("SELECT dr.*, o.nama_obat, o.satuan, o.stok_saat_ini FROM detail_resep dr JOIN obat o ON dr.obat_id = o.id WHERE dr.resep_id = %s", (id,))
    
    # 1. Pengecekan stok awal
    for it in items:
        if it['stok_saat_ini'] < it['jumlah']:
            flash(f"Stok obat {it['nama_obat']} tidak mencukupi! Dibutuhkan {it['jumlah']} {it['satuan']}, stok tersedia hanya {it['stok_saat_ini']} {it['satuan']}.", 'danger')
            return redirect(url_for('farmasi.resep_detail', id=id))
            
    try:
        with transaction_scope() as conn:
            with conn.cursor() as cursor:
                for it in items:
                    cursor.execute("SELECT stok_saat_ini FROM obat WHERE id = %s FOR UPDATE", (it['obat_id'],))
                    cur_stok = cursor.fetchone()['stok_saat_ini']
                    new_stok = cur_stok - it['jumlah']
                    
                    # Potong stok obat
                    cursor.execute("UPDATE obat SET stok_saat_ini = %s WHERE id = %s", (new_stok, it['obat_id']))
                    
                    # Catat mutasi keluar
                    cursor.execute(
                        """INSERT INTO obat_mutasi (obat_id, jenis_mutasi, jumlah, stok_sebelum, stok_sesudah, tanggal, no_referensi, keterangan)
                           VALUES (%s, 'Keluar', %s, %s, %s, CURDATE(), %s, %s)""",
                        (it['obat_id'], it['jumlah'], cur_stok, new_stok, resep['no_resep'], 'Penyerahan obat resep rawat jalan')
                    )
                    
                # Ubah status resep menjadi Selesai
                cursor.execute("UPDATE resep SET status_resep = 'Selesai' WHERE id = %s", (id,))
                
        log_audit('Penyerahan Obat Resep', 'Farmasi', f"Resep {resep['no_resep']} telah selesai dan diserahkan kepada pasien (Stok terpotong)")
        flash(f"Obat resep {resep['no_resep']} berhasil diserahkan dan stok obat telah terpotong secara otomatis!", 'success')
    except Exception as e:
        flash(f"Gagal memproses penyerahan obat: {str(e)}", 'danger')
        
    return redirect(url_for('farmasi.resep_detail', id=id))
