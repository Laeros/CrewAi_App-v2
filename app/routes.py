import json
import os
from flask import Blueprint, request, jsonify
from openai import OpenAI
from app.models import Agent as AgentModel, Tool as ToolModel, ChatLog, User, db
from app.auth import token_required, get_current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Crear agente (requiere autenticación)
@api_bp.route('/agents', methods=['POST'])
@token_required
def create_agent(current_user):
    try:
        agent_data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['name', 'prompt', 'llm_provider', 'model']
        for field in required_fields:
            if not agent_data.get(field):
                return jsonify({'message': f'El campo {field} es requerido'}), 400
        
        name = agent_data['name']
        prompt = agent_data['prompt']
        provider = agent_data['llm_provider']
        model = agent_data['model']
        temperature = agent_data.get('temperature', 0.1)
        max_tokens = agent_data.get('max_tokens', 50)
        tools = agent_data.get('tools', [])

        # Crear agente asociado al usuario actual
        agent = AgentModel(
            name=name,
            prompt=prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            user_id=current_user.id  # Asociar al usuario actual
        )

        # Asociar herramientas si existen
        if tools:
            associated_tools = ToolModel.query.filter(ToolModel.name.in_(tools)).all()
            agent.tools.extend(associated_tools)

        db.session.add(agent)
        db.session.commit()

        return jsonify({
            "message": "Agente creado exitosamente", 
            "agent_id": agent.id,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "prompt": agent.prompt,
                "provider": agent.provider,
                "model": agent.model,
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "tools": [tool.name for tool in agent.tools]
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear agente: {str(e)}'}), 500

# Crear herramienta (solo para administradores o públicas)
@api_bp.route('/tools', methods=['POST'])
@token_required
def create_tool(current_user):
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('description'):
            return jsonify({'message': 'Nombre y descripción son requeridos'}), 400
        
        tool_parameters = data.get('parameters', {})
        if isinstance(tool_parameters, str):
            tool_parameters = json.loads(tool_parameters)

        if "type" not in tool_parameters:
            tool_parameters = {
                "type": "object",
                "properties": tool_parameters,
                "required": list(tool_parameters.keys())
            }

        tool = ToolModel(
            name=data['name'],
            description=data['description'],
            parameters=tool_parameters
        )
        db.session.add(tool)
        db.session.commit()
        
        return jsonify({
            "message": "Tool creada exitosamente", 
            "tool_id": tool.id,
            "tool": {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear herramienta: {str(e)}'}), 500

# Listar agentes del usuario actual
@api_bp.route('/agents', methods=['GET'])
@token_required
def list_agents(current_user):
    try:
        # Solo mostrar agentes del usuario actual
        agents = AgentModel.query.filter_by(user_id=current_user.id).all()
        agent_list = [{
            "id": agent.id,
            "name": agent.name,
            "prompt": agent.prompt,
            "provider": agent.provider,
            "model": agent.model,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "tools": [tool.name for tool in agent.tools]
        } for agent in agents]
        return jsonify(agent_list), 200
    except Exception as e:
        return jsonify({'message': f'Error al listar agentes: {str(e)}'}), 500

# Obtener agente específico del usuario
@api_bp.route('/agents/<int:agent_id>', methods=['GET'])
@token_required
def get_agent(current_user, agent_id):  # ✅ CORREGIDO: current_user primero
    try:
        agent = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent:
            return jsonify({'message': 'Agente no encontrado'}), 404
        
        return jsonify({
            "id": agent.id,
            "name": agent.name,
            "prompt": agent.prompt,
            "provider": agent.provider,
            "model": agent.model,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "tools": [{"id": tool.id, "name": tool.name} for tool in agent.tools]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error al obtener agente: {str(e)}'}), 500

# Actualizar agente (solo del usuario actual)
@api_bp.route('/agents/<int:agent_id>', methods=['PUT'])
@token_required
def update_agent(current_user, agent_id):  # ✅ CORREGIDO: current_user primero
    try:
        data = request.get_json()
        
        # Verificar que el agente pertenece al usuario actual
        agent = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent:
            return jsonify({'message': 'Agente no encontrado'}), 404
        
        # Actualizar campos
        agent.name = data.get('name', agent.name)
        agent.prompt = data.get('prompt', agent.prompt)
        agent.provider = data.get('llm_provider', agent.provider)
        agent.model = data.get('model', agent.model)
        agent.temperature = data.get('temperature', agent.temperature)
        agent.max_tokens = data.get('max_tokens', agent.max_tokens)

        # Actualizar herramientas asociadas
        if 'tools' in data:
            tools = ToolModel.query.filter(ToolModel.name.in_(data['tools'])).all()
            agent.tools = tools

        db.session.commit()
        return jsonify({"message": "Agente actualizado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar agente: {str(e)}'}), 500

# Eliminar agente (solo del usuario actual)
@api_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@token_required
def delete_agent(current_user, agent_id):  # ✅ CORREGIDO: current_user primero
    try:
        # Verificar que el agente pertenece al usuario actual
        agent = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent:
            return jsonify({'message': 'Agente no encontrado'}), 404
        
        db.session.delete(agent)
        db.session.commit()
        return jsonify({"message": "Agente eliminado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar agente: {str(e)}'}), 500

# Listar herramientas (públicas)
@api_bp.route('/tools', methods=['GET'])
@token_required
def list_tools(current_user):
    try:
        tools = ToolModel.query.all()
        tool_list = [{
            "id": tool.id, 
            "name": tool.name,
            "description": tool.description
        } for tool in tools]
        return jsonify(tool_list), 200
    except Exception as e:
        return jsonify({'message': f'Error al listar herramientas: {str(e)}'}), 500

# Actualizar herramienta
@api_bp.route('/tools/<int:tool_id>', methods=['PUT'])
@token_required
def update_tool(current_user, tool_id):  # ✅ CORREGIDO: current_user primero
    try:
        data = request.get_json()
        tool = ToolModel.query.get_or_404(tool_id)
        
        tool.name = data.get('name', tool.name)
        tool.description = data.get('description', tool.description)
        if 'parameters' in data:
            tool.parameters = data['parameters']
        
        db.session.commit()
        return jsonify({"message": "Tool actualizada correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar herramienta: {str(e)}'}), 500

# Eliminar herramienta
@api_bp.route('/tools/<int:tool_id>', methods=['DELETE'])
@token_required
def delete_tool(current_user, tool_id):  # ✅ CORREGIDO: current_user primero
    try:
        tool = ToolModel.query.get_or_404(tool_id)
        db.session.delete(tool)
        db.session.commit()
        return jsonify({"message": "Tool eliminada correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar herramienta: {str(e)}'}), 500

# Listar chats del agente (solo del usuario actual)
@api_bp.route('/agents/<int:agent_id>/chats', methods=['GET'])
@token_required
def list_chats(current_user, agent_id):  # ✅ CORREGIDO: current_user primero
    try:
        # Verificar que el agente pertenece al usuario actual
        agent = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent:
            return jsonify({'message': 'Agente no encontrado'}), 404
        
        chats = ChatLog.query.filter_by(agent_id=agent_id).order_by(ChatLog.timestamp.asc()).all()
        chat_list = [{
            "id": chat.id,
            "message": chat.message,
            "role": chat.role,
            "timestamp": chat.timestamp.isoformat() if chat.timestamp else None
        } for chat in chats]
        return jsonify(chat_list), 200
    except Exception as e:
        return jsonify({'message': f'Error al listar chats: {str(e)}'}), 500

# Eliminar chats del agente (solo del usuario actual)
@api_bp.route('/agents/<int:agent_id>/chats', methods=['DELETE'])
@token_required
def delete_chats(current_user, agent_id):  # ✅ CORREGIDO: current_user primero
    try:
        # Verificar que el agente pertenece al usuario actual
        agent = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent:
            return jsonify({'message': 'Agente no encontrado'}), 404
        
        chats = ChatLog.query.filter_by(agent_id=agent_id).all()
        for chat in chats:
            db.session.delete(chat)
        db.session.commit()
        return jsonify({"message": "Chats eliminados correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar chats: {str(e)}'}), 500

# Chat con agente (solo del usuario actual)
@api_bp.route('/chat/<int:agent_id>', methods=['POST'])
@token_required
def chat_with_agent(current_user, agent_id): 
    try:
        data = request.get_json()
        
        if not data.get('message'):
            return jsonify({'message': 'Mensaje requerido'}), 400
        
        # Verificar que el agente pertenece al usuario actual
        agent_db = AgentModel.query.filter_by(id=agent_id, user_id=current_user.id).first()
        if not agent_db:
            return jsonify({'message': 'Agente no encontrado'}), 404

        # Configurar OpenAI
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        client = OpenAI()

        # Preparar herramientas
        tools = []
        for tool in agent_db.tools:
            if tool.description and tool.parameters:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                })

        # Obtener historial de chat reciente (últimos 20 mensajes)
        recent_chats = ChatLog.query.filter_by(agent_id=agent_id).order_by(ChatLog.timestamp.desc()).limit(20).all()
        recent_chats.reverse()  # Ordenar cronológicamente

        # Construir mensajes
        messages = [{"role": "system", "content": agent_db.prompt}]
        
        # Agregar historial reciente
        for chat in recent_chats:
            messages.append({"role": chat.role, "content": chat.message})
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": data["message"]})

        # Primera llamada al modelo
        response = client.chat.completions.create(
            model=agent_db.model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=agent_db.temperature,
            max_tokens=agent_db.max_tokens
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls
        tool_messages = []

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except Exception:
                    tool_args = {}

                # Simular ejecución de herramientas
                if tool_name == "buscar_web":
                    result = f"Resultado simulado para búsqueda: {tool_args.get('query', '')}"
                else:
                    result = f"[Simulación] Herramienta '{tool_name}' ejecutada con argumentos: {tool_args}"

                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            # Añadir mensajes de herramientas
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tc.model_dump() for tc in tool_calls]
            })
            messages.extend(tool_messages)

            # Segunda llamada al modelo
            final_response = client.chat.completions.create(
                model=agent_db.model,
                messages=messages,
                temperature=agent_db.temperature,
                max_tokens=agent_db.max_tokens
            )
            final_message = final_response.choices[0].message.content
        else:
            final_message = assistant_message.content

        # Guardar mensajes en el historial
        user_log = ChatLog(agent_id=agent_id, message=data["message"], role="user")
        assistant_log = ChatLog(agent_id=agent_id, message=final_message, role="assistant")
        
        db.session.add(user_log)
        db.session.add(assistant_log)
        db.session.commit()
        
        return jsonify({"respuesta": final_message}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error en el chat: {str(e)}'}), 500

# Ruta de estado para verificar conectividad
@api_bp.route('/status', methods=['GET'])
def status():
    current_user = get_current_user()
    return jsonify({
        'status': 'ok',
        'authenticated': current_user is not None,
        'user': current_user.to_dict() if current_user else None
    }), 200

@api_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validar campos requeridos
        if not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'message': 'Todos los campos son obligatorios (username, email, password)'}), 400

        # Verificar si el usuario ya existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'El nombre de usuario ya está en uso'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'El correo electrónico ya está en uso'}), 400

        # Crear nuevo usuario
        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
        user = User(username=data['username'], email=data['email'], password=data['password'])
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'Usuario registrado exitosamente'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Error de integridad. Datos duplicados'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al registrar usuario: {str(e)}'}), 500
    
# Rutas administrativas (requieren permisos de administrador)

@api_bp.route('/admin/users', methods=['GET'])
@token_required
def list_users(current_user):
    if not current_user.is_admin:
        return jsonify({'message': 'Acceso denegado'}), 403

    users = User.query.all()
    user_list = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    } for user in users]

    return jsonify(user_list), 200


@api_bp.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@token_required
def update_user_role(current_user, user_id):
    if not current_user.is_admin:
        return jsonify({'message': 'Acceso denegado'}), 403

    if current_user.id == user_id:
        return jsonify({'message': 'No puedes modificar tu propio rol'}), 400

    data = request.get_json()
    is_admin = data.get('is_admin')
    
    if is_admin is None:
        return jsonify({'message': 'El campo "is_admin" es requerido'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    user.is_admin = bool(is_admin)
    db.session.commit()

    return jsonify({'message': f'Rol de usuario "{user.username}" actualizado correctamente'}), 200


@api_bp.route('/admin/logs', methods=['GET'])
@token_required
def view_logs(current_user):
    if not current_user.is_admin:
        return jsonify({'message': 'Acceso denegado'}), 403

    from app.models import LogEntry  # Si no estaba importado al inicio

    logs = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(100).all()
    log_list = [{
        'id': log.id,
        'timestamp': log.timestamp.isoformat(),
        'event': log.event
    } for log in logs]

    return jsonify(log_list), 200
