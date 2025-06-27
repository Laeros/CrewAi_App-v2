import React, { useState } from 'react';
import { useParams } from 'react-router-dom';

export default function ResetPassword() {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [confirmed, setConfirmed] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Lógica para enviar nueva contraseña
    setConfirmed(true);
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <h2>Restablecer contraseña</h2>
        {confirmed ? (
          <p>Tu contraseña ha sido restablecida correctamente.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <input
              type="password"
              placeholder="Nueva contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button type="submit">Restablecer</button>
          </form>
        )}
      </div>
    </div>
  );
}
