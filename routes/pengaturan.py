import os
import io
import subprocess
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, Response
from werkzeug.security import check_password_hash, generate_password_hash
from database import query_db, execute_db, get_db
from helpers import login_required, log_audit, get_hospital_profile
from config import Config

pengaturan_bp = Blueprint('pengaturan', __name__, url_prefix='/pengaturan')

@pengaturan_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    hosp = get_hospital_profile()
    user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        
        # 1. Update Profil RS
        if action_type == 'profil_rs':
            nama_rs = request.form.get('nama_rs', '').strip()
            alamat = request.form.get('alamat', '').strip()
            kota = request.form.get('kota', '').strip()
            provinsi = request.form.get('provinsi', '').strip()
            no_telepon = request.form.get('no_telepon', '').strip()
            email = request.form.get('email', '').strip()
            website = request.form.get('website', '').strip()
            motto = request.form.get('motto', '').strip()
            biaya_daftar = request.form.get('biaya_pendaftaran_default', '25000').replace('.', '')
            catatan_struk = request.form.get('catatan_struk', '').strip()
            
            try:
                execute_db(
                    """UPDATE pengaturan_rs 
                       SET nama_rs=%s, alamat=%s, kota=%s, provinsi=%s, no_telepon=%s, 
                           email=%s, website=%s, motto=%s, biaya_pendaftaran_default=%s, catatan_struk=%s
                       WHERE id=%s""",
                    (nama_rs, alamat, kota, provinsi, no_telepon, email, website, motto, biaya_daftar, catatan_struk, hosp['id'])
                )
                log_audit('Update Profil RS', 'Pengaturan', f"Memperbarui profil rumah sakit {nama_rs}")
                flash('Profil rumah sakit berhasil diperbarui!', 'success')
                return redirect(url_for('pengaturan.index'))
            except Exception as e:
                flash(f"Gagal memperbarui profil RS: {str(e)}", 'danger')
                
        # 2. Update Akun Admin
        elif action_type == 'akun_admin':
            nama_lengkap = request.form.get('nama_lengkap', '').strip()
            email = request.form.get('email', '').strip()
            no_telepon = request.form.get('no_telepon', '').strip()
            
            try:
                execute_db(
                    "UPDATE users SET nama_lengkap=%s, email=%s, no_telepon=%s WHERE id=%s",
                    (nama_lengkap, email, no_telepon, user['id'])
                )
                session['nama_lengkap'] = nama_lengkap
                session['email'] = email
                log_audit('Update Akun Admin', 'Pengaturan', f"Mengubah data profil admin {nama_lengkap}")
                flash('Informasi akun Admin berhasil diperbarui!', 'success')
                return redirect(url_for('pengaturan.index'))
            except Exception as e:
                flash(f"Gagal memperbarui profil admin: {str(e)}", 'danger')
                
        # 3. Ganti Password
        elif action_type == 'ganti_password':
            pass_lama = request.form.get('password_lama', '')
            pass_baru = request.form.get('password_baru', '')
            pass_konfirmasi = request.form.get('password_konfirmasi', '')
            
            if not check_password_hash(user['password_hash'], pass_lama):
                flash('Password saat ini (lama) tidak sesuai!', 'danger')
                return redirect(url_for('pengaturan.index'))
                
            if len(pass_baru) < 6:
                flash('Password baru minimal harus 6 karakter.', 'danger')
                return redirect(url_for('pengaturan.index'))
                
            if pass_baru != pass_konfirmasi:
                flash('Konfirmasi password baru tidak cocok.', 'danger')
                return redirect(url_for('pengaturan.index'))
                
            try:
                hash_baru = generate_password_hash(pass_baru)
                execute_db("UPDATE users SET password_hash=%s WHERE id=%s", (hash_baru, user['id']))
                log_audit('Ganti Password', 'Pengaturan', "Admin berhasil memperbarui password login.")
                flash('Password akun Admin berhasil diganti! Gunakan password baru untuk login berikutnya.', 'success')
                return redirect(url_for('pengaturan.index'))
            except Exception as e:
                flash(f"Gagal mengganti password: {str(e)}", 'danger')
                
    return render_template('pengaturan/index.html', hosp=hosp, user=user)

@pengaturan_bp.route('/log')
@login_required
def log_view():
    modul = request.args.get('modul', '')
    tgl = request.args.get('tanggal', '')
    
    query = "SELECT * FROM log_aktivitas WHERE 1=1"
    params = []
    if modul:
        query += " AND modul = %s"
        params.append(modul)
    if tgl:
        query += " AND DATE(created_at) = %s"
        params.append(tgl)
        
    query += " ORDER BY id DESC LIMIT 200"
    logs = query_db(query, tuple(params))
    
    modul_list = query_db("SELECT DISTINCT modul FROM log_aktivitas ORDER BY modul ASC")
    
    return render_template('pengaturan/log.html', logs=logs, modul_list=modul_list, selected_modul=modul, selected_tgl=tgl)

@pengaturan_bp.route('/backup')
@login_required
def backup_database():
    """Menghasilkan dump SQL dari seluruh tabel dan data sistem rumah sakit."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Ambil semua nama tabel
        cursor.execute("SHOW TABLES")
        tables = [row[f"Tables_in_{Config.MYSQL_DB}"] for row in cursor.fetchall()]
        
        buffer = io.StringIO()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        buffer.write(f"-- ==========================================================\n")
        buffer.write(f"-- CADANGAN DATABASE SISTEM INFORMASI RUMAH SAKIT (SIMRS)\n")
        buffer.write(f"-- Database: {Config.MYSQL_DB}\n")
        buffer.write(f"-- Tanggal Backup: {timestamp}\n")
        buffer.write(f"-- Oleh User: {session.get('username', 'Admin')}\n")
        buffer.write(f"-- ==========================================================\n\n")
        buffer.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        
        for table in tables:
            # CREATE TABLE statement
            cursor.execute(f"SHOW CREATE TABLE `{table}`")
            create_table = cursor.fetchone()['Create Table']
            buffer.write(f"DROP TABLE IF EXISTS `{table}`;\n")
            buffer.write(f"{create_table};\n\n")
            
            # INSERT DATA
            cursor.execute(f"SELECT * FROM `{table}`")
            rows = cursor.fetchall()
            if rows:
                cols = list(rows[0].keys())
                col_names = ", ".join([f"`{c}`" for c in cols])
                
                for r in rows:
                    val_strs = []
                    for c in cols:
                        val = r[c]
                        if val is None:
                            val_strs.append("NULL")
                        elif isinstance(val, (int, float)):
                            val_strs.append(str(val))
                        else:
                            # escape single quotes
                            escaped = str(val).replace("\\", "\\\\").replace("'", "\\'")
                            val_strs.append(f"'{escaped}'")
                    buffer.write(f"INSERT INTO `{table}` ({col_names}) VALUES ({', '.join(val_strs)});\n")
                buffer.write("\n")
                
        buffer.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        conn.close()
        
        log_audit('Backup Database', 'Pengaturan', f"Admin melakukan ekspor cadangan database {Config.MYSQL_DB}")
        
        mem = io.BytesIO()
        mem.write(buffer.getvalue().encode('utf-8'))
        mem.seek(0)
        
        filename = f"backup_{Config.MYSQL_DB}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        return send_file(mem, as_attachment=True, download_name=filename, mimetype='application/sql')
    except Exception as e:
        flash(f"Gagal melakukan backup database: {str(e)}", 'danger')
        return redirect(url_for('pengaturan.index'))
