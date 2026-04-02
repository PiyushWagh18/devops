import os
import secrets
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # ── Secret key ────────────────────────────────────────────────────────────
    # Never fall back to a hard-coded string (Bandit B105).
    # In production FLASK_ENV=production must be set; a missing key is fatal.
    secret_key = os.environ.get('SECRET_KEY')
    is_production = os.environ.get('FLASK_ENV', '').lower() == 'production'

    if not secret_key:
        if is_production:
            raise RuntimeError(
                'SECRET_KEY environment variable must be set in production. '
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        # Development only: fresh random key per process (sessions invalidated on restart)
        secret_key = secrets.token_hex(32)
        logging.warning(
            'SECRET_KEY not set – auto-generated a temporary key for development. '
            'All sessions will be lost on restart. Set SECRET_KEY in .env.'
        )

    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # ── Secure session cookies ────────────────────────────────────────────────
    # SESSION_COOKIE_SECURE must only be True when the site is served over HTTPS.
    # Default to False so HTTP deployments (e.g. EC2 without TLS) work correctly.
    https_enabled = os.environ.get('HTTPS_ENABLED', 'False').lower() == 'true'
    app.config['SESSION_COOKIE_SECURE'] = https_enabled    # HTTPS-only when TLS configured
    app.config['SESSION_COOKIE_HTTPONLY'] = True           # No JS access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'          # CSRF mitigation
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600               # 1-hour CSRF token

    db.init_app(app)
    csrf.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    # ── Security headers ──────────────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        # Prevent MIME-type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Block clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Limit referrer info leakage
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Restrict browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=()'
        )
        # HTTPS enforcement (only when TLS is configured via HTTPS_ENABLED=True)
        if https_enabled:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        # Content Security Policy – no unsafe-inline; all scripts from 'self' or CDN
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        return response

    # ── Error handlers (prevent stack-trace disclosure) ───────────────────────
    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('errors.html', code=404, message='Page Not Found'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        return render_template('errors.html', code=500, message='Internal Server Error'), 500

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('errors.html', code=403, message='Forbidden'), 403

    return app