import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainPage from './pages/MainPage';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Logout from './components/Logout';
import './styles/main.css'

// Ruta privada: protege MainPage
function PrivateRoute({ children }) {
  const token = localStorage.getItem('jwtToken');
  return token ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Router>
      <div className="h-screen">
        <Routes>
          <Route path="/" element={<Navigate to="/main" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/logout" element={<Logout />} />  {/* ruta logout */}
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/main" element={
            <PrivateRoute>
              <MainPage />
            </PrivateRoute>
          } />
          {/* Ruta 404 opcional */}
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}
