import React, { useState } from 'react';
import { Shield, Lock, User, AlertCircle } from 'lucide-react';
import { apiRequest, setToken, setUser } from '../services/api';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('student');
  const [password, setPassword] = useState('Student@12345');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');

    try {
      const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          password: password,
        }),
      });

      setToken(data.access_token);
      setUser(data.user);
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-card border border-border rounded-xl shadow-xs p-6 lg:p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-lg bg-primary text-white flex items-center justify-center font-bold mx-auto shadow-sm">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">TestTrace</h1>
          <p className="text-xs font-medium text-slate-500">
            Secure Examination & Algorithmic Proctoring Platform
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3 rounded-lg bg-danger-light border border-danger-border text-danger text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Username or Email</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-border rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-border rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white font-semibold text-sm shadow-xs transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Verifying Credentials...' : 'Sign In'}
          </button>
        </form>

        {/* Quick Demo Credentials */}
        <div className="pt-4 border-t border-border space-y-2">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">
            Demo Test Accounts:
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill('student', 'Student@12345')}
              className="px-2 py-1.5 rounded bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-mono text-slate-700 transition-colors"
            >
              Student
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('teacher', 'Teacher@12345')}
              className="px-2 py-1.5 rounded bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-mono text-slate-700 transition-colors"
            >
              Teacher
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('admin', 'Admin@12345')}
              className="px-2 py-1.5 rounded bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-mono text-slate-700 transition-colors"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
