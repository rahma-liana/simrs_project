import sys
from app import create_app
from database import query_db

def run_tests():
    print("=== PENGUJIAN INTEGRASI SIMRS ===")
    
    # 1. Test Database Connectivity
    try:
        user = query_db("SELECT username, email, role FROM users LIMIT 1", one=True)
        print(f"[OK] Database MySQL Terhubung! User: {user['username']} ({user['role']})")
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke MySQL: {e}")
        return False
        
    # 2. Test Flask Client & Routes
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test Login Page
    res = client.get('/login')
    assert res.status_code == 200, f"Login status code: {res.status_code}"
    assert b"SIMRS" in res.data, "Login page content mismatch"
    print("[OK] Halaman Login (200 OK)")
    
    # Test Unauthorized Access to Dashboard (Should redirect to /login)
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 302, f"Expected 302 redirect for unauthorized access, got {res_dash.status_code}"
    print("[OK] Proteksi Akses Tamu Terverifikasi (Redirect ke /login)")
    
    # Test Login Process
    res_post = client.post('/login', data={
        'username_or_email': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"Dashboard Utama" in res_post.data or b"Dashboard" in res_post.data
    print("[OK] Login Administrator Berhasil dengan password hash scrypt!")
    
    # Test All Main Endpoints as Admin
    routes_to_test = [
        ('/dashboard', "Dashboard"),
        ('/pasien/', "Pasien"),
        ('/pasien/tambah', "Tambah Pasien"),
        ('/dokter/', "Dokter"),
        ('/poli/', "Poliklinik"),
        ('/jadwal/', "Jadwal"),
        ('/tindakan/', "Tindakan"),
        ('/pendaftaran/', "Pendaftaran"),
        ('/rekam-medis/', "Rekam Medis"),
        ('/farmasi/obat', "Farmasi"),
        ('/farmasi/mutasi', "Mutasi"),
        ('/farmasi/resep', "Resep"),
        ('/kasir/', "Kasir"),
        ('/laporan/', "Laporan"),
        ('/laporan/pasien', "Laporan Pasien"),
        ('/laporan/kunjungan', "Laporan Kunjungan"),
        ('/laporan/farmasi?tipe=stok', "Laporan Stok"),
        ('/laporan/pendapatan', "Laporan Pendapatan"),
        ('/pengaturan/', "Pengaturan"),
        ('/pengaturan/log', "Log Aktivitas")
    ]
    
    for route, label in routes_to_test:
        r = client.get(route)
        assert r.status_code == 200, f"Route {route} failed with status {r.status_code}"
        print(f"  [OK] Rute {route} ({label}) -> 200 OK")
        
    print("\n=== SEMUA PENGUJIAN INTEGRASI BERHASIL 100%! ===")
    return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
