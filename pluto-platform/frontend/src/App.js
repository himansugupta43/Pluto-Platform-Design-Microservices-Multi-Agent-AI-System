import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import './App.css'; // Import the unified CSS file

import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import FacilitatorDashboard from './pages/FacilitatorDashboard';
import PsychologistDashboard from './pages/PsychologistDashboard';
import RegisterPage from './pages/RegisterPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/student-dashboard" element={<StudentDashboard />} />
        <Route path="/facilitator-dashboard" element={<FacilitatorDashboard />} />
        <Route path="/psychologist-dashboard" element={<PsychologistDashboard />} />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;