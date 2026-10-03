import React, { useEffect, useState } from 'react';
import {
  Shield,
  BookOpen,
  Plus,
  Users,
  AlertTriangle,
  Award,
  Clock,
  Eye,
  Filter,
  RefreshCw,
  Upload,
  FileText,
  CheckCircle2,
  Cpu,
  Key,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import Navbar from '../components/Navbar';

export default function TeacherDashboard({ user, onLogout }) {
  const [exams, setExams] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('attempts'); // 'attempts' or 'exams'
  const [filterIntegrity, setFilterIntegrity] = useState('ALL');
  const [selectedAttemptForAudit, setSelectedAttemptForAudit] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  // Manual Review & Grading Modal state
  const [selectedAttemptForReview, setSelectedAttemptForReview] = useState(null);
  const [reviewAnswers, setReviewAnswers] = useState([]);
  const [reviewReferencePhoto, setReviewReferencePhoto] = useState(null);
  const [loadingReview, setLoadingReview] = useState(false);
  const [savingGradeId, setSavingGradeId] = useState(null);

  // New Exam Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newExamTitle, setNewExamTitle] = useState('');
  const [newExamSubject, setNewExamSubject] = useState('Mathematics');
  const [newExamDescription, setNewExamDescription] = useState('');
  const [newExamDuration, setNewExamDuration] = useState(25);
  const [newExamTotalMarks, setNewExamTotalMarks] = useState(25);
  const [newExamPassingMarks, setNewExamPassingMarks] = useState(12);
  const [newExamProctoring, setNewExamProctoring] = useState(true);
  const [newExamMaxTabSwitches, setNewExamMaxTabSwitches] = useState(3);
  const [isCreatingExam, setIsCreatingExam] = useState(false);

  // Document Upload & Groq Parser Modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadExamId, setUploadExamId] = useState(null);
  const [uploadExamTitle, setUploadExamTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Manual Add Question Modal state
  const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
  const [manualQuestionExamId, setManualQuestionExamId] = useState(null);
  const [manualQuestionExamTitle, setManualQuestionExamTitle] = useState('');
  const [manualQText, setManualQText] = useState('');
  const [manualQType, setManualQType] = useState('MCQ');
  const [manualQMarks, setManualQMarks] = useState(5);
  const [manualQCorrectAnswer, setManualQCorrectAnswer] = useState('');
  const [manualOptA, setManualOptA] = useState('');
  const [manualOptB, setManualOptB] = useState('');
  const [manualOptC, setManualOptC] = useState('');
  const [manualOptD, setManualOptD] = useState('');
  const [isAddingQuestion, setIsAddingQuestion] = useState(false);

  // Load instructor data
  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [examsData, attemptsData] = await Promise.all([
        apiRequest('/exams'),
        apiRequest('/attempts/overview'),
      ]);
      setExams(examsData || []);
      setAttempts(attemptsData || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch instructor dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAuditModal = async (attempt) => {
    setSelectedAttemptForAudit(attempt);
    setLoadingAudit(true);
    try {
      const events = await apiRequest(`/proctor/attempts/${attempt.attempt_id}/events`);
      setAuditEvents(events || []);
    } catch (err) {
      console.error('Error fetching audit telemetry:', err);
      setAuditEvents([]);
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleOpenReviewModal = async (attempt) => {
    setSelectedAttemptForReview(attempt);
    setLoadingReview(true);
    setReviewReferencePhoto(null);
    try {
      const data = await apiRequest(`/attempts/${attempt.attempt_id}/answers`);
      setReviewAnswers(data?.items || []);
      setReviewReferencePhoto(data?.reference_photo || null);
    } catch (err) {
      console.error('Error fetching student answers:', err);
      setReviewAnswers([]);
      setReviewReferencePhoto(null);
    } finally {
      setLoadingReview(false);
    }
  };

  const handleSaveGrade = async (questionId, newMarks, isCorrect) => {
    if (!selectedAttemptForReview) return;
    setSavingGradeId(questionId);
    try {
      const res = await apiRequest(`/attempts/${selectedAttemptForReview.attempt_id}/override-grade`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: questionId,
          marks_awarded: parseFloat(newMarks),
          is_correct: isCorrect,
        }),
      });

      // Update local review state
      setReviewAnswers((prev) =>
        prev.map((item) =>
          item.question_id === questionId
            ? { ...item, marks_awarded: parseFloat(newMarks), is_correct: isCorrect }
            : item
        )
      );

      // Refresh attempts list to show updated total score
      await fetchData();
    } catch (err) {
      alert(`Error updating grade: ${err.message}`);
    } finally {
      setSavingGradeId(null);
    }
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!newExamTitle.trim() || !newExamSubject.trim()) return;

    setIsCreatingExam(true);
    try {
      const payload = {
        title: newExamTitle.trim(),
        subject: newExamSubject.trim(),
        description: newExamDescription.trim(),
        duration_minutes: parseInt(newExamDuration, 10),
        total_marks: parseInt(newExamTotalMarks, 10),
        passing_marks: parseInt(newExamPassingMarks, 10),
        proctoring_enabled: newExamProctoring,
        auto_submit_on_violations: true,
        max_violations_threshold: 15,
        max_tab_switches_threshold: parseInt(newExamMaxTabSwitches, 10),
      };

      const created = await apiRequest('/exams', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      setNewExamTitle('');
      setNewExamDescription('');
      await fetchData();
      setActiveTab('exams');

      // Prompt to upload questions
      handleOpenUploadModal(created.id, created.title);
    } catch (err) {
      alert(`Error creating exam: ${err.message}`);
    } finally {
      setIsCreatingExam(false);
    }
  };

  const handleOpenUploadModal = (examId, title) => {
    setUploadExamId(examId);
    setUploadExamTitle(title);
    setSelectedFile(null);
    setUploadResult(null);
    setUploadError(null);
    setShowUploadModal(true);
  };

  const handleDocumentUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !uploadExamId) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('auto_save', 'true');

      const result = await apiRequest(`/exams/${uploadExamId}/upload-questions`, {
        method: 'POST',
        body: formData,
      });

      setUploadResult(result);
      await fetchData();
    } catch (err) {
      setUploadError(err.message || 'Failed to parse and upload questions');
    } finally {
      setIsUploading(false);
    }
  };

  const handleOpenAddQuestion = (examId, title) => {
    setManualQuestionExamId(examId);
    setManualQuestionExamTitle(title);
    setManualQText('');
    setManualQType('MCQ');
    setManualQMarks(5);
    setManualQCorrectAnswer('');
    setManualOptA('');
    setManualOptB('');
    setManualOptC('');
    setManualOptD('');
    setShowAddQuestionModal(true);
  };

  const handleAddQuestionSubmit = async (e) => {
    e.preventDefault();
    if (!manualQText.trim() || !manualQuestionExamId) return;

    setIsAddingQuestion(true);
    try {
      let optionsJson = null;
      if (manualQType === 'MCQ') {
        const opts = [
          { id: 'A', text: manualOptA.trim() },
          { id: 'B', text: manualOptB.trim() },
          { id: 'C', text: manualOptC.trim() },
          { id: 'D', text: manualOptD.trim() },
        ].filter((o) => o.text);
        optionsJson = JSON.stringify(opts);
      } else if (manualQType === 'TRUE_FALSE') {
        optionsJson = JSON.stringify([
          { id: 'True', text: 'True' },
          { id: 'False', text: 'False' },
        ]);
      }

      await apiRequest(`/exams/${manualQuestionExamId}/questions`, {
        method: 'POST',
        body: JSON.stringify({
          question_text: manualQText.trim(),
          question_type: manualQType,
          marks: parseInt(manualQMarks, 10),
          correct_answer: manualQCorrectAnswer.trim(),
          options_json: optionsJson,
          order_num: 1,
        }),
      });

      setShowAddQuestionModal(false);
      await fetchData();
      alert('Question added successfully!');
    } catch (err) {
      alert(`Error adding question: ${err.message}`);
    } finally {
      setIsAddingQuestion(false);
    }
  };

  // Filtered attempts
  const filteredAttempts = attempts.filter((att) => {
    if (filterIntegrity === 'ALL') return true;
    return att.integrity_status === filterIntegrity;
  });

  // Summary KPIs
  const totalSubmissions = attempts.length;
  const criticalFlags = attempts.filter(
    (a) => a.integrity_status === 'CRITICAL' || a.integrity_status === 'HIGH'
  ).length;
  const passedCount = attempts.filter((a) => a.passed).length;
  const avgScore = totalSubmissions
    ? (attempts.reduce((acc, a) => acc + (a.final_score || 0), 0) / totalSubmissions).toFixed(1)
    : '0.0';

  return (
    <div className="min-h-screen bg-canvas flex flex-col font-sans">
      <Navbar onLogout={onLogout} userName={user?.name} />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 lg:p-8 space-y-6">
        {/* Header */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-primary text-xs font-semibold">
                School Faculty Console
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-xs text-slate-500 font-mono">{user?.email}</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {user?.name || 'Instructor'} Dashboard
            </h1>
            <p className="text-xs text-slate-500">
              Curriculum authoring, document parser (PDF / Word / Excel / CSV), Groq assessment judging, and integrity verification.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              title="Refresh telemetry"
              className="p-2 border border-border rounded-lg bg-card hover:bg-slate-50 text-slate-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create School Assessment</span>
            </button>
          </div>
        </div>

        {/* Aggregate KPI Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-4 space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-between">
              <span>School Subjects</span>
              <BookOpen className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{exams.length}</div>
            <div className="text-[11px] text-slate-500">Active exam suites</div>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-between">
              <span>Student Submissions</span>
              <Users className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{totalSubmissions}</div>
            <div className="text-[11px] text-slate-500">Completed attempts</div>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-between">
              <span>Proctoring Alerts</span>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-amber-600 font-mono">{criticalFlags}</div>
            <div className="text-[11px] text-slate-500">High / Critical risk</div>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-between">
              <span>Student Pass Rate</span>
              <Award className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-emerald-600 font-mono">
              {totalSubmissions ? `${Math.round((passedCount / totalSubmissions) * 100)}%` : '0%'}
            </div>
            <div className="text-[11px] text-slate-500">Avg score: {avgScore} pts</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('attempts')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'attempts'
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-card text-slate-600 hover:text-slate-900 border border-border'
              }`}
            >
              Student Attempts & Integrity Audit ({attempts.length})
            </button>
            <button
              onClick={() => setActiveTab('exams')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'exams'
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-card text-slate-600 hover:text-slate-900 border border-border'
              }`}
            >
              School Subject Suites ({exams.length})
            </button>
          </div>

          {activeTab === 'attempts' && (
            <div className="flex items-center gap-2 text-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500">Risk Filter:</span>
              <select
                value={filterIntegrity}
                onChange={(e) => setFilterIntegrity(e.target.value)}
                className="bg-card border border-border rounded px-2 py-1 text-xs text-slate-700 font-medium focus:outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="LOW">Low Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="CRITICAL">Critical Risk</option>
              </select>
            </div>
          )}
        </div>

        {/* Tab 1: Student Attempts */}
        {activeTab === 'attempts' && (
          <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Student Attempts Log</h3>
                <p className="text-xs text-slate-500">
                  Comprehensive audit traces including server-verified scores, tab switches, and AI proctoring scores.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">{filteredAttempts.length} records</span>
            </div>

            {isLoading ? (
              <div className="p-8 text-center text-xs text-slate-500">Loading student attempts...</div>
            ) : filteredAttempts.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-xs">
                No examination attempts match the selected filter.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-border text-slate-600 uppercase font-semibold tracking-wider text-[10px]">
                    <tr>
                      <th className="px-5 py-3">Student</th>
                      <th className="px-4 py-3">Subject & Exam</th>
                      <th className="px-3 py-3">Score</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3">Tab Switches</th>
                      <th className="px-3 py-3">Integrity Risk</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-slate-700">
                    {filteredAttempts.map((att) => {
                      const isCritical = att.integrity_status === 'CRITICAL' || att.integrity_status === 'HIGH';
                      const isMedium = att.integrity_status === 'MEDIUM';

                      return (
                        <tr key={att.attempt_id} className="hover:bg-slate-50/60 transition-colors">
                          <td className="px-5 py-3.5">
                            <div className="font-semibold text-slate-900">{att.student_name}</div>
                            <div className="text-[10px] text-slate-400 font-mono">Attempt #{att.attempt_id}</div>
                          </td>

                          <td className="px-4 py-3.5">
                            <div className="font-medium text-slate-800">{att.exam_title}</div>
                            <div className="text-[10px] text-slate-400">
                              {att.answered_count} of {att.total_questions} answered
                            </div>
                          </td>

                          <td className="px-3 py-3.5 font-mono">
                            <div className="font-bold text-slate-900">
                              {att.final_score} / {att.total_marks}
                            </div>
                            <div className="text-[10px] text-slate-500">
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
                                  : att.status === 'TERMINATED_VIOLATION'
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : 'bg-amber-50 text-amber-700 border-amber-200'
                              }`}
                            >
                              {att.status}
                            </span>
                            {att.termination_reason && (
                              <div className="text-[10px] text-rose-600 truncate max-w-[150px]" title={att.termination_reason}>
                                {att.termination_reason}
                              </div>
                            )}
                          </td>

                          <td className="px-3 py-3.5 font-mono">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                att.tab_switch_count > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'text-slate-600'
                              }`}
                            >
                              {att.tab_switch_count} switches
                            </span>
                          </td>

                          <td className="px-3 py-3.5">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                                isCritical
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : isMedium
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              }`}
                            >
                              {att.integrity_status} ({att.suspicious_score} pts)
                            </span>
                          </td>

                          <td className="px-4 py-3.5 text-right space-x-2">
                            <button
                              onClick={() => handleOpenReviewModal(att)}
                              className="px-3 py-1 rounded bg-indigo-50 hover:bg-indigo-100 text-primary border border-indigo-200 font-semibold text-[11px] inline-flex items-center gap-1 transition-colors"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                              <span>Check & Grade</span>
                            </button>
                            <button
                              onClick={() => handleOpenAuditModal(att)}
                              className="px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] inline-flex items-center gap-1 transition-colors"
                            >
                              <Eye className="w-3.5 h-3.5 text-slate-500" />
                              <span>Audit Events</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: School Subject Suites */}
        {activeTab === 'exams' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Configured School Subject Assessments</h3>
                <p className="text-xs text-slate-500">Upload question sheets directly from PDF/Word/Excel or author manually.</p>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Subject Exam</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {exams.map((ex) => (
                <div
                  key={ex.id}
                  className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-primary font-semibold text-[10px] uppercase">
                        {ex.subject}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">{ex.question_count} Questions</span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900">{ex.title}</h4>
                    <p className="text-xs text-slate-500 line-clamp-2">
                      {ex.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="space-y-3 pt-3 border-t border-border/60">
                    <div className="space-y-1.5 text-xs">
                      <div className="flex items-center justify-between text-slate-600">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-400" /> Duration:
                        </span>
                        <span className="font-semibold font-mono text-slate-900">{ex.duration_minutes} mins</span>
                      </div>

                      <div className="flex items-center justify-between text-slate-600">
                        <span className="flex items-center gap-1">
                          <Award className="w-3.5 h-3.5 text-slate-400" /> Marks:
                        </span>
                        <span className="font-semibold font-mono text-slate-900">
                          {ex.total_marks} (Pass: {ex.passing_marks})
                        </span>
                      </div>
                    </div>

                    {/* Actions Grid */}
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleOpenUploadModal(ex.id, ex.title)}
                        className="py-2 px-2.5 rounded-lg border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-100/60 text-primary font-semibold text-[11px] flex items-center justify-center gap-1 transition-colors"
                      >
                        <Upload className="w-3.5 h-3.5" />
                        <span>Upload Sheet</span>
                      </button>

                      <button
                        onClick={() => handleOpenAddQuestion(ex.id, ex.title)}
                        className="py-2 px-2.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-[11px] flex items-center justify-center gap-1 transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5 text-slate-500" />
                        <span>Add Question</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Document Upload & Parser Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Upload & Parse Question Document</h3>
                <p className="text-xs text-slate-500">
                  Target Exam: <span className="font-semibold text-slate-800">{uploadExamTitle}</span>
                </p>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-1 rounded hover:bg-slate-100 text-slate-500 text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <form onSubmit={handleDocumentUpload} className="space-y-4 text-xs">
              {/* File Select */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Select Question Paper (PDF, Word .docx, Excel .xlsx, CSV, TXT)
                </label>
                <div className="border-2 border-dashed border-border rounded-xl p-4 text-center hover:bg-slate-50 transition-colors">
                  <input
                    type="file"
                    required
                    accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt"
                    onChange={(e) => setSelectedFile(e.target.files[0])}
                    className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-hover"
                  />
                  {selectedFile && (
                    <div className="mt-2 text-slate-700 font-semibold flex items-center justify-center gap-1 text-[11px]">
                      <FileText className="w-3.5 h-3.5 text-primary" />
                      <span>{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Error Display */}
              {uploadError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                  {uploadError}
                </div>
              )}

              {/* Success Result Display */}
              {uploadResult && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Success: {uploadResult.questions_saved} Questions Extracted & Added</span>
                  </div>
                  <p className="text-[11px] text-emerald-700">
                    Questions are now live in this examination suite.
                  </p>
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-3 py-1.5 rounded border border-border bg-card text-slate-700 font-semibold"
                >
                  Done
                </button>
                <button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="px-4 py-1.5 rounded bg-primary hover:bg-primary-hover text-white font-semibold disabled:opacity-60 flex items-center gap-1.5"
                >
                  {isUploading ? 'Parsing Document...' : 'Parse & Save Questions'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Audit Telemetry Modal */}
      {selectedAttemptForAudit && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Attempt Audit Trail — #{selectedAttemptForAudit.attempt_id}
                </h3>
                <p className="text-xs text-slate-500">
                  Candidate: <span className="font-semibold text-slate-800">{selectedAttemptForAudit.student_name}</span> •{' '}
                  Exam: <span className="font-semibold text-slate-800">{selectedAttemptForAudit.exam_title}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedAttemptForAudit(null)}
                className="p-1 rounded hover:bg-slate-200 text-slate-500 text-sm font-semibold"
              >
                Close
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              <div className="grid grid-cols-3 gap-3 bg-slate-50 border border-border rounded-lg p-3 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Integrity Status</div>
                  <div className="font-bold text-slate-900">{selectedAttemptForAudit.integrity_status}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Anomaly Score</div>
                  <div className="font-bold text-slate-900 font-mono">
                    {selectedAttemptForAudit.suspicious_score} points
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Tab Switches</div>
                  <div className="font-bold text-slate-900 font-mono">
                    {selectedAttemptForAudit.tab_switch_count} recorded
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wider">
                  Chronological Telemetry Events
                </h4>

                {loadingAudit ? (
                  <div className="py-8 text-center text-xs text-slate-500">Loading telemetry events...</div>
                ) : auditEvents.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-500 border border-dashed border-border rounded-lg">
                    No violation events logged for this session. Candidate maintained continuous integrity compliance.
                  </div>
                ) : (
                  <div className="border border-border rounded-lg divide-y divide-border overflow-hidden">
                    {auditEvents.map((evt) => (
                      <div key={evt.id} className="p-3 text-xs flex items-center justify-between hover:bg-slate-50">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-900">{evt.event_type}</span>
                            <span className="px-1.5 py-0.2 rounded bg-rose-50 text-rose-700 text-[10px] font-semibold border border-rose-200">
                              +{evt.points} pts
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono">
                            {new Date(evt.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        <div className="text-[11px] text-slate-600 max-w-xs text-right font-mono truncate">
                          {evt.metadata_json || 'System logged event'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 py-3 border-t border-border bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedAttemptForAudit(null)}
                className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold"
              >
                Dismiss Audit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Check & Grade Assessment Modal */}
      {selectedAttemptForReview && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-3xl w-full max-h-[88vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Manual Paper Evaluation & Grading — Attempt #{selectedAttemptForReview.attempt_id}
                </h3>
                <p className="text-xs text-slate-500">
                  Student: <span className="font-semibold text-slate-800">{selectedAttemptForReview.student_name}</span> •{' '}
                  Subject/Exam: <span className="font-semibold text-slate-800">{selectedAttemptForReview.exam_title}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-bold text-slate-800 bg-white border border-border px-2.5 py-1 rounded">
                  Current Score: {selectedAttemptForReview.final_score} / {selectedAttemptForReview.total_marks}
                </span>
                <button
                  onClick={() => setSelectedAttemptForReview(null)}
                  className="p-1 rounded hover:bg-slate-200 text-slate-500 text-xs font-semibold"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {reviewReferencePhoto && (
                <div className="flex items-center gap-4 p-3 bg-slate-50 border border-border rounded-xl">
                  <img
                    src={reviewReferencePhoto}
                    alt="Verified Candidate Baseline"
                    className="w-14 h-14 object-cover rounded-lg border border-slate-300 shadow-2xs shrink-0"
                  />
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Verified Pre-Flight Biometric Photograph</span>
                    </span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Captured during pre-exam system calibration. Used as the authoritative baseline for continuous face matching throughout the test.
                    </p>
                  </div>
                </div>
              )}

              {loadingReview ? (
                <div className="py-12 text-center text-xs text-slate-500">Loading student answers...</div>
              ) : reviewAnswers.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500 border border-dashed border-border rounded-lg">
                  No submitted answers found for this attempt.
                </div>
              ) : (
                <div className="space-y-4">
                  {reviewAnswers.map((item, idx) => (
                    <div
                      key={item.question_id}
                      className="border border-border rounded-xl p-4 bg-white shadow-xs space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[10px] font-bold text-slate-500 px-1.5 py-0.5 rounded bg-slate-100">
                              Q{item.order_num || idx + 1}
                            </span>
                            <span className="text-[10px] uppercase font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                              {item.question_type}
                            </span>
                            <span className="text-[10px] text-slate-400">Max: {item.max_marks} marks</span>
                          </div>
                          <div className="text-xs font-semibold text-slate-900">{item.question_text}</div>
                        </div>

                        {/* Grade Controls */}
                        <div className="flex items-center gap-2 shrink-0 bg-slate-50 p-1.5 rounded-lg border border-border text-xs">
                          <span className="text-[11px] text-slate-500 font-medium">Marks:</span>
                          <input
                            type="number"
                            step="0.5"
                            min="0"
                            max={item.max_marks}
                            defaultValue={item.marks_awarded}
                            id={`marks_input_${item.question_id}`}
                            className="w-14 px-1.5 py-0.5 border border-border rounded text-center font-mono font-bold text-slate-800 bg-white"
                          />
                          <button
                            onClick={() => {
                              const input = document.getElementById(`marks_input_${item.question_id}`);
                              const val = parseFloat(input?.value || 0);
                              handleSaveGrade(item.question_id, val, val > 0);
                            }}
                            disabled={savingGradeId === item.question_id}
                            className="px-2.5 py-1 rounded bg-primary hover:bg-primary-hover text-white text-[11px] font-semibold disabled:opacity-60"
                          >
                            {savingGradeId === item.question_id ? 'Saving...' : 'Update'}
                          </button>
                        </div>
                      </div>

                      {/* Reference Answer */}
                      {item.correct_answer && (
                        <div className="p-2.5 rounded bg-emerald-50/60 border border-emerald-100 text-xs">
                          <span className="font-semibold text-emerald-900 block text-[10px] uppercase">
                            Reference / Expected Answer:
                          </span>
                          <span className="text-emerald-800 font-mono text-[11px]">{item.correct_answer}</span>
                        </div>
                      )}

                      {/* Student Submitted Answer */}
                      <div className="p-2.5 rounded bg-slate-50 border border-border text-xs space-y-1">
                        <span className="font-semibold text-slate-600 block text-[10px] uppercase">
                          Student's Submitted Response:
                        </span>
                        <div className="text-slate-900 font-mono text-[11px] whitespace-pre-wrap">
                          {item.submitted_answer || '(Student left this question blank)'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="px-6 py-3 border-t border-border bg-slate-50 flex justify-between items-center">
              <span className="text-xs text-slate-500">
                Teacher adjustments recalculate final scores and pass/fail status immediately.
              </span>
              <button
                onClick={() => setSelectedAttemptForReview(null)}
                className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold"
              >
                Done Reviewing
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create New Examination Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Create School Subject Assessment</h3>
              <p className="text-xs text-slate-500">Configure curriculum parameters for school students.</p>
            </div>

            <form onSubmit={handleCreateExam} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Assessment Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Class 7 Fractions & Decimals Quiz"
                  value={newExamTitle}
                  onChange={(e) => setNewExamTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Subject</label>
                  <select
                    value={newExamSubject}
                    onChange={(e) => setNewExamSubject(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  >
                    <option value="Mathematics">Mathematics</option>
                    <option value="Science">Science</option>
                    <option value="English & Grammar">English & Grammar</option>
                    <option value="Computer & Programming">Computer & Programming</option>
                    <option value="Social Studies">Social Studies</option>
                    <option value="General Knowledge">General Knowledge</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Duration (Mins)</label>
                  <input
                    type="number"
                    min="5"
                    max="180"
                    value={newExamDuration}
                    onChange={(e) => setNewExamDuration(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Total Marks</label>
                  <input
                    type="number"
                    min="5"
                    max="200"
                    value={newExamTotalMarks}
                    onChange={(e) => setNewExamTotalMarks(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Passing Marks</label>
                  <input
                    type="number"
                    min="1"
                    max={newExamTotalMarks}
                    value={newExamPassingMarks}
                    onChange={(e) => setNewExamPassingMarks(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Max Tab Switches Allowed</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={newExamMaxTabSwitches}
                  onChange={(e) => setNewExamMaxTabSwitches(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description / Syllabus</label>
                <textarea
                  rows="2"
                  placeholder="Topics covered, reference chapters, instructions..."
                  value={newExamDescription}
                  onChange={(e) => setNewExamDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded border border-border bg-card text-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingExam}
                  className="px-4 py-1.5 rounded bg-primary hover:bg-primary-hover text-white font-semibold disabled:opacity-60"
                >
                  {isCreatingExam ? 'Creating...' : 'Publish Assessment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manual Add Question Modal */}
      {showAddQuestionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Add Question to Assessment</h3>
                <p className="text-xs text-slate-500">
                  Target: <span className="font-semibold text-slate-800">{manualQuestionExamTitle}</span>
                </p>
              </div>
              <button
                onClick={() => setShowAddQuestionModal(false)}
                className="p-1 rounded hover:bg-slate-100 text-slate-500 text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <form onSubmit={handleAddQuestionSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Question Type</label>
                <select
                  value={manualQType}
                  onChange={(e) => setManualQType(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                >
                  <option value="MCQ">Multiple Choice (MCQ)</option>
                  <option value="TRUE_FALSE">True / False</option>
                  <option value="SHORT_ANSWER">Short Answer / Step Working</option>
                  <option value="CODING">Computer / Coding Question</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Question Text</label>
                <textarea
                  rows="3"
                  required
                  placeholder="Type the question text or math problem..."
                  value={manualQText}
                  onChange={(e) => setManualQText(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                />
              </div>

              {/* Options for MCQ */}
              {manualQType === 'MCQ' && (
                <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-border">
                  <span className="font-semibold text-slate-700 block text-[11px]">Answer Choices:</span>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="Option A"
                      value={manualOptA}
                      onChange={(e) => setManualOptA(e.target.value)}
                      className="px-2.5 py-1.5 border border-border rounded bg-white"
                    />
                    <input
                      type="text"
                      placeholder="Option B"
                      value={manualOptB}
                      onChange={(e) => setManualOptB(e.target.value)}
                      className="px-2.5 py-1.5 border border-border rounded bg-white"
                    />
                    <input
                      type="text"
                      placeholder="Option C"
                      value={manualOptC}
                      onChange={(e) => setManualOptC(e.target.value)}
                      className="px-2.5 py-1.5 border border-border rounded bg-white"
                    />
                    <input
                      type="text"
                      placeholder="Option D"
                      value={manualOptD}
                      onChange={(e) => setManualOptD(e.target.value)}
                      className="px-2.5 py-1.5 border border-border rounded bg-white"
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Correct Answer / Key</label>
                  <input
                    type="text"
                    required
                    placeholder={manualQType === 'MCQ' ? 'e.g. A or B' : 'Reference solution'}
                    value={manualQCorrectAnswer}
                    onChange={(e) => setManualQCorrectAnswer(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Marks</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={manualQMarks}
                    onChange={(e) => setManualQMarks(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-card text-slate-800 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddQuestionModal(false)}
                  className="px-3 py-1.5 rounded border border-border bg-card text-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAddingQuestion}
                  className="px-4 py-1.5 rounded bg-primary hover:bg-primary-hover text-white font-semibold disabled:opacity-60"
                >
                  {isAddingQuestion ? 'Adding Question...' : 'Save Question'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
