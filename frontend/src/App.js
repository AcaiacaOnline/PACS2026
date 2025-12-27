import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';
import PACList from './pages/PACList';
import PACEditor from './pages/PACEditor';
import PACGeralList from './pages/PACGeralList';
import PACGeralEditor from './pages/PACGeralEditor';
import Users from './pages/Users';
import ProtectedRoute from './components/ProtectedRoute';
import { Toaster } from './components/ui/sonner';
import './App.css';

function App() {
  // Check for session_id in URL hash during render (before Routes)
  if (window.location.hash && window.location.hash.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <div className="App">
      <Toaster position="top-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/pacs" element={<ProtectedRoute><PACList /></ProtectedRoute>} />
          <Route path="/pacs/:id/edit" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
          <Route path="/pacs/new" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
