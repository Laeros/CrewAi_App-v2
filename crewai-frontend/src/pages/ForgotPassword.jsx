import React, { useState } from 'react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Lógica para enviar solicitud de recuperación
    setSubmitted(true);
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <h2>¿Olvidaste tu contraseña?</h2>
        {submitted ? (
          <p>Hemos enviado un enlace a tu correo si existe en nuestra base de datos.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Tu correo electrónico"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit">Enviar enlace de recuperación</button>
          </form>
        )}
      </div>
    </div>
  );
}
