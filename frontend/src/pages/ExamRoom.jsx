import React, { useEffect, useState, useRef, useCallback } from 'react';
import Navbar from '../components/Navbar';
import QuestionPanel from '../components/QuestionPanel';
import CodeEditor from '../components/CodeEditor';
import MiniVivaCard from '../components/MiniVivaCard';
import ProctorHUD from '../components/ProctorHUD';
import { apiRequest } from '../services/api';

export default function ExamRoom({ examId, onExamCompleted }) {
  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [codeAnswers, setCodeAnswers] = useState({});
  const [remainingSeconds, setRemainingSeconds] = useState(1800);
  const [violationsCount, setViolationsCount] = useState(0);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Initialize Exam Attempt
  useEffect(() => {
    async function initExam() {
      try {
        // Request fullscreen mode
        if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen().catch(() => {});
        }

        const startData = await apiRequest(`/attempts/exams/${examId}/start`, {
          method: 'POST',
        });
        setAttempt(startData);
        setRemainingSeconds(startData.remaining_seconds);

        const qData = await apiRequest(`/attempts/${startData.attempt_id}/questions`);
        setQuestions(qData);

        // Preload starter codes
        const initialCode = {};
        qData.forEach((q) => {
          if (q.starter_code) {
            initialCode[q.id] = q.starter_code;
          }
        });
        setCodeAnswers(initialCode);
      } catch (err) {
        setErrorMessage(err.message || 'Failed to initialize examination session.');
      }
    }
    initExam();
  }, [examId]);

  // Server-authoritative timer countdown and periodic sync
  useEffect(() => {
    if (!attempt) return;

    // Local 1-second interval
    const localTimer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(localTimer);
          handleFinalSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // 25-second server synchronization check
    const syncTimer = setInterval(async () => {
      try {
        const syncData = await apiRequest(`/attempts/${attempt.attempt_id}/time-sync`);
        setRemainingSeconds(syncData.remaining_seconds);
        if (syncData.is_expired) {
          clearInterval(localTimer);
          clearInterval(syncTimer);
          handleFinalSubmit();
        }
      } catch (err) {
        // Ignore transient sync error
      }
    }, 25000);

    return () => {
      clearInterval(localTimer);
      clearInterval(syncTimer);
    };
  }, [attempt]);

  // Handle MCQ/Option selection
  const handleSelectOption = async (questionId, optionId) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { submitted_answer: optionId },
    }));

    if (!attempt) return;
    try {
      await apiRequest(`/attempts/${attempt.attempt_id}/answer`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: questionId,
          submitted_answer: optionId,
        }),
      });
    } catch (err) {
      console.error('Failed to save answer:', err);
    }
  };

  // Handle Code Saving
  const handleSaveCode = async () => {
    const currentQ = questions[currentIndex];
    if (!currentQ || !attempt) return;

    const code = codeAnswers[currentQ.id] || '';
    setAnswers((prev) => ({
      ...prev,
      [currentQ.id]: { submitted_answer: code },
    }));

    try {
      await apiRequest(`/attempts/${attempt.attempt_id}/answer`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: currentQ.id,
          submitted_answer: code,
          execution_output: 'Saved candidate code.',
        }),
      });
      alert('Solution saved successfully.');
    } catch (err) {
      alert(`Save error: ${err.message}`);
    }
  };

  // Handle Mini-Viva Submission
  const handleSubmitViva = async (vivaData) => {
    const currentQ = questions[currentIndex];
    if (!currentQ || !attempt) return;

    try {
      await apiRequest(`/attempts/${attempt.attempt_id}/viva-explanation`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: currentQ.id,
          prompt_index: vivaData.prompt_index,
          prompt_text: vivaData.prompt_text,
          student_explanation: vivaData.student_explanation,
          response_time_seconds: vivaData.response_time_seconds,
        }),
      });
    } catch (err) {
      console.error('Failed to record viva explanation:', err);
    }
  };

  // Final Exam Submission
  const handleFinalSubmit = async () => {
    if (!attempt || isSubmitting) return;
    setIsSubmitting(true);

    try {
      const resultData = await apiRequest(`/attempts/${attempt.attempt_id}/submit`, {
        method: 'POST',
      });
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      if (onExamCompleted) {
        onExamCompleted(resultData);
      }
    } catch (err) {
      alert(`Submission error: ${err.message}`);
      setIsSubmitting(false);
    }
  };

  const currentQ = questions[currentIndex];
  const isCodingQuestion =
    currentQ && (currentQ.question_type === 'CODING' || currentQ.question_type === 'DEBUGGING');

  if (errorMessage) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
        <div className="bg-card border border-border p-6 rounded-xl max-w-md w-full space-y-4 text-center">
          <div className="text-sm font-semibold text-danger">{errorMessage}</div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-white text-xs font-semibold rounded"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!attempt || questions.length === 0) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center text-slate-500 text-sm">
        Initializing secure examination workspace...
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-canvas overflow-hidden">
      {/* Top Authoritative Header */}
      <Navbar
        examTitle={attempt.title}
        subject={attempt.subject}
        remainingSeconds={remainingSeconds}
        violationsCount={violationsCount}
        onSubmitExam={handleFinalSubmit}
        isSubmitting={isSubmitting}
      />

      {/* Main Split Bento Layout */}
      <div className="flex-1 p-3 lg:p-4 grid grid-cols-1 lg:grid-cols-12 gap-3 lg:gap-4 overflow-hidden">
        {/* Left Column: Question Matrix & Problem Description */}
        <div className="lg:col-span-5 h-full overflow-hidden flex flex-col">
          <QuestionPanel
            questions={questions}
            currentIndex={currentIndex}
            onSelectQuestion={setCurrentIndex}
            answers={answers}
            onSelectOption={handleSelectOption}
          />
        </div>

        {/* Right Column: Code Editor & Mini-Viva Follow-up */}
        <div className="lg:col-span-7 h-full overflow-y-auto custom-scrollbar flex flex-col gap-3 pr-1 pb-20">
          {isCodingQuestion ? (
            <>
              <div className="min-h-[420px] flex-1 flex flex-col">
                <CodeEditor
                  starterCode={currentQ.starter_code || ''}
                  code={codeAnswers[currentQ.id] || ''}
                  onChangeCode={(newCode) =>
                    setCodeAnswers((prev) => ({ ...prev, [currentQ.id]: newCode }))
                  }
                  onSaveAnswer={handleSaveCode}
                  language={currentQ.coding_language || 'python'}
                />
              </div>

              {/* Rapid Mini-Viva Follow-up */}
              {currentQ.explanation_prompts && currentQ.explanation_prompts.length > 0 && (
                <div className="shrink-0 pt-1">
                  <MiniVivaCard
                    prompts={currentQ.explanation_prompts}
                    onSubmitViva={handleSubmitViva}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 bg-card border border-border rounded-lg p-6 flex flex-col justify-center items-center text-center space-y-3">
              <div className="text-sm font-semibold text-slate-800">
                Multiple Choice / Theoretical Assessment
              </div>
              <p className="text-xs text-slate-500 max-w-md leading-relaxed">
                Please select your chosen response directly on the question card in the left panel. Your answers are auto-saved to the server upon selection.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Floating Biometric & Integrity Proctor HUD */}
      <ProctorHUD
        attemptId={attempt.attempt_id}
        tabSwitches={tabSwitches}
        isFloating={true}
        onViolationOccurred={(res) => {
          setViolationsCount(res.total_suspicious_score);
          if (res.tab_switch_count !== undefined) {
            setTabSwitches(res.tab_switch_count);
          }
        }}
        onExamTerminated={(reason) => {
          alert(`Examination Terminated: ${reason}`);
          handleFinalSubmit();
        }}
      />
    </div>
  );
}
