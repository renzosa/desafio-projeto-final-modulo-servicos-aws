import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = () => {
    // Lógica de autenticação
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    // Lógica de logout
    setIsAuthenticated(false);
  };

  return (
    <div className="App">
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ?
              <Navigate to="/dashboard" replace /> :
              <LoginPage onLogin={handleLogin} />
          }
        />
        <Route
          path="/dashboard"
          element={
            isAuthenticated ?
              <DashboardPage onLogout={handleLogout} /> :
              <Navigate to="/login" replace />
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ?
              <Navigate to="/dashboard" replace /> :
              <Navigate to="/login" replace />
          }
        />
      </Routes>
    </div>
  );
}

export default App;