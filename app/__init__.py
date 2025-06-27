from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
import os

# Carga variables de entorno
load_dotenv()

# Inicializaciones globales
db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

    # Configuración de correo
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Validación rápida de config SMTP
    required_mail_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    for var in required_mail_vars:
        if not app.config.get(var):
            raise RuntimeError(f"⚠️ La variable de entorno {var} no está configurada para el envío de correos.")

    # Inicializaciones
    db.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "https://crewaiapp-production.up.railway.app"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Blueprints
    from .routes import api_bp
    from .auth import auth_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # Crear tablas y superusuario
    with app.app_context():
        db.create_all()

        from app.models import User  # evitar import circular

        admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL")
        admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

        if not admin_email or not admin_password:
            raise RuntimeError("⚠️ DEFAULT_ADMIN_EMAIL y DEFAULT_ADMIN_PASSWORD deben estar definidos en el entorno.")

        existing_admin = User.query.filter_by(is_admin=True).first()
        if not existing_admin:
            new_admin = User(username='admin', email=admin_email, is_admin=True)
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Admin creado: {admin_email} / {admin_password}")
        else:
            print("ℹ️ Admin ya existe.")

    return app
