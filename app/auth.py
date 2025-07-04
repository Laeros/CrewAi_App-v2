from flask import Blueprint, request, jsonify
from functools import wraps
from app.models import User, db
from flask_mail import Message
from app import mail
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_cors import cross_origin
import re
import os
from app.utils.logger import log_event

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
serializer = URLSafeTimedSerializer(os.getenv("JWT_SECRET_KEY", "clave-ultra-secreta"))

# Lista de dominios frontend permitidos
ALLOWED_ORIGINS = [
    "https://crew-ai-front-laeros-projects.vercel.app",
    "https://crew-ai-front-3gqlmdm0i-laeros-projects.vercel.app",
    "http://localhost:5173"  # opcional para desarrollo local
]

# ------------------- UTILIDADES -------------------

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Formato de token inválido'}), 401
        if not token:
            return jsonify({'message': 'Token requerido'}), 401
        current_user = User.verify_token(token)
        if not current_user:
            return jsonify({'message': 'Token inválido o expirado'}), 401
        return f(current_user, *args, **kwargs)
    return decorated_function

def get_current_user():
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return None
    if not token:
        return None
    return User.verify_token(token)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    if not re.search(r'[A-Za-z]', password):
        return False, "La contraseña debe contener al menos una letra"
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    return True, "Válida"

# ------------------- ENDPOINTS -------------------

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def register():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Username, email y password son requeridos'}), 400

        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']

        if len(username) < 3:
            return jsonify({'message': 'El username debe tener al menos 3 caracteres'}), 400
        if not validate_email(email):
            return jsonify({'message': 'Formato de email inválido'}), 400

        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({'message': password_message}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'El username ya está en uso'}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'El email ya está registrado'}), 409

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()

        log_event(f"👤 Nuevo usuario registrado: {user.username} ({user.email})")

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': user.to_dict(),
            'token': token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error interno del servidor: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def login():
    try:
        data = request.get_json()
        if not data or not data.get('login') or not data.get('password'):
            return jsonify({'message': 'Login y password son requeridos'}), 400

        login_input = data['login'].strip()
        password = data['password']

        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input.lower())
        ).first()

        if not user or not user.check_password(password):
            log_event(f"🔐 Login fallido para '{login_input}'")
            return jsonify({'message': 'Credenciales inválidas'}), 401
        if not user.is_active:
            return jsonify({'message': 'Cuenta desactivada'}), 401

        token = user.generate_token()
        log_event(f"✅ Login exitoso: {user.username}")

        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict(),
            'token': token
        }), 200

    except Exception as e:
        return jsonify({'message': f'Error interno del servidor: {str(e)}'}), 500

@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@token_required
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def get_current_user_info(current_user):
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def logout(current_user):
    log_event(f"🚪 Logout exitoso: {current_user.username}")
    return jsonify({'message': 'Logout exitoso'}), 200

@auth_bp.route('/change-password', methods=['PUT', 'OPTIONS'])
@token_required
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def change_password(current_user):
    try:
        data = request.get_json()
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'message': 'Contraseña actual y nueva contraseña son requeridas'}), 400

        current_password = data['current_password']
        new_password = data['new_password']

        if not current_user.check_password(current_password):
            log_event(f"🔒 Cambio de contraseña fallido para '{current_user.username}' (contraseña incorrecta)")
            return jsonify({'message': 'Contraseña actual incorrecta'}), 401

        is_valid_password, password_message = validate_password(new_password)
        if not is_valid_password:
            return jsonify({'message': password_message}), 400

        current_user.set_password(new_password)
        db.session.commit()

        log_event(f"🔁 Contraseña cambiada exitosamente por '{current_user.username}'")

        return jsonify({'message': 'Contraseña cambiada exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error interno del servidor: {str(e)}'}), 500

@auth_bp.route('/update-profile', methods=['PUT', 'OPTIONS'])
@token_required
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def update_profile(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Datos requeridos'}), 400

        if 'username' in data:
            new_username = data['username'].strip()
            if len(new_username) < 3:
                return jsonify({'message': 'El username debe tener al menos 3 caracteres'}), 400
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'message': 'El username ya está en uso'}), 409
            current_user.username = new_username

        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not validate_email(new_email):
                return jsonify({'message': 'Formato de email inválido'}), 400
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'message': 'El email ya está registrado'}), 409
            current_user.email = new_email

        db.session.commit()

        log_event(f"✏️ Perfil actualizado por '{current_user.username}'")

        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'user': current_user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error interno del servidor: {str(e)}'}), 500

@auth_bp.route('/request-reset', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def request_reset():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email or not validate_email(email):
            return jsonify({'message': 'Correo inválido'}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'message': 'Si el correo está registrado, se ha enviado un enlace de recuperación.'}), 200

        token = serializer.dumps(email, salt='password-recovery')

        frontend_url = os.getenv('FRONTEND_BASE_URL')
        if not frontend_url:
            raise RuntimeError("⚠️ Debes definir FRONTEND_BASE_URL en las variables de entorno.")

        reset_link = f"{frontend_url}/reset-password?token={token}"

        msg = Message("Recuperación de contraseña", recipients=[email])
        msg.body = f"""Hola {user.username},

Recibiste este correo porque solicitaste restablecer tu contraseña.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_link}

Este enlace expira en 15 minutos. Si no lo solicitaste, puedes ignorarlo.

Gracias,
El equipo de CrewAIApp
"""
        mail.send(msg)

        log_event(f"📧 Solicitud de recuperación enviada para '{email}'")

        return jsonify({'message': 'Se ha enviado un enlace de recuperación si el correo está registrado'}), 200

    except Exception as e:
        return jsonify({'message': f'Error al enviar el correo: {str(e)}'}), 500

@auth_bp.route('/reset-password', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({'message': 'Token y nueva contraseña requeridos'}), 400

        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'message': msg}), 400

        try:
            email = serializer.loads(token, salt='password-recovery', max_age=900)
        except SignatureExpired:
            return jsonify({'message': 'El enlace ha expirado'}), 400
        except BadSignature:
            return jsonify({'message': 'Token inválido'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404

        user.set_password(new_password)
        db.session.commit()

        log_event(f"🔁 Contraseña restablecida para '{email}'")

        return jsonify({'message': 'Contraseña restablecida correctamente'}), 200

    except Exception as e:
        return jsonify({'message': f'Error interno: {str(e)}'}), 500
