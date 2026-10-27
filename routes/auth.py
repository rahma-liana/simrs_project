from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import query_db, execute_db
from helpers import log_audit, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        identifier = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        
        if not identifier or not password:
            flash('Harap isi username/email dan password.', 'danger')
            return render_template('auth/login.html')
            
        user = query_db(
            "SELECT * FROM users WHERE (username = %s OR email = %s) LIMIT 1",
            (identifier, identifier),
            one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            # Simpan sesi login
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nama_lengkap'] = user['nama_lengkap']
            session['role'] = user['role']
            session['email'] = user['email']
            
            # Update waktu terakhir login
            execute_db("UPDATE users SET terakhir_login = NOW() WHERE id = %s", (user['id'],))
            log_audit('Login Sistem', 'Autentikasi', f"Admin {user['username']} berhasil login ke sistem.")
            
            flash(f"Selamat datang kembali, {user['nama_lengkap']}!", 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard.index'))
        else:
            flash('Username/email atau password salah. Silakan coba lagi.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'Admin')
    log_audit('Logout Sistem', 'Autentikasi', f"Admin {username} logout dari sistem.")
    session.clear()
    flash('Anda telah berhasil keluar dari sistem.', 'info')
    return redirect(url_for('auth.login'))
