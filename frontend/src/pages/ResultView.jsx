import React, { useEffect, useState } from 'react';
import { Award, ShieldCheck, AlertTriangle, ArrowLeft, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { apiRequest } from '../services/api';

export default function ResultView({ result, onBackToDashboard }) {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (!result?.attempt_id) return;

    async function fetchEvents() {
      try {
        const data = await apiRequest(`/proctor/attempts/${result.attempt_id}/events`);
        setEvents(data);
      } catch (err) {
        console.error('Failed to load events:', err);
      }
    }
    fetchEvents();
  }, [result]);

  if (!result) return null;

  const passed = result.passed;
  const isHighRisk = result.integrity_status === 'HIGH' || result.integrity_status === 'CRITICAL';

  return (
    <div className="min-h-screen bg-canvas py-8 px-4 flex flex-col items-center justify-center">
      <div className="max-w-3xl w-full bg-card border border-border rounded-xl shadow-xs p-6 lg:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border pb-4">
          <div>
            <span className="text-[11px] font-mono font-bold uppercase text-primary bg-primary-light px-2 py-0.5 rounded">
              Examination Result & Integrity Record
            </span>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">{result.exam_title}</h1>
            <p className="text-xs text-slate-500">
              Candidate: <span className="font-semibold text-slate-800">{result.student_name}</span> • Attempt #{result.attempt_id}
            </p>
          </div>

          <div
            className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider border ${
              passed
                ? 'bg-success-light text-success border-success-border'
                : 'bg-danger-light text-danger border-danger-border'
            }`}
          >
            {passed ? 'Passed' : 'Failed'}
          </div>
        </div>

        {/* Scorecard Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-slate-50 border border-border">
            <div className="text-[11px] text-slate-500 font-medium">Final Score</div>
            <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
              {result.final_score} / {result.total_marks}
            </div>
            <div className="text-[10px] text-slate-400">Passing: {result.passing_marks} marks</div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-border">
            <div className="text-[11px] text-slate-500 font-medium">Integrity Risk</div>
            <div
              className={`text-xl font-bold font-mono mt-0.5 ${
                isHighRisk ? 'text-danger' : 'text-success'
              }`}
            >
              {result.integrity_status}
            </div>
            <div className="text-[10px] text-slate-400">{result.suspicious_score} penalty pts</div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-border">
            <div className="text-[11px] text-slate-500 font-medium">Tab Switches</div>
            <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
              {result.tab_switch_count}
            </div>
            <div className="text-[10px] text-slate-400">Max limit: 3</div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-border">
            <div className="text-[11px] text-slate-500 font-medium">Session Status</div>
            <div className="text-xs font-bold font-mono text-slate-900 mt-1 uppercase">
              {result.status}
            </div>
            <div className="text-[10px] text-slate-400">{result.answered_count} answered</div>
          </div>
        </div>

        {/* Termination Reason Alert if any */}
        {result.termination_reason && (
          <div className="p-3 rounded-lg bg-danger-light border border-danger-border text-xs text-danger flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Termination Reason: {result.termination_reason}</span>
          </div>
        )}

        {/* Chronological Proctoring Audit Trail */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Chronological Integrity Audit Trail ({events.length} Events)
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">Timestamped UTC Log</span>
          </div>

          <div className="border border-border rounded-lg overflow-hidden max-h-48 overflow-y-auto custom-scrollbar">
            {events.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                Zero integrity anomalies recorded during this examination session.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-border text-[11px] font-mono text-slate-500 uppercase">
                  <tr>
                    <th className="p-2.5">Time</th>
                    <th className="p-2.5">Event</th>
                    <th className="p-2.5">Severity</th>
                    <th className="p-2.5 text-right">Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono text-[11px]">
                  {events.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-50">
                      <td className="p-2.5 text-slate-500">
                        {new Date(ev.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="p-2.5 font-sans font-medium text-slate-800">{ev.event_type}</td>
                      <td className="p-2.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] ${
                            ev.severity === 'CRITICAL'
                              ? 'bg-danger-light text-danger'
                              : 'bg-warning-light text-warning'
                          }`}
                        >
                          {ev.severity}
                        </span>
                      </td>
                      <td className="p-2.5 text-right font-bold text-slate-700">+{ev.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-border flex items-center justify-between">
          <button
            onClick={() => {
              const token = localStorage.getItem('testtrace_token');
              const url = `http://127.0.0.1:8000/attempts/${result.attempt_id}/pdf-report`;
              fetch(url, {
                headers: { Authorization: `Bearer ${token}` },
              })
                .then((res) => res.blob())
                .then((blob) => {
                  const blobUrl = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = blobUrl;
                  a.download = `TestTrace_Report_Attempt_${result.attempt_id}.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                })
                .catch((err) => alert('Failed to download report PDF: ' + err.message));
            }}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-xs transition-colors flex items-center gap-2"
          >
            <Award className="w-3.5 h-3.5" />
            <span>Download Official PDF Report Card</span>
          </button>

          <button
            onClick={onBackToDashboard}
            className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition-colors flex items-center gap-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    </div>
  );
}
