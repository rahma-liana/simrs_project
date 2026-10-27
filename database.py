import pymysql
from pymysql.cursors import DictCursor
from config import Config
from contextlib import contextmanager

def get_db():
    """Membuka koneksi ke database MySQL Laragon."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset=Config.MYSQL_CHARSET,
        cursorclass=DictCursor,
        autocommit=False
    )

def query_db(sql, args=(), one=False):
    """Menjalankan query SELECT dan mengembalikan dictionary atau list dictionary."""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result
    finally:
        conn.close()

def execute_db(sql, args=(), commit=True):
    """Menjalankan query INSERT/UPDATE/DELETE dan mengembalikan (lastrowid, rowcount)."""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            last_id = cursor.lastrowid
            affected = cursor.rowcount
        if commit:
            conn.commit()
        return last_id, affected
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@contextmanager
def transaction_scope():
    """Context manager untuk operasi multi-tabel dengan atomic transaction commit/rollback."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
