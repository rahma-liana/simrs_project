from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database import query_db, execute_db, transaction_scope
from helpers import login_required, log_audit, generate_no_pembayaran, get_hospital_profile

kasir_bp = Blueprint('kasir', __name__, url_prefix='/kasir')

@kasir_bp.route('/')
@login_required
def index():
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    tgl = request.args.get('tanggal', '')
    
    query = """
        SELECT t.*, pas.nama_lengkap as nama_pasien, pas.no_rm, 
               p.no_pendaftaran, p.no_antrean, pol.nama_poli, d.nama_dokter,
               COALESCE(SUM(pem.jumlah_bayar), 0) as total_dibayar
        FROM tagihan t
        JOIN pendaftaran p ON t.pendaftaran_id = p.id
        JOIN pasien pas ON t.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        LEFT JOIN pembayaran pem ON t.id = pem.tagihan_id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND t.status_pembayaran = %s"
        params.append(status)
    if tgl:
        query += " AND t.tanggal_tagihan = %s"
        params.append(tgl)
    if search:
        query += " AND (pas.nama_lengkap LIKE %s OR pas.no_rm LIKE %s OR t.no_tagihan LIKE %s)"
        s = f"%{search}%"
        params.extend([s, s, s])
        
    query += " GROUP BY t.id ORDER BY t.id DESC"
    tagihan_list = query_db(query, tuple(params))
    
    return render_template('kasir/index.html', tagihan_list=tagihan_list, selected_status=status, 
                           selected_tanggal=tgl, search=search)

@kasir_bp.route('/tagihan/<int:id>/bayar', methods=['GET', 'POST'])
@login_required
def bayar(id):
    tagihan = query_db("""
        SELECT t.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.alamat, pas.no_telepon,
               p.no_pendaftaran, p.no_antrean, pol.nama_poli, d.nama_dokter
        FROM tagihan t
        JOIN pendaftaran p ON t.pendaftaran_id = p.id
        JOIN pasien pas ON t.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        WHERE t.id = %s
    """, (id,), one=True)
    
    if not tagihan:
        flash('Data tagihan tidak ditemukan.', 'danger')
        return redirect(url_for('kasir.index'))
        
    # Ambil riwayat pembayaran tagihan ini
    riwayat_bayar = query_db("SELECT * FROM pembayaran WHERE tagihan_id = %s ORDER BY id ASC", (id,))
    total_sudah_bayar = sum(float(b['jumlah_bayar']) for b in riwayat_bayar)
    sisa_tagihan = float(tagihan['total_tagihan']) - total_sudah_bayar
    if sisa_tagihan < 0:
        sisa_tagihan = 0.0
        
    # Detail tindakan dan resep untuk rincian
    rm = query_db("SELECT id, no_rekam_medis FROM rekam_medis WHERE pendaftaran_id = %s", (tagihan['pendaftaran_id'],), one=True)
    tindakan_items = []
    resep_items = []
    if rm:
        tindakan_items = query_db("""
            SELECT rmt.*, tm.nama_tindakan 
            FROM rekam_medis_tindakan rmt 
            JOIN tindakan_medis tm ON rmt.tindakan_id = tm.id 
            WHERE rmt.rekam_medis_id = %s
        """, (rm['id'],))
        
        resep = query_db("SELECT id FROM resep WHERE rekam_medis_id = %s", (rm['id'],), one=True)
        if resep:
            resep_items = query_db("""
                SELECT dr.*, o.nama_obat, o.satuan 
                FROM detail_resep dr 
                JOIN obat o ON dr.obat_id = o.id 
                WHERE dr.resep_id = %s
            """, (resep['id'],))
            
    if request.method == 'POST':
        if tagihan['status_pembayaran'] == 'Lunas':
            flash('Tagihan ini sudah berstatus Lunas dan tidak memerlukan pembayaran lagi.', 'warning')
            return redirect(url_for('kasir.bayar', id=id))
            
        jumlah_bayar = float(request.form.get('jumlah_bayar', 0).replace('.', ''))
        metode_pembayaran = request.form.get('metode_pembayaran', 'Tunai')
        no_referensi = request.form.get('no_referensi', '').strip()
        keterangan = request.form.get('keterangan', '').strip()
        
        if jumlah_bayar <= 0:
            flash('Jumlah pembayaran harus lebih besar dari 0.', 'danger')
            return render_template('kasir/form.html', tagihan=tagihan, riwayat_bayar=riwayat_bayar,
                                   total_sudah_bayar=total_sudah_bayar, sisa_tagihan=sisa_tagihan,
                                   tindakan_items=tindakan_items, resep_items=resep_items)
                                   
        no_pembayaran = generate_no_pembayaran()
        
        try:
            with transaction_scope() as conn:
                with conn.cursor() as cursor:
                    # 1. Simpan transaksi pembayaran
                    cursor.execute(
                        """INSERT INTO pembayaran (no_pembayaran, tagihan_id, tanggal_bayar, jumlah_bayar, 
                                                 metode_pembayaran, no_referensi, keterangan, kasir_nama)
                           VALUES (%s, %s, NOW(), %s, %s, %s, %s, 'Admin')""",
                        (no_pembayaran, id, jumlah_bayar, metode_pembayaran, no_referensi, keterangan)
                    )
                    pay_id = cursor.lastrowid
                    
                    # 2. Update status tagihan (Lunas / Sebagian)
                    akumulasi_bayar = total_sudah_bayar + jumlah_bayar
                    status_baru = 'Lunas' if akumulasi_bayar >= float(tagihan['total_tagihan']) else 'Sebagian'
                    
                    cursor.execute("UPDATE tagihan SET status_pembayaran = %s WHERE id = %s", (status_baru, id))
                    
            log_audit('Terima Pembayaran', 'Kasir', f"Menerima pembayaran {no_pembayaran} sebesar Rp {jumlah_bayar:,.0f} untuk tagihan {tagihan['no_tagihan']} ({status_baru})")
            flash(f"Pembayaran berhasil dicatat dengan No. Kuitansi {no_pembayaran}! Status tagihan kini: {status_baru}.", 'success')
            return redirect(url_for('kasir.cetak_struk', tagihan_id=id, pembayaran_id=pay_id))
        except Exception as e:
            flash(f"Gagal memproses pembayaran: {str(e)}", 'danger')
            
    return render_template(
        'kasir/form.html',
        tagihan=tagihan,
        riwayat_bayar=riwayat_bayar,
        total_sudah_bayar=total_sudah_bayar,
        sisa_tagihan=sisa_tagihan,
        tindakan_items=tindakan_items,
        resep_items=resep_items
    )

@kasir_bp.route('/tagihan/<int:tagihan_id>/struk')
@login_required
def cetak_struk(tagihan_id):
    pembayaran_id = request.args.get('pembayaran_id')
    
    tagihan = query_db("""
        SELECT t.*, pas.nama_lengkap as nama_pasien, pas.no_rm, pas.alamat, pas.no_telepon,
               p.no_pendaftaran, p.no_antrean, p.tanggal_kunjungan,
               pol.nama_poli, d.nama_dokter
        FROM tagihan t
        JOIN pendaftaran p ON t.pendaftaran_id = p.id
        JOIN pasien pas ON t.pasien_id = pas.id
        JOIN dokter d ON p.dokter_id = d.id
        JOIN poli pol ON p.poli_id = pol.id
        WHERE t.id = %s
    """, (tagihan_id,), one=True)
    
    if not tagihan:
        flash('Data tagihan tidak ditemukan.', 'danger')
        return redirect(url_for('kasir.index'))
        
    pembayaran = None
    if pembayaran_id:
        pembayaran = query_db("SELECT * FROM pembayaran WHERE id = %s", (pembayaran_id,), one=True)
    if not pembayaran:
        pembayaran = query_db("SELECT * FROM pembayaran WHERE tagihan_id = %s ORDER BY id DESC LIMIT 1", (tagihan_id,), one=True)
        
    # Detail tindakan & obat
    rm = query_db("SELECT id FROM rekam_medis WHERE pendaftaran_id = %s", (tagihan['pendaftaran_id'],), one=True)
    tindakan_items = []
    resep_items = []
    if rm:
        tindakan_items = query_db("""
            SELECT rmt.*, tm.nama_tindakan 
            FROM rekam_medis_tindakan rmt 
            JOIN tindakan_medis tm ON rmt.tindakan_id = tm.id 
            WHERE rmt.rekam_medis_id = %s
        """, (rm['id'],))
        
        resep = query_db("SELECT id FROM resep WHERE rekam_medis_id = %s", (rm['id'],), one=True)
        if resep:
            resep_items = query_db("""
                SELECT dr.*, o.nama_obat, o.satuan 
                FROM detail_resep dr 
                JOIN obat o ON dr.obat_id = o.id 
                WHERE dr.resep_id = %s
            """, (resep['id'],))
            
    hosp = get_hospital_profile()
    
    return render_template(
        'kasir/struk.html',
        tagihan=tagihan,
        pembayaran=pembayaran,
        tindakan_items=tindakan_items,
        resep_items=resep_items,
        hosp=hosp
    )
