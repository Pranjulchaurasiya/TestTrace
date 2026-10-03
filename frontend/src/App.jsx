import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import ExamRoom from './pages/ExamRoom';
import ResultView from './pages/ResultView';
import { getUser, setToken, setUser } from './services/api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentView, setCurrentView] = useState('login'); // 'login', 'dashboard', 'exam', 'result'
  const [activeExamId, setActiveExamId] = useState(null);
  const [examResult, setExamResult] = useState(null);

  useEffect(() => {
    const savedUser = getUser();
    if (savedUser) {
      setCurrentUser(savedUser);
      setCurrentView('dashboard');
    }
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setCurrentUser(null);
    setCurrentView('login');
  };

  const handleStartExam = (examId) => {
    setActiveExamId(examId);
    setCurrentView('exam');
  };

  const handleExamCompleted = (result) => {
    setExamResult(result);
    setCurrentView('result');
  };

  const handleBackToDashboard = () => {
    setActiveExamId(null);
    setExamResult(null);
    setCurrentView('dashboard');
  };

  if (currentView === 'login' || !currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  if (currentView === 'exam') {
    return (
      <ExamRoom
        examId={activeExamId}
        onExamCompleted={handleExamCompleted}
      />
    );
  }

  if (currentView === 'result') {
    return (
      <ResultView
        result={examResult}
        onBackToDashboard={handleBackToDashboard}
      />
    );
  }

  // Role-based Dashboard routing
  if (currentUser.role === 'TEACHER' || currentUser.role === 'ADMIN') {
    return (
      <TeacherDashboard
        user={currentUser}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <Dashboard
      user={currentUser}
      onStartExam={handleStartExam}
      onLogout={handleLogout}
    />
  );
}
