import os
from flask import Flask
from dotenv import load_dotenv
from app.extensions import db, mail, migrate
from app.routes import api_bp
from app.auth import auth_bp
from app.models import User 

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Config CORS (ya manejado por cross_origin en rutas)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Validar correo
    for var in ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']:
        if not app.config.get(var):
            raise RuntimeError(f"La variable {var} es obligatoria para el envío de correos")

    # Inicializar extensiones
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # Crear admin si no existe
    with app.app_context():
        db.create_all()

        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not admin_email or not admin_password:
            raise RuntimeError("DEFAULT_ADMIN_EMAIL y DEFAULT_ADMIN_PASSWORD deben estar definidos")

        if not User.query.filter_by(email=admin_email).first():
            new_admin = User(
                username='admin',
                email=admin_email,
                password=admin_password,
                is_admin=True
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Admin creado: {admin_email}")
        else:
            print("ℹ️ Admin ya existe.")

    return app
