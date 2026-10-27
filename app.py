import os
from flask import Flask, render_template, session
from config import Config
from helpers import format_rupiah, format_tanggal_indo, format_datetime_indo, get_hospital_profile
from database import query_db

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.pasien import pasien_bp
from routes.dokter import dokter_bp
from routes.poli import poli_bp
from routes.jadwal import jadwal_bp
from routes.pendaftaran import pendaftaran_bp
from routes.rekam_medis import rekam_medis_bp
from routes.tindakan import tindakan_bp
from routes.farmasi import farmasi_bp
from routes.kasir import kasir_bp
from routes.laporan import laporan_bp
from routes.pengaturan import pengaturan_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Custom Template Filters
    app.jinja_env.filters['rupiah'] = format_rupiah
    app.jinja_env.filters['tanggal_indo'] = format_tanggal_indo
    app.jinja_env.filters['datetime_indo'] = format_datetime_indo

    # Global Context Processor untuk Navbar & Header
    @app.context_processor
    def inject_global_data():
        if 'user_id' in session:
            hosp = get_hospital_profile()
            
            # Notifikasi stok obat menipis
            obat_alert = query_db(
                "SELECT COUNT(*) as c FROM obat WHERE stok_saat_ini <= stok_minimum AND status_aktif = 'Aktif'",
                one=True
            )
            total_obat_menipis = obat_alert['c'] if obat_alert else 0
            
            # Notifikasi antrean menunggu hari ini
            antrean_alert = query_db(
                "SELECT COUNT(*) as c FROM pendaftaran WHERE tanggal_kunjungan = CURDATE() AND status_antrean = 'Menunggu'",
                one=True
            )
            total_antrean_menunggu = antrean_alert['c'] if antrean_alert else 0
            
            return {
                'hosp': hosp,
                'total_obat_menipis': total_obat_menipis,
                'total_antrean_menunggu': total_antrean_menunggu,
                'admin_user': {
                    'username': session.get('username'),
                    'nama_lengkap': session.get('nama_lengkap'),
                    'role': session.get('role', 'Admin')
                }
            }
        return {'hosp': get_hospital_profile()}

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pasien_bp)
    app.register_blueprint(dokter_bp)
    app.register_blueprint(poli_bp)
    app.register_blueprint(jadwal_bp)
    app.register_blueprint(pendaftaran_bp)
    app.register_blueprint(rekam_medis_bp)
    app.register_blueprint(tindakan_bp)
    app.register_blueprint(farmasi_bp)
    app.register_blueprint(kasir_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(pengaturan_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', error=e), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = Config.PORT
    debug = Config.DEBUG
    print(f"============================================================")
    print(f" SISTEM INFORMASI RUMAH SAKIT (SIMRS) TERINTEGRASI")
    print(f" Akses Website: http://127.0.0.1:{port}")
    print(f" Login Admin: username=admin / password=admin123")
    print(f"============================================================")
    app.run(host='0.0.0.0', port=port, debug=debug)
