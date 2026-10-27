from flask import Blueprint, render_template, jsonify
from database import query_db
from helpers import login_required
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # 1. Total statistik master
    total_pasien = query_db("SELECT COUNT(*) as c FROM pasien", one=True)['c']
    total_dokter = query_db("SELECT COUNT(*) as c FROM dokter WHERE status_aktif = 'Aktif'", one=True)['c']
    total_poli = query_db("SELECT COUNT(*) as c FROM poli WHERE status_aktif = 'Aktif'", one=True)['c']
    
    # 2. Statistik Kunjungan Hari Ini
    kunjungan_hari_ini = query_db(
        "SELECT COUNT(*) as c FROM pendaftaran WHERE tanggal_kunjungan = CURDATE()",
        one=True
    )['c']
    
    # 3. Antrean aktif hari ini (Menunggu / Dipanggil / Sedang Diperiksa)
    antrean_aktif = query_db(
        """SELECT COUNT(*) as c FROM pendaftaran 
           WHERE tanggal_kunjungan = CURDATE() 
           AND status_antrean IN ('Menunggu', 'Dipanggil', 'Sedang Diperiksa')""",
        one=True
    )['c']
    
    # 4. Transaksi & Pendapatan Kasir
    total_transaksi = query_db("SELECT COUNT(*) as c FROM pembayaran", one=True)['c']
    
    pendapatan_total_row = query_db("SELECT COALESCE(SUM(jumlah_bayar), 0) as s FROM pembayaran", one=True)
    pendapatan_total = pendapatan_total_row['s'] if pendapatan_total_row else 0
    
    pendapatan_bulan_row = query_db(
        """SELECT COALESCE(SUM(jumlah_bayar), 0) as s FROM pembayaran 
           WHERE MONTH(tanggal_bayar) = MONTH(CURDATE()) AND YEAR(tanggal_bayar) = YEAR(CURDATE())""",
        one=True
    )
    pendapatan_bulan_ini = pendapatan_bulan_row['s'] if pendapatan_bulan_row else 0

    # 5. Obat Stok Menipis
    obat_menipis_count = query_db(
        "SELECT COUNT(*) as c FROM obat WHERE stok_saat_ini <= stok_minimum AND status_aktif = 'Aktif'",
        one=True
    )['c']
    
    daftar_obat_menipis = query_db(
        """SELECT * FROM obat 
           WHERE stok_saat_ini <= stok_minimum AND status_aktif = 'Aktif' 
           ORDER BY (stok_saat_ini - stok_minimum) ASC LIMIT 5"""
    )
    
    # 6. Antrean Hari Ini
    antrean_hari_ini = query_db(
        """SELECT p.*, pas.nama_lengkap as nama_pasien, pas.no_rm, 
                  d.nama_dokter, pol.nama_poli 
           FROM pendaftaran p
           JOIN pasien pas ON p.pasien_id = pas.id
           JOIN dokter d ON p.dokter_id = d.id
           JOIN poli pol ON p.poli_id = pol.id
           WHERE p.tanggal_kunjungan = CURDATE()
           ORDER BY 
              CASE p.status_antrean
                  WHEN 'Sedang Diperiksa' THEN 1
                  WHEN 'Dipanggil' THEN 2
                  WHEN 'Menunggu' THEN 3
                  WHEN 'Selesai' THEN 4
                  ELSE 5
              END, p.id ASC
           LIMIT 10"""
    )
    
    # 7. Data Grafik Trend Kunjungan 7 Hari Terakhir
    trend_kunjungan = query_db(
        """SELECT tanggal_kunjungan, COUNT(*) as jumlah 
           FROM pendaftaran 
           WHERE tanggal_kunjungan >= CURDATE() - INTERVAL 6 DAY 
           GROUP BY tanggal_kunjungan 
           ORDER BY tanggal_kunjungan ASC"""
    )
    
    chart_dates = []
    chart_visits = []
    trend_dict = {str(item['tanggal_kunjungan']): item['jumlah'] for item in trend_kunjungan}
    
    for i in range(6, -1, -1):
        dt = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        chart_dates.append(dt)
        chart_visits.append(trend_dict.get(dt, 0))
        
    # 8. Data Distribusi Pasien per Poli (Bulan Ini)
    distribusi_poli = query_db(
        """SELECT pol.nama_poli, COUNT(p.id) as total 
           FROM poli pol
           LEFT JOIN pendaftaran p ON pol.id = p.poli_id 
                AND MONTH(p.tanggal_kunjungan) = MONTH(CURDATE())
                AND YEAR(p.tanggal_kunjungan) = YEAR(CURDATE())
           WHERE pol.status_aktif = 'Aktif'
           GROUP BY pol.id, pol.nama_poli
           ORDER BY total DESC"""
    )
    
    # 9. Transaksi Terakhir
    transaksi_terbaru = query_db(
        """SELECT pem.*, t.no_tagihan, pas.nama_lengkap as nama_pasien, pas.no_rm
           FROM pembayaran pem
           JOIN tagihan t ON pem.tagihan_id = t.id
           JOIN pasien pas ON t.pasien_id = pas.id
           ORDER BY pem.id DESC LIMIT 5"""
    )

    stats = {
        'total_pasien': total_pasien,
        'total_dokter': total_dokter,
        'total_poli': total_poli,
        'kunjungan_hari_ini': kunjungan_hari_ini,
        'antrean_aktif': antrean_aktif,
        'total_transaksi': total_transaksi,
        'pendapatan_total': pendapatan_total,
        'pendapatan_bulan_ini': pendapatan_bulan_ini,
        'obat_menipis_count': obat_menipis_count
    }

    return render_template(
        'dashboard/index.html',
        stats=stats,
        daftar_obat_menipis=daftar_obat_menipis,
        antrean_hari_ini=antrean_hari_ini,
        transaksi_terbaru=transaksi_terbaru,
        chart_dates=chart_dates,
        chart_visits=chart_visits,
        distribusi_poli=distribusi_poli
    )
