import os
import logging
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from app.models import Agent as AgentModel, db

# Configuración del cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

def call_llm(agent, message, use_tools=True, debug=False):
    """
    Realiza una llamada a un modelo LLM (OpenAI) con o sin herramientas.

    Args:
        agent: objeto agente (de la base de datos).
        message (str): mensaje del usuario.
        use_tools (bool): si se deben incluir herramientas en la llamada.
        debug (bool): si se debe imprimir información de depuración.

    Returns:
        str: respuesta del modelo.
    """
    try:
        # Preparar mensajes
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=agent.prompt),
            ChatCompletionUserMessageParam(role="user", content=message)
        ]

        # Construir tools si corresponde
        tools: list[ChatCompletionToolParam] = []
        if use_tools and hasattr(agent, 'tools'):
            for tool in agent.tools:
                if tool.parameters:
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters
                        }
                    })

        if debug:
            print("===== Llamada a OpenAI =====")
            print("Model:", agent.model)
            print("Messages:", messages)
            print("Tools:", tools)
            print("=============================")

        # Ejecutar llamada al modelo
        response = client.chat.completions.create(
            model=agent.model,
            messages=messages,
            tools=tools if tools else None,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )

        if debug:
            print("===== Respuesta bruta de OpenAI =====")
            print(response)
            print("=============================")

        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            return "La respuesta está vacía o no contiene contenido."

    except Exception as e:
        logger.exception(f"Error al llamar al modelo LLM: {str(e)}")
        return f"Error en la llamada al modelo: {str(e)}"


def call_llm_from_id(agent_id, message, use_tools=True, debug=False):
    """
    Recupera un agente desde la base de datos por ID y llama al modelo LLM.

    Args:
        agent_id (int): ID del agente a consultar.
        message (str): mensaje del usuario.
        use_tools (bool): si se deben incluir herramientas.
        debug (bool): mostrar logs de depuración.

    Returns:
        str: respuesta generada por el modelo, o mensaje de error.
    """
    try:
        agent = AgentModel.query.get(agent_id)
        if not agent:
            return f"No se encontró ningún agente con ID {agent_id}."

        return call_llm(agent, message, use_tools=use_tools, debug=debug)

    except Exception as e:
        logger.exception(f"Error al recuperar el agente o llamar al modelo: {str(e)}")
        return f"Error al procesar la solicitud: {str(e)}"
