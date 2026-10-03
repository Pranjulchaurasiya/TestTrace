import React, { useEffect, useState } from 'react';
import { BookOpen, Clock, Award, ShieldCheck, ArrowRight, User, History, Download, CheckCircle2, AlertTriangle } from 'lucide-react';
import { apiRequest } from '../services/api';
import Navbar from '../components/Navbar';

export default function Dashboard({ user, onStartExam, onLogout }) {
  const [exams, setExams] = useState([]);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('exams'); // 'exams' or 'history'
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [examsData, historyData] = await Promise.all([
          apiRequest('/exams'),
          apiRequest('/attempts/my-history').catch(() => []),
        ]);
        setExams(examsData || []);
        setHistory(historyData || []);
      } catch (err) {
        setError(err.message || 'Failed to fetch dashboard data');
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <Navbar onLogout={onLogout} userName={user?.name} />

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 lg:p-8 space-y-6">
        {/* Welcome Banner */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Welcome, {user?.name || 'Student'}
            </h2>
            <p className="text-xs text-slate-500">
              Role: <span className="font-semibold text-primary">{user?.role}</span> • Account: <span className="font-mono">{user?.email}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded bg-success-light border border-success-border text-success text-xs font-semibold">
              Assessment System Online
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <button
            onClick={() => setActiveTab('exams')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              activeTab === 'exams'
                ? 'bg-primary text-white shadow-xs'
                : 'bg-card text-slate-600 hover:text-slate-900 border border-border'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Available Examinations ({exams.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              activeTab === 'history'
                ? 'bg-primary text-white shadow-xs'
                : 'bg-card text-slate-600 hover:text-slate-900 border border-border'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>My Assessment History & Reports ({history.length})</span>
          </button>
        </div>

        {/* Tab 1: Available Exams */}
        {activeTab === 'exams' && (
          <div className="space-y-4">
            {isLoading && (
              <div className="p-8 text-center text-slate-500 text-sm">Loading available examinations...</div>
            )}

            {error && (
              <div className="p-4 rounded-lg bg-danger-light border border-danger-border text-danger text-xs">
                {error}
              </div>
            )}

            {!isLoading && exams.length === 0 && (
              <div className="p-8 bg-card border border-border rounded-lg text-center text-slate-500 text-sm">
                No published examinations available at this time.
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {exams.map((exam) => (
                <div
                  key={exam.id}
                  className="bg-card border border-border rounded-xl p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {exam.subject}
                      </span>
                      {exam.proctoring_enabled && (
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                          <span>AI Proctoring</span>
                        </span>
                      )}
                    </div>

                    <h4 className="text-base font-bold text-slate-900 leading-snug">{exam.title}</h4>
                    <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                      {exam.description || 'Standard timed curriculum assessment.'}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-border flex items-center justify-between text-xs font-mono text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{exam.duration_minutes} Minutes</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-slate-400" />
                      <span>{exam.total_marks} Marks ({exam.question_count} Qs)</span>
                    </div>
                  </div>

                  <button
                    onClick={() => onStartExam(exam.id)}
                    className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <span>Enter Examination Room</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: My Assessment History */}
        {activeTab === 'history' && (
          <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Your Completed Assessments</h3>
                <p className="text-xs text-slate-500">
                  Review finalized scores, integrity status, and download official PDF report cards.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">{history.length} records</span>
            </div>

            {history.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-xs">
                You have not completed any examinations yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-border text-slate-600 uppercase font-semibold tracking-wider text-[10px]">
                    <tr>
                      <th className="px-5 py-3">Examination</th>
                      <th className="px-3 py-3">Score</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3">Integrity</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-slate-700">
                    {history.map((att) => (
                      <tr key={att.attempt_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="font-semibold text-slate-900">{att.exam_title}</div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Attempt #{att.attempt_id} • {new Date(att.start_time).toLocaleDateString()}
                          </div>
                        </td>

                        <td className="px-3 py-3.5 font-mono">
                          <div className="font-bold text-slate-900">
                            {att.final_score} / {att.total_marks}
                          </div>
                          <div className="text-[10px]">
                            {att.passed ? (
                              <span className="text-emerald-600 font-semibold">Passed</span>
                            ) : (
                              <span className="text-rose-600 font-semibold">Failed</span>
                            )}
                          </div>
                        </td>

                        <td className="px-3 py-3.5">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                              att.status === 'SUBMITTED'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border-rose-200'
                            }`}
                          >
                            {att.status}
                          </span>
                        </td>

                        <td className="px-3 py-3.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              att.integrity_status === 'LOW'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border-rose-200'
                            }`}
                          >
                            {att.integrity_status} Risk
                          </span>
                        </td>

                        <td className="px-4 py-3.5 text-right">
                          <button
                            onClick={() => {
                              const token = localStorage.getItem('testtrace_token');
                              const url = `http://127.0.0.1:8000/attempts/${att.attempt_id}/pdf-report`;
                              fetch(url, {
                                headers: { Authorization: `Bearer ${token}` },
                              })
                                .then((res) => res.blob())
                                .then((blob) => {
                                  const blobUrl = window.URL.createObjectURL(blob);
                                  const a = document.createElement('a');
                                  a.href = blobUrl;
                                  a.download = `TestTrace_Report_Attempt_${att.attempt_id}.pdf`;
                                  document.body.appendChild(a);
                                  a.click();
                                  a.remove();
                                })
                                .catch((err) => alert('Failed to download PDF: ' + err.message));
                            }}
                            className="px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] inline-flex items-center gap-1 transition-colors"
                          >
                            <Download className="w-3.5 h-3.5 text-slate-500" />
                            <span>Download PDF</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
