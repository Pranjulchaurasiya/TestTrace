import React from 'react';
import { Shield, Clock, AlertTriangle, CheckCircle2, Video, LogOut } from 'lucide-react';

export default function Navbar({
  examTitle,
  subject,
  remainingSeconds,
  violationsCount = 0,
  onSubmitExam,
  isSubmitting = false,
  onLogout,
  userName,
}) {
  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const isCriticalTime = remainingSeconds <= 300;

  return (
    <header className="h-14 bg-card border-b border-border px-4 lg:px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Brand & Context */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-primary text-white flex items-center justify-center font-bold text-base shadow-sm">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 tracking-tight leading-none text-base">TestTrace</div>
            <div className="text-[11px] text-slate-500 tracking-wide font-medium">Test knowledge. Trace integrity</div>
          </div>
        </div>

        {examTitle && (
          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-border text-xs text-slate-600">
            <span className="font-semibold text-slate-900">{examTitle}</span>
            <span className="text-slate-400">•</span>
            <span className="px-2 py-0.5 rounded bg-slate-100 font-medium text-slate-700">{subject}</span>
          </div>
        )}
      </div>

      {/* Central / Right Controls */}
      <div className="flex items-center gap-3">
        {/* Authoritative Server Countdown */}
        {remainingSeconds !== undefined && (
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded border text-sm font-mono font-semibold transition-colors ${
              isCriticalTime
                ? 'bg-danger-light text-danger border-danger-border animate-pulse'
                : 'bg-slate-50 text-slate-800 border-border'
            }`}
          >
            <Clock className="w-4 h-4 text-slate-500" />
            <span>{formatTime(remainingSeconds)} Remaining</span>
          </div>
        )}

        {/* Proctor Active Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-success-light border border-success-border text-xs font-semibold text-success">
          <span className="w-2 h-2 rounded-full bg-success animate-ping"></span>
          <span>Proctoring Active</span>
        </div>

        {/* Violation Count Badge */}
        <div
          className={`flex items-center gap-1 px-2.5 py-1 rounded border text-xs font-semibold ${
            violationsCount > 0
              ? 'bg-warning-light text-warning border-warning-border'
              : 'bg-slate-50 text-slate-600 border-border'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>{violationsCount} Violations</span>
        </div>

        {/* Submit Exam CTA */}
        {onSubmitExam && (
          <button
            onClick={onSubmitExam}
            disabled={isSubmitting}
            className="px-4 py-1.5 rounded bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-60"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{isSubmitting ? 'Submitting...' : 'Submit Exam'}</span>
          </button>
        )}

        {/* Logout button if in dashboard */}
        {onLogout && (
          <button
            onClick={onLogout}
            title="Log Out"
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
}
