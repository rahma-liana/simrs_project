"""Buat akun Admin awal dengan password hash. Jalankan setelah schema.sql diimpor."""
import getpass
import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
username = input('Username Admin baru: ').strip()
email = input('Email Admin: ').strip()
nama = input('Nama lengkap Admin: ').strip()
password = getpass.getpass('Password (minimal 12 karakter): ')
confirm = getpass.getpass('Ulangi password: ')
if not username or not email or not nama:
    raise SystemExit('Username, email, dan nama wajib diisi.')
if len(password) < 12:
    raise SystemExit('Password harus minimal 12 karakter.')
if password != confirm:
    raise SystemExit('Konfirmasi password tidak sama.')
conn = pymysql.connect(host=os.getenv('DB_HOST','127.0.0.1'), port=int(os.getenv('DB_PORT','3306')), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','db_sistem_rumah_sakit'), charset='utf8mb4')
try:
    with conn.cursor() as cur:
        cur.execute('INSERT INTO users (username,email,password_hash,nama_lengkap) VALUES (%s,%s,%s,%s)', (username,email,generate_password_hash(password),nama))
    conn.commit()
    print('Akun Admin berhasil dibuat. Simpan kredensial dengan aman.')
except Exception as exc:
    conn.rollback()
    raise SystemExit(f'Gagal membuat akun. Pastikan username/email belum digunakan. Detail: {exc}')
finally:
    conn.close()
