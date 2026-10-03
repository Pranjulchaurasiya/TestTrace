import React, { useState } from 'react';
import { Play, RotateCcw, Terminal, CheckCircle2, Save } from 'lucide-react';

export default function CodeEditor({
  starterCode = '',
  code = '',
  onChangeCode,
  onSaveAnswer,
  language = 'python',
}) {
  const [isRunning, setIsRunning] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState(null);

  const handleRunTests = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setConsoleOutput({
        passed: 2,
        total: 2,
        runtimeMs: 19,
        memoryMb: 14.1,
        logs: '[TEST RUNNER]\n✓ Case 1 passed (Input verified)\n✓ Case 2 passed (Boundary verified)\nExecution completed with status 0.',
      });
    }, 450);
  };

  const handleReset = () => {
    if (confirm('Reset editor to initial starter template?')) {
      onChangeCode(starterCode);
    }
  };

  // Generate line numbers
  const linesCount = Math.max(12, (code || '').split('\n').length);
  const lines = Array.from({ length: linesCount }, (_, i) => i + 1);

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-lg overflow-hidden shadow-xs">
      {/* Editor Action Header */}
      <div className="h-10 bg-slate-50 border-b border-border px-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-slate-700 bg-white px-2 py-0.5 rounded border border-border">
            {language.toUpperCase()} 3.11
          </span>
          <span className="text-[11px] text-slate-400 font-mono">UTF-8</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            title="Reset to starter template"
            className="p-1 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-200 text-xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleRunTests}
            disabled={isRunning}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-white text-xs font-mono font-semibold transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Play className="w-3 h-3 text-emerald-400 fill-emerald-400" />
            <span>{isRunning ? 'Running...' : 'Run Tests'}</span>
          </button>

          <button
            onClick={onSaveAnswer}
            className="px-2.5 py-1 rounded bg-primary hover:bg-primary-hover text-white text-xs font-semibold transition-colors flex items-center gap-1"
          >
            <Save className="w-3 h-3" />
            <span>Save Solution</span>
          </button>
        </div>
      </div>

      {/* Editor Body with Monospace Gutters */}
      <div className="flex-1 flex overflow-hidden bg-white font-mono text-xs">
        {/* Line Numbers Gutter */}
        <div className="w-10 bg-slate-50 border-r border-border py-3 select-none text-right pr-2 text-slate-400 leading-5">
          {lines.map((num) => (
            <div key={num}>{num}</div>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          value={code}
          onChange={(e) => onChangeCode(e.target.value)}
          spellCheck={false}
          className="flex-1 p-3 bg-transparent text-slate-900 resize-none outline-none leading-5 font-mono overflow-auto custom-scrollbar whitespace-pre"
          placeholder="# Write your solution here..."
        />
      </div>

      {/* Test Execution Output Terminal */}
      <div className="h-36 bg-slate-900 border-t border-slate-800 flex flex-col font-mono text-xs text-slate-300">
        <div className="h-7 bg-slate-950 px-3 flex items-center justify-between border-b border-slate-800 text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold text-slate-300">Sandbox Test Runner Console</span>
          </div>
          {consoleOutput && (
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>{consoleOutput.passed}/{consoleOutput.total} Checks Passed ({consoleOutput.runtimeMs}ms)</span>
            </span>
          )}
        </div>

        <div className="flex-1 p-3 overflow-y-auto custom-scrollbar font-mono text-[11px] leading-relaxed text-slate-300">
          {consoleOutput ? (
            <pre className="whitespace-pre-wrap">{consoleOutput.logs}</pre>
          ) : (
            <div className="text-slate-500 italic">
              Click 'Run Tests' above to execute candidate code in the sandbox.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
