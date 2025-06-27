from app import db
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os

# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    agents = db.relationship('Agent', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        payload = {
            'user_id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'your-secret-key'), algorithm='HS256')
        return token if isinstance(token, str) else token.decode('utf-8')

    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def promote_to_admin(self, target_user):
        if self.is_admin:
            target_user.is_admin = True
            db.session.commit()
        else:
            raise PermissionError("No tienes permiso para realizar esta acción.")

    def demote_from_admin(self, target_user):
        if self.is_admin:
            if target_user.id == self.id:
                raise PermissionError("No puedes revocar tu propio rol de administrador.")
            target_user.is_admin = False
            db.session.commit()
        else:
            raise PermissionError("No tienes permiso para realizar esta acción.")

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }

# ---------------- AGENT ----------------
class Agent(db.Model):
    __tablename__ = 'agent'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False, default=0.1)
    max_tokens = db.Column(db.Integer, nullable=False, default=50)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='agents')

    tools = db.relationship('Tool', secondary='agent_tool', backref='agents')
    chat_logs = db.relationship('ChatLog', backref='agent', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'prompt': self.prompt,
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'user_id': self.user_id,
            'tools': [tool.to_dict() for tool in self.tools]
        }

# ---------------- TOOL ----------------
class Tool(db.Model):
    __tablename__ = 'tool'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    parameters = db.Column(JSONB, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }

# ---------------- AGENT_TOOL ----------------
class AgentTool(db.Model):
    __tablename__ = 'agent_tool'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id', ondelete='CASCADE'))
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id', ondelete='CASCADE'))

    __table_args__ = (
        db.UniqueConstraint('agent_id', 'tool_id', name='unique_agent_tool'),
    )

# ---------------- CHAT_LOG ----------------
class ChatLog(db.Model):
    __tablename__ = 'chat_log'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id', ondelete='CASCADE'))
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' o 'assistant'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
# ---------------- LOG_ENTRY ----------------
class LogEntry(db.Model):
    __tablename__ = 'log_entry'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }