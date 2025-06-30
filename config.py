import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Seguridad de sesión para CORS con cookies
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None"  # ⚠️ Necesario para cross-site cookies
    SESSION_COOKIE_SECURE = True      # ⚠️ Necesario en HTTPS (como en Vercel y Railway)

    # Flask-Mail (si aplica)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = False
