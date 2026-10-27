import functools
from datetime import datetime, date
from flask import session, redirect, url_for, flash, request
from database import query_db, execute_db

INDONESIAN_MONTHS = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}

INDONESIAN_DAYS = {
    0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis',
    4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'
}

def login_required(view):
    """Decorator untuk membatasi akses hanya untuk pengguna (Admin) yang sudah login."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view

def format_rupiah(value):
    """Format angka menjadi format Rupiah Indonesia, misal: Rp 150.000"""
    try:
        val = float(value or 0)
        formatted = f"{val:,.0f}".replace(',', '.')
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return "Rp 0"

def format_tanggal_indo(val):
    """Format tanggal ke Bahasa Indonesia (misal: 20 Oktober 2026)."""
    if not val:
        return "-"
    if isinstance(val, str):
        try:
            val = datetime.strptime(val[:10], '%Y-%m-%d').date()
        except Exception:
            return val
    elif isinstance(val, datetime):
        val = val.date()
    
    if isinstance(val, date):
        return f"{val.day} {INDONESIAN_MONTHS.get(val.month, '')} {val.year}"
    return str(val)

def format_datetime_indo(val):
    """Format tanggal dan waktu ke Bahasa Indonesia."""
    if not val:
        return "-"
    if isinstance(val, str):
        try:
            val = datetime.strptime(val[:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            return val
    if isinstance(val, datetime):
        tgl = f"{val.day} {INDONESIAN_MONTHS.get(val.month, '')} {val.year}"
        jam = val.strftime('%H:%M:%S')
        return f"{tgl} {jam}"
    return str(val)

def get_hospital_profile():
    """Mengambil profil dan informasi rumah sakit dari database."""
    res = query_db("SELECT * FROM pengaturan_rs LIMIT 1", one=True)
    if not res:
        return {
            'nama_rs': 'RS Medika Sehat Sentosa',
            'alamat': 'Jl. Kesehatan Raya No. 45',
            'kota': 'Jakarta Pusat',
            'provinsi': 'DKI Jakarta',
            'no_telepon': '(021) 3901234',
            'email': 'kontak@rsmedikasehat.co.id',
            'website': 'www.rsmedikasehat.co.id',
            'motto': 'Melayani dengan Sepenuh Hati',
            'biaya_pendaftaran_default': 25000.00,
            'catatan_struk': 'Semoga Lekas Sembuh!'
        }
    return res

def log_audit(aktivitas, modul, detail=""):
    """Mencatat aktivitas Admin ke dalam tabel log_aktivitas."""
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'Sistem')
        ip_address = request.remote_addr if request else '127.0.0.1'
        execute_db(
            "INSERT INTO log_aktivitas (user_id, username, aktivitas, modul, detail, ip_address) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, username, aktivitas, modul, str(detail), ip_address)
        )
    except Exception as e:
        print(f"Gagal mencatat log aktivitas: {e}")

def generate_no_rm():
    """Menghasilkan Nomor Rekam Medis unik berurutan: RM-YYYYMM-XXXX"""
    now = datetime.now()
    prefix = f"RM-{now.strftime('%Y%m')}-"
    row = query_db(
        "SELECT no_rm FROM pasien WHERE no_rm LIKE %s ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",),
        one=True
    )
    if row and row.get('no_rm'):
        last_seq = int(row['no_rm'].split('-')[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}"

def generate_no_antrean(poli_id, tanggal_str=None):
    """Menghasilkan nomor antrean poli harian otomatis (misal: U-001, G-002)."""
    if not tanggal_str:
        tanggal_str = datetime.now().strftime('%Y-%m-%d')
    
    poli = query_db("SELECT kode_poli FROM poli WHERE id = %s", (poli_id,), one=True)
    if poli and poli.get('kode_poli'):
        # Ambil inisial setelah 'POL-' atau huruf pertama
        code = poli['kode_poli'].replace('POL-', '')
        prefix = code[0].upper()
    else:
        prefix = "A"

    row = query_db(
        """SELECT COUNT(*) as total FROM pendaftaran 
           WHERE poli_id = %s AND tanggal_kunjungan = %s""",
        (poli_id, tanggal_str),
        one=True
    )
    next_num = (row['total'] if row else 0) + 1
    return f"{prefix}-{next_num:03d}"

def generate_no_pendaftaran():
    """Menghasilkan Nomor Pendaftaran unik: REG-YYYYMMDD-XXXX"""
    now = datetime.now()
    prefix = f"REG-{now.strftime('%Y%m%d')}-"
    row = query_db("SELECT no_pendaftaran FROM pendaftaran WHERE no_pendaftaran LIKE %s ORDER BY id DESC LIMIT 1", (f"{prefix}%",), one=True)
    seq = int(row['no_pendaftaran'].split('-')[-1]) + 1 if row else 1
    return f"{prefix}{seq:04d}"

def generate_no_rekam_medis():
    """Menghasilkan No Rekam Medis Pemeriksaan: RMED-YYYYMMDD-XXXX"""
    now = datetime.now()
    prefix = f"RMED-{now.strftime('%Y%m%d')}-"
    row = query_db("SELECT no_rekam_medis FROM rekam_medis WHERE no_rekam_medis LIKE %s ORDER BY id DESC LIMIT 1", (f"{prefix}%",), one=True)
    seq = int(row['no_rekam_medis'].split('-')[-1]) + 1 if row else 1
    return f"{prefix}{seq:04d}"

def generate_no_resep():
    """Menghasilkan Nomor Resep Obat: RSP-YYYYMMDD-XXXX"""
    now = datetime.now()
    prefix = f"RSP-{now.strftime('%Y%m%d')}-"
    row = query_db("SELECT no_resep FROM resep WHERE no_resep LIKE %s ORDER BY id DESC LIMIT 1", (f"{prefix}%",), one=True)
    seq = int(row['no_resep'].split('-')[-1]) + 1 if row else 1
    return f"{prefix}{seq:04d}"

def generate_no_tagihan():
    """Menghasilkan Nomor Tagihan / Invoice Kasir: INV-YYYYMMDD-XXXX"""
    now = datetime.now()
    prefix = f"INV-{now.strftime('%Y%m%d')}-"
    row = query_db("SELECT no_tagihan FROM tagihan WHERE no_tagihan LIKE %s ORDER BY id DESC LIMIT 1", (f"{prefix}%",), one=True)
    seq = int(row['no_tagihan'].split('-')[-1]) + 1 if row else 1
    return f"{prefix}{seq:04d}"

def generate_no_pembayaran():
    """Menghasilkan Nomor Kuitansi Pembayaran: PAY-YYYYMMDD-XXXX"""
    now = datetime.now()
    prefix = f"PAY-{now.strftime('%Y%m%d')}-"
    row = query_db("SELECT no_pembayaran FROM pembayaran WHERE no_pembayaran LIKE %s ORDER BY id DESC LIMIT 1", (f"{prefix}%",), one=True)
    seq = int(row['no_pembayaran'].split('-')[-1]) + 1 if row else 1
    return f"{prefix}{seq:04d}"
