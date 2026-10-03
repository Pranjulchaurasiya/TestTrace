import React from 'react';
import { Check, CheckCircle2, FileCode, HelpCircle, Layers } from 'lucide-react';

export default function QuestionPanel({
  questions = [],
  currentIndex = 0,
  onSelectQuestion,
  answers = {},
  onSelectOption,
}) {
  const currentQ = questions[currentIndex];
  if (!currentQ) {
    return <div className="p-6 text-slate-500 text-sm">No questions available.</div>;
  }

  // Parse options if present
  let options = [];
  if (currentQ.options_json) {
    try {
      options = JSON.parse(currentQ.options_json);
    } catch {
      options = [];
    }
  }

  const currentAnswer = answers[currentQ.id]?.submitted_answer || '';

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-lg overflow-hidden shadow-xs">
      {/* Question Index Matrix Drawer */}
      <div className="p-3 border-b border-border bg-slate-50/70">
        <div className="flex items-center justify-between text-xs text-slate-600 mb-2">
          <span className="font-semibold text-slate-800">Question Matrix</span>
          <span className="font-mono text-slate-500">
            {Object.keys(answers).length} / {questions.length} Answered
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {questions.map((q, idx) => {
            const isAnswered = !!answers[q.id]?.submitted_answer;
            const isCurrent = idx === currentIndex;

            let btnStyle = 'bg-slate-100 text-slate-600 hover:bg-slate-200 border-transparent';
            if (isAnswered) {
              btnStyle = 'bg-slate-900 text-white font-medium';
            }
            if (isCurrent) {
              btnStyle = 'border-2 border-primary text-primary font-bold bg-white';
            }

            return (
              <button
                key={q.id}
                onClick={() => onSelectQuestion(idx)}
                className={`w-7 h-7 rounded text-xs font-mono transition-all flex items-center justify-center border ${btnStyle}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Question Body */}
      <div className="p-4 lg:p-5 overflow-y-auto flex-1 custom-scrollbar space-y-4">
        {/* Header Tags */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase tracking-wider bg-slate-100 text-slate-800 border border-slate-200">
              {currentQ.question_type}
            </span>
            <span className="text-xs font-semibold text-slate-500">
              Question {currentIndex + 1} of {questions.length}
            </span>
          </div>
          <span className="text-xs font-mono font-semibold text-primary bg-primary-light px-2.5 py-0.5 rounded border border-primary/20">
            {currentQ.marks} Marks
          </span>
        </div>

        {/* Question Text */}
        <div className="text-slate-900 text-sm leading-relaxed whitespace-pre-wrap font-medium">
          {currentQ.question_text}
        </div>

        {/* MCQ / TRUE_FALSE Selection Tiles */}
        {options.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Select Option:</div>
            {options.map((opt) => {
              const isSelected = currentAnswer.toUpperCase() === opt.id.toUpperCase();

              return (
                <div
                  key={opt.id}
                  onClick={() => onSelectOption(currentQ.id, opt.id)}
                  className={`p-3 rounded border cursor-pointer transition-all flex items-center justify-between ${
                    isSelected
                      ? 'border-primary bg-primary-light text-primary font-semibold shadow-xs'
                      : 'border-border bg-white hover:bg-slate-50 text-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-6 h-6 rounded flex items-center justify-center text-xs font-mono font-bold ${
                        isSelected ? 'bg-primary text-white' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {opt.id}
                    </span>
                    <span className="text-sm">{opt.text}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-primary" />}
                </div>
              );
            })}
          </div>
        )}

        {/* Coding Public Test Cases Accordion */}
        {currentQ.public_test_cases && currentQ.public_test_cases.length > 0 && (
          <div className="pt-3 border-t border-border space-y-2">
            <div className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <FileCode className="w-3.5 h-3.5 text-primary" />
              <span>Public Verification Test Cases:</span>
            </div>

            <div className="space-y-1.5 font-mono text-xs">
              {currentQ.public_test_cases.map((tc, idx) => (
                <div key={idx} className="p-2.5 rounded bg-slate-50 border border-border">
                  <div className="text-slate-500 text-[11px] mb-1 font-semibold">Test Case #{idx + 1}</div>
                  <div className="text-slate-700">
                    <span className="text-slate-400">Input:</span> {tc.input}
                  </div>
                  <div className="text-slate-700">
                    <span className="text-slate-400">Expected:</span> {tc.expected_output}
                  </div>
                </div>
              ))}
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              Private verification cases remain encrypted until evaluation.
            </div>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="p-3 bg-slate-50 border-t border-border flex items-center justify-between">
        <button
          onClick={() => onSelectQuestion(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
          className="px-3 py-1.5 rounded text-xs font-semibold bg-white border border-border text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition-colors"
        >
          Previous
        </button>

        <span className="text-xs font-mono text-slate-500">
          {currentIndex + 1} / {questions.length}
        </span>

        <button
          onClick={() => onSelectQuestion(Math.min(questions.length - 1, currentIndex + 1))}
          disabled={currentIndex === questions.length - 1}
          className="px-3 py-1.5 rounded text-xs font-semibold bg-white border border-border text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
