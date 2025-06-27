import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../services/api';

export default function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!credentials.username || !credentials.password) {
      setError('Todos los campos son obligatorios');
      return;
    }

    try {
      const response = await loginUser({
        login: credentials.username,
        password: credentials.password
      });

      localStorage.setItem('token', response.data.token);

      navigate('/main'); // Redirigir al dashboard u otra ruta
    } catch (err) {
      setError('Credenciales inválidas o error del servidor');
    }
  };

  const togglePassword = () => {
    setShowPassword(prev => !prev);
  };

  const goToForgotPassword = () => {
    navigate('/forgot-password');
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <div className="auth-header">Iniciar Sesión</div>
        {error && <p className="error">{error}</p>}

        <form onSubmit={handleSubmit}>
          {/* Campo de usuario */}
          <label htmlFor="username">Usuario</label>
          <input
            id="username"
            type="text"
            name="username"
            placeholder="Usuario"
            value={credentials.username}
            onChange={handleChange}
            required
          />

          {/* Campo de contraseña con botón de visibilidad */}
          <label htmlFor="password">Contraseña</label>
          <div style={{ position: 'relative' }}>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              name="password"
              placeholder="Contraseña"
              value={credentials.password}
              onChange={handleChange}
              required
            />
            <button
              type="button"
              onClick={togglePassword}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: '0.8rem'
              }}
            >
              {showPassword ? 'Ocultar' : 'Mostrar'}
            </button>
          </div>

          {/* Botón de login */}
          <button type="submit" disabled={!credentials.username || !credentials.password}>
            Entrar
          </button>
        </form>

        {/* Olvidé mi contraseña */}
        <p style={{ marginTop: '10px' }}>
          <button
            onClick={goToForgotPassword}
            style={{
              background: 'none',
              border: 'none',
              color: '#007bff',
              textDecoration: 'underline',
              cursor: 'pointer',
              padding: 0
            }}
          >
            ¿Olvidaste tu contraseña?
          </button>
        </p>

        <p className="auth-footer">
          ¿No tienes cuenta? <a href="/register">Regístrate</a>
        </p>
      </div>
    </div>
  );
}
