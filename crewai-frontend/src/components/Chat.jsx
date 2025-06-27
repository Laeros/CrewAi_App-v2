import React, { useEffect, useState, useRef } from 'react';
import { fetchChats, sendMessage, deleteChats } from '../services/api';

export default function Chat({
  agent,
  chat,
  onChatStart,
  tools = [],
  selectedTools = [],
  onToggleTool = () => {},
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (agent) {
      loadChats();
    }
  }, [agent]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChats = async () => {
    try {
      const data = await fetchChats(agent.id);
      setMessages(data || []);
    } catch (error) {
      console.error('Error loading chats:', error);
      setMessages([]);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    const newUserMessage = {
      id: Date.now(),
      message: userMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);

    if (messages.length === 0 && onChatStart) {
      onChatStart();
    }

    try {
      const res = await sendMessage(agent.id, userMessage);
      const agentMessage = {
        id: Date.now() + 1,
        message: res.respuesta || res.message || 'Lo siento, no pude procesar tu mensaje.',
        sender: 'agent',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        message: 'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo.',
        sender: 'agent',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleClear = async () => {
    if (!agent || loading) return;

    try {
      await deleteChats(agent.id);
      setMessages([]);
    } catch (error) {
      console.error('Error clearing chats:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="chat-container">
      {!agent ? (
        <>
          <div className="chat-welcome">
            <h2 className="welcome-title">¡Hola, Rodrigo! ¿Todo listo para empezar?</h2>
            <p className="welcome-subtitle">Selecciona un agente para comenzar a chatear</p>
          </div>

          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <button className="tools-button" disabled>⚙️ Herramientas</button>
              <textarea
                className="chat-input"
                placeholder="Selecciona un agente para comenzar..."
                rows="1"
                disabled
              />
              <button className="send-button" disabled>↑</button>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="chat-agent-header">
            <div className="agent-info">
              <div className="agent-avatar">{agent.name.charAt(0).toUpperCase()}</div>
              <div className="agent-details">
                <h3 className="agent-name">{agent.name}</h3>
                <p className="agent-status">{loading ? 'Escribiendo...' : 'En línea'}</p>
                {selectedTools.length > 0 && (
                  <div className="active-tools">
                    {tools
                      .filter(t => selectedTools.includes(t.id))
                      .map(t => (
                        <span key={t.id} className="tool-chip">{t.name}</span>
                      ))}
                  </div>
                )}
              </div>
            </div>
            <div className="chat-actions">
              <button
                className="clear-chat-btn"
                onClick={handleClear}
                disabled={loading || messages.length === 0}
                title="Limpiar conversación"
              >
                🗑️
              </button>
            </div>
          </div>

          <div className="chat-messages-container">
            {messages.length === 0 ? (
              <div className="empty-chat">
                <div className="empty-chat-icon">💬</div>
                <h3>Inicia una conversación</h3>
                <p>Envía un mensaje para comenzar a chatear con {agent.name}</p>
              </div>
            ) : (
              <div className="chat-messages">
                {messages.map((msg) => (
                  <div
                    key={msg.id || Math.random()}
                    className={`message-row ${msg.sender === 'user' ? 'message-right' : 'message-left'}`}
                  >
                    <div className={`message ${msg.sender}`}>
                      <div className="message-avatar">
                        {msg.sender === 'user' ? 'U' : agent.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="message-content-wrapper">
                        <div className={`message-content ${msg.isError ? 'error' : ''}`}>
                          {msg.message}
                        </div>
                        {msg.timestamp && (
                          <div className="message-timestamp">
                            {formatTimestamp(msg.timestamp)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="message-row message-left">
                    <div className="message agent">
                      <div className="message-avatar">{agent.name.charAt(0).toUpperCase()}</div>
                      <div className="message-content-wrapper">
                        <div className="message-content loading">
                          <div className="typing-indicator">
                            <span></span><span></span><span></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <button
                className="tools-button"
                onClick={() => setShowToolsPanel(prev => !prev)}
              >
                ⚙️ Herramientas
              </button>

              {showToolsPanel && (
                <div className="tool-selector-panel">
                  <ul className="tool-selector-list">
                    {tools.filter(tool => selectedTools.includes(tool.id)).length > 0 ? (
                      tools
                        .filter(tool => selectedTools.includes(tool.id))
                        .map(tool => (
                          <li key={tool.id} className="tool-selector-item selected">
                            <span className="tool-icon">🛠️</span>
                            <span>{tool.name}</span>
                          </li>
                        ))
                    ) : (
                      <li className="tool-selector-item disabled">
                        <span>No hay herramientas activas</span>
                      </li>
                    )}
                  </ul>
                </div>
              )}

              <textarea
                ref={textareaRef}
                className="chat-input"
                placeholder={`Envía un mensaje a ${agent.name}...`}
                value={input}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                disabled={loading}
                rows="1"
              />
              <button
                className="send-button"
                onClick={handleSend}
                disabled={loading || !input.trim()}
              >
                {loading ? '⏳' : '↑'}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
