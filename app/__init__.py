import os
import secrets
import hmac
from flask import Flask, request, session, abort
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'development-key-change-this'),
        DB_HOST=os.getenv('DB_HOST', '127.0.0.1'),
        DB_PORT=int(os.getenv('DB_PORT', '3306')),
        DB_USER=os.getenv('DB_USER', 'root'),
        DB_PASSWORD=os.getenv('DB_PASSWORD', ''),
        DB_NAME=os.getenv('DB_NAME', 'db_sistem_rumah_sakit'),
        FLASK_HOST=os.getenv('FLASK_HOST', '127.0.0.1'),
        FLASK_PORT=int(os.getenv('FLASK_PORT', '5000')),
        DEBUG=os.getenv('FLASK_DEBUG', '0') == '1',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    from datetime import datetime
    @app.before_request
    def protect_post_requests():
        if request.method == 'POST':
            submitted = request.form.get('_csrf_token', '')
            expected = session.get('_csrf_token', '')
            if not submitted or not expected or not hmac.compare_digest(submitted, expected):
                abort(400, description='Token keamanan formulir tidak valid. Muat ulang halaman dan coba lagi.')

    @app.context_processor
    def inject_globals():
        now = datetime.now()
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_urlsafe(32)
        return {'now_date': now.strftime('%d %B %Y'), 'today_iso': now.strftime('%Y-%m-%d'), 'current_year': now.year, 'csrf_token': session['_csrf_token']}

    from .routes import bp
    app.register_blueprint(bp)
    return app
