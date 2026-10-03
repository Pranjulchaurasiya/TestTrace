import React, { useState, useEffect } from 'react';
import { Timer, ShieldCheck, Send } from 'lucide-react';

export default function MiniVivaCard({
  prompts = [],
  onSubmitViva,
  isSubmitted = false,
}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [explanation, setExplanation] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(180);

  const activePrompt = prompts[currentIndex];

  useEffect(() => {
    if (!activePrompt || isSubmitted) return;
    setSecondsLeft(activePrompt.timer_seconds || 180);

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [activePrompt, isSubmitted]);

  if (!activePrompt) return null;

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleSubmit = () => {
    if (!explanation.trim()) return;
    onSubmitViva({
      prompt_index: currentIndex,
      prompt_text: activePrompt.prompt,
      student_explanation: explanation,
      response_time_seconds: (activePrompt.timer_seconds || 180) - secondsLeft,
    });
    setExplanation('');
    if (currentIndex + 1 < prompts.length) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  return (
    <div className="bg-card border-2 border-indigo-200 rounded-lg p-3.5 shadow-xs bg-indigo-50/20 flex flex-col gap-2.5">
      <div className="flex items-center justify-between pb-2 border-indigo-100">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary" />
          <span className="text-xs font-bold text-slate-900 tracking-tight">
            AI-Resistant Mini-Viva Verification Step
          </span>
        </div>

        <div
          className={`flex items-center gap-1 font-mono text-xs font-bold px-2 py-0.5 rounded border ${
            secondsLeft <= 30
              ? 'bg-danger-light text-danger border-danger-border animate-pulse'
              : 'bg-primary-light text-primary border-primary/20'
          }`}
        >
          <Timer className="w-3.5 h-3.5" />
          <span>{formatTimer(secondsLeft)} remaining</span>
        </div>
      </div>

      <div className="text-xs font-medium text-slate-800 leading-snug">
        <span className="font-bold text-primary">Prompt {currentIndex + 1} of {prompts.length}: </span>
        {activePrompt.prompt}
      </div>

      <div className="space-y-2">
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          disabled={secondsLeft === 0 || isSubmitted}
          rows={2}
          placeholder="Type your rapid explanation here..."
          className="w-full text-xs font-sans p-2 rounded border border-border bg-white text-slate-900 focus:outline-none focus:border-primary resize-none"
        />

        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono text-slate-400">
            {explanation.trim().split(/\s+/).filter(Boolean).length} words
          </span>

          <button
            onClick={handleSubmit}
            disabled={!explanation.trim() || secondsLeft === 0 || isSubmitted}
            className="px-3 py-1 rounded bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-xs transition-colors flex items-center gap-1 disabled:opacity-40"
          >
            <Send className="w-3 h-3" />
            <span>Submit Viva</span>
          </button>
        </div>
      </div>
    </div>
  );
}
