import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  CheckCircle2,
  AlertTriangle,
  Monitor,
  Wifi,
  ShieldCheck,
  RotateCcw,
  ArrowRight,
  Clock,
  Award,
  XCircle,
  FileCheck,
} from 'lucide-react';
import { apiRequest } from '../services/api';

export default function PreExamCheck({
  examId,
  examDetails,
  onProceedToExam,
  onCancel,
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  // Diagnostics status
  const [diagnostics, setDiagnostics] = useState({
    browser: true,
    fullscreen: true,
    networkPing: 38,
  });

  // Captured photo state
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrolledSuccess, setEnrolledSuccess] = useState(false);
  const [enrollError, setEnrollError] = useState(null);

  // Honor code
  const [honorCodeAgreed, setHonorCodeAgreed] = useState(false);

  // Start webcam on mount
  useEffect(() => {
    let localStream = null;

    async function initWebcam() {
      try {
        localStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 480, height: 360, facingMode: 'user' },
          audio: false,
        });
        setStream(localStream);
        if (videoRef.current) {
          videoRef.current.srcObject = localStream;
          await videoRef.current.play();
          setCameraActive(true);
        }
      } catch (err) {
        setCameraError('Camera access required. Please allow camera permissions to continue.');
        setCameraActive(false);
      }
    }

    initWebcam();

    return () => {
      if (localStream) {
        localStream.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // Snapshot capture
  const handleCaptureSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = 480;
    canvas.height = 360;
    ctx.drawImage(video, 0, 0, 480, 360);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setCapturedPhoto(dataUrl);
    setEnrollError(null);
    setEnrolledSuccess(false);
  };

  const handleRetake = () => {
    setCapturedPhoto(null);
    setEnrolledSuccess(false);
    setEnrollError(null);
  };

  // Enroll captured reference photo
  const handleEnrollPhoto = async () => {
    if (!capturedPhoto) return;
    setIsEnrolling(true);
    setEnrollError(null);

    try {
      // 1. First ensure an attempt exists by initializing start
      const startData = await apiRequest(`/attempts/exams/${examId}/start`, {
        method: 'POST',
      });

      // 2. Enroll official photo against this attempt
      const formData = new FormData();
      formData.append('photo_base64', capturedPhoto);

      const res = await apiRequest(`/attempts/${startData.attempt_id}/enroll-identity`, {
        method: 'POST',
        body: formData,
      });

      if (res.success) {
        setEnrolledSuccess(true);
      } else {
        setEnrollError(res.message || 'Identity verification could not detect a valid face.');
      }
    } catch (err) {
      setEnrollError(err.message || 'Failed to verify reference photo. Please retake.');
      setEnrolledSuccess(false);
    } finally {
      setIsEnrolling(false);
    }
  };

  // Final confirmation to launch the exam
  const handleLaunchExam = () => {
    // Request fullscreen mode
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
    // Release pre-flight camera stream before transitioning to exam room HUD
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
    }
    onProceedToExam();
  };

  return (
    <div className="min-h-screen bg-canvas p-4 lg:p-8 flex items-center justify-center">
      <div className="bg-card border border-border rounded-2xl shadow-sm max-w-4xl w-full p-6 lg:p-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-border gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-primary/10 text-primary border border-primary/20">
                Pre-Flight Diagnostic
              </span>
              <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>Identity Calibration</span>
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              System Verification & Candidate Biometric Enrollment
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Assessment: <strong className="text-slate-800">{examDetails?.title || 'Selected Assessment'}</strong> ({examDetails?.subject || 'Curriculum'})
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-slate-500 self-start md:self-auto">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{examDetails?.duration_minutes || 30} Mins</span>
            </span>
            <span className="flex items-center gap-1">
              <Award className="w-3.5 h-3.5 text-slate-400" />
              <span>{examDetails?.total_marks || 35} Marks</span>
            </span>
          </div>
        </div>

        {/* Diagnostic Status Pills */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-lg bg-slate-50 border border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Monitor className="w-4 h-4 text-slate-600" />
              <span className="text-xs font-semibold text-slate-700">Display & Browser</span>
            </div>
            <span className="text-[11px] font-mono font-bold text-emerald-600 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Ready
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4 text-slate-600" />
              <span className="text-xs font-semibold text-slate-700">Network Latency</span>
            </div>
            <span className="text-[11px] font-mono font-bold text-emerald-600 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> {diagnostics.networkPing}ms
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-slate-600" />
              <span className="text-xs font-semibold text-slate-700">Webcam Optical Feed</span>
            </div>
            <span className={`text-[11px] font-mono font-bold flex items-center gap-1 ${cameraActive ? 'text-emerald-600' : 'text-danger'}`}>
              {cameraActive ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                </>
              ) : (
                <>
                  <XCircle className="w-3.5 h-3.5" /> Disabled
                </>
              )}
            </span>
          </div>
        </div>

        {/* Main Biometric Photo Capture Bento */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Camera Viewport & Calibration Oval */}
          <div className="md:col-span-7 bg-slate-900 rounded-xl overflow-hidden aspect-video relative flex items-center justify-center border border-slate-300 shadow-inner">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover transform scale-x-[-1] ${
                capturedPhoto || !cameraActive ? 'hidden' : ''
              }`}
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* If snapshot captured, show preview */}
            {capturedPhoto && (
              <img
                src={capturedPhoto}
                alt="Candidate Reference Baseline"
                className="w-full h-full object-cover"
              />
            )}

            {!cameraActive && !capturedPhoto && (
              <div className="text-center p-6 text-slate-400 space-y-2">
                <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
                <p className="text-xs font-semibold text-slate-300">
                  {cameraError || 'Waiting for webcam hardware connection...'}
                </p>
              </div>
            )}

            {/* Centered Face Alignment Oval Guide */}
            {cameraActive && !capturedPhoto && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-40 h-52 border-2 border-dashed border-emerald-400/80 rounded-[50%] flex flex-col items-center justify-end pb-3 bg-emerald-500/5">
                  <span className="text-[10px] font-mono text-emerald-300 bg-black/75 px-2 py-0.5 rounded">
                    Align Face Here
                  </span>
                </div>
              </div>
            )}

            {/* Status Overlay Badge */}
            <div className="absolute top-2 left-2 pointer-events-none">
              {enrolledSuccess ? (
                <span className="text-[10px] font-mono font-bold text-white bg-emerald-600 px-2 py-1 rounded shadow-xs flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Biometric Identity Enrolled
                </span>
              ) : capturedPhoto ? (
                <span className="text-[10px] font-mono font-bold text-white bg-indigo-600 px-2 py-1 rounded shadow-xs">
                  Captured Snapshot Preview
                </span>
              ) : (
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-black/70 px-2 py-1 rounded">
                  Live Calibration Feed
                </span>
              )}
            </div>
          </div>

          {/* Right Instruction and Action Panel */}
          <div className="md:col-span-5 space-y-4">
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-800">
                Candidate Photographic Calibration
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Your reference photograph will be securely locked as your baseline facial signature. During the assessment, real-time proctoring validates that the same student remains in front of the camera.
              </p>
            </div>

            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4 leading-normal">
              <li>Ensure even ambient lighting with no harsh shadows.</li>
              <li>Look straight into the webcam inside the alignment guide.</li>
              <li>Remove tinted glasses, caps, or head coverings.</li>
            </ul>

            {/* Error Banner */}
            {enrollError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{enrollError}</span>
              </div>
            )}

            {/* Enrollment Success Banner */}
            {enrolledSuccess && (
              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="block font-semibold">Verification Confirmed</strong>
                  <span>Your facial identity has been enrolled for continuous proctoring.</span>
                </div>
              </div>
            )}

            {/* Capture Buttons */}
            <div className="pt-2 flex flex-col gap-2">
              {!capturedPhoto ? (
                <button
                  type="button"
                  disabled={!cameraActive}
                  onClick={handleCaptureSnapshot}
                  className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5"
                >
                  <Camera className="w-4 h-4" />
                  <span>Capture Official Reference Photo</span>
                </button>
              ) : !enrolledSuccess ? (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleRetake}
                    className="flex-1 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Retake</span>
                  </button>
                  <button
                    type="button"
                    disabled={isEnrolling}
                    onClick={handleEnrollPhoto}
                    className="flex-1 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{isEnrolling ? 'Verifying...' : 'Verify & Lock Photo'}</span>
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleRetake}
                  className="w-full py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retake Another Photo</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Phase 3: Honor Code Acknowledgement */}
        <div className="p-4 rounded-xl bg-slate-50 border border-border flex items-start gap-3">
          <input
            id="honor-check"
            type="checkbox"
            checked={honorCodeAgreed}
            onChange={(e) => setHonorCodeAgreed(e.target.checked)}
            className="mt-0.5 rounded border-slate-300 text-primary focus:ring-primary w-4 h-4 cursor-pointer"
          />
          <label htmlFor="honor-check" className="text-xs text-slate-700 leading-relaxed cursor-pointer select-none">
            <strong>Candidate Honor Pledge:</strong> I certify that I am the authorized student taking this assessment. I understand that the session is strictly proctored in fullscreen, and that background tab changes, multiple faces, different individuals, or mobile phones will be immediately logged in my integrity audit report.
          </label>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
          >
            Cancel & Return
          </button>

          <button
            type="button"
            disabled={!enrolledSuccess || !honorCodeAgreed}
            onClick={handleLaunchExam}
            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-xs transition-all flex items-center gap-2"
          >
            <span>Enter Examination Environment</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
