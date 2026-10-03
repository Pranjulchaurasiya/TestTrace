import React, { useEffect, useRef, useState } from 'react';
import { Camera, UserCheck, Eye, Compass, Maximize2, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import { apiRequest } from '../services/api';

export default function ProctorHUD({
  attemptId,
  tabSwitches = 0,
  onViolationOccurred,
  onExamTerminated,
  isFloating = false,
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);

  const [cameraActive, setCameraActive] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [telemetry, setTelemetry] = useState({
    facesDetected: null,
    identityVerified: true,
    gazeStatus: 'DETECTING',
    headPose: 'DETECTING',
  });
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [recentAlert, setRecentAlert] = useState(null);

  // Initialize webcam
  useEffect(() => {
    let stream = null;

    async function initCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: 'user' },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setCameraActive(true);
        }
      } catch (err) {
        console.warn('Camera access not available or permission denied:', err.message);
        setCameraActive(false);
      }
    }

    initCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const onViolationRef = useRef(onViolationOccurred);
  const onTerminatedRef = useRef(onExamTerminated);

  useEffect(() => {
    onViolationRef.current = onViolationOccurred;
  }, [onViolationOccurred]);

  useEffect(() => {
    onTerminatedRef.current = onExamTerminated;
  }, [onExamTerminated]);

  // Frame capture loop (sends compressed frame immediately upon camera start, then every 3.5s)
  useEffect(() => {
    if (!attemptId || !cameraActive) return;

    let isProcessing = false;

    const captureAndAnalyze = () => {
      if (isProcessing) return;
      if (!videoRef.current || !canvasRef.current) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      if (video.videoWidth === 0 || video.videoHeight === 0) return;

      canvas.width = 320;
      canvas.height = 240;
      ctx.drawImage(video, 0, 0, 320, 240);

      isProcessing = true;
      canvas.toBlob(
        async (blob) => {
          if (!blob) {
            isProcessing = false;
            return;
          }
          try {
            const formData = new FormData();
            formData.append('attempt_id', attemptId);
            formData.append('frame', blob, 'frame.jpg');

            const res = await apiRequest('/proctor/analyze-frame', {
              method: 'POST',
              body: formData,
            });

            setTelemetry({
              facesDetected: res.faces_detected,
              identityVerified: res.identity_verified !== false,
              gazeStatus: res.gaze_status,
              headPose: res.head_pose_direction,
            });

            if (res.violation_detected) {
              setRecentAlert(res.warning_message || `Detected: ${res.violation_detected}`);
              if (onViolationRef.current) onViolationRef.current(res);
            }

            if (res.terminate_exam) {
              if (onTerminatedRef.current) onTerminatedRef.current(res.warning_message);
            }
          } catch (err) {
            console.warn('[ProctorHUD] Frame analysis error:', err);
          } finally {
            isProcessing = false;
          }
        },
        'image/jpeg',
        0.55
      );
    };

    // Capture immediately after 600ms stream warmup, then repeat every 3.5s
    const warmupTimer = setTimeout(captureAndAnalyze, 600);
    intervalRef.current = setInterval(captureAndAnalyze, 3500);

    return () => {
      clearTimeout(warmupTimer);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [attemptId, cameraActive]);

  // Browser-level telemetry listeners
  useEffect(() => {
    if (!attemptId) return;

    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'hidden') {
        try {
          const res = await apiRequest('/proctor/violation', {
            method: 'POST',
            body: JSON.stringify({
              attempt_id: attemptId,
              violation_type: 'TAB_SWITCH',
              metadata: { timestamp: new Date().toISOString() },
            }),
          });

          setRecentAlert(res.warning_message || 'Warning: Tab switch recorded.');
          if (onViolationOccurred) onViolationOccurred(res);

          if (res.terminate_exam) {
            if (onExamTerminated) onExamTerminated(res.warning_message);
          }
        } catch (err) {
          console.error('Failed to report tab switch violation:', err);
        }
      }
    };

    const handleFullscreenChange = async () => {
      const isFull = !!document.fullscreenElement;
      setIsFullscreen(isFull);

      if (!isFull) {
        try {
          const res = await apiRequest('/proctor/violation', {
            method: 'POST',
            body: JSON.stringify({
              attempt_id: attemptId,
              violation_type: 'FULLSCREEN_EXIT',
              metadata: { timestamp: new Date().toISOString() },
            }),
          });

          setRecentAlert('Warning: Fullscreen exited.');
          if (onViolationOccurred) onViolationOccurred(res);
        } catch (err) {
          console.error('Failed to report fullscreen violation:', err);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [attemptId, onViolationOccurred, onExamTerminated]);

  const containerClasses = isFloating
    ? 'fixed bottom-4 right-4 z-40 w-72 bg-white/95 backdrop-blur-md border border-slate-300 rounded-xl shadow-lg p-3 transition-all'
    : 'bg-card border border-border rounded-lg p-3 shadow-xs flex flex-col gap-2.5';

  return (
    <div className={containerClasses}>
      <div className="flex items-center justify-between text-xs font-semibold text-slate-800 pb-1.5 border-b border-border">
        <div className="flex items-center gap-1.5">
          <Camera className="w-3.5 h-3.5 text-primary" />
          <span>Biometric & Integrity HUD</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-mono text-success bg-success-light px-1.5 py-0.5 rounded border border-success-border font-bold">
            Live
          </span>
          <button
            onClick={() => setIsMinimized((prev) => !prev)}
            title={isMinimized ? 'Expand HUD' : 'Minimize HUD'}
            className="p-0.5 rounded hover:bg-slate-100 text-slate-500"
          >
            {isMinimized ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Video Preview and Badges (hidden when minimized) */}
      {!isMinimized && (
        <div className="space-y-2 mt-2">
          {/* Video Preview */}
          <div className="relative w-full aspect-video bg-slate-900 rounded overflow-hidden flex items-center justify-center border border-slate-300">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover transform scale-x-[-1] ${
                !cameraActive ? 'hidden' : ''
              }`}
            />
            <canvas ref={canvasRef} className="hidden" />

            {!cameraActive && (
              <div className="text-center px-4 py-2 text-slate-400 text-xs">
                <Camera className="w-5 h-5 mx-auto mb-1 text-slate-500" />
                <span>Connecting Camera...</span>
              </div>
            )}

            {/* Target Bounding Frame - Dynamic based on actual detected face */}
            {/* Target Bounding Frame - Dynamic based on actual detected face and identity match */}
            {cameraActive && (
              <div
                className={`absolute inset-2 border-2 border-dashed rounded pointer-events-none flex items-start justify-end p-1 transition-colors ${
                  telemetry.facesDetected === 1
                    ? telemetry.identityVerified
                      ? 'border-emerald-400/80 bg-emerald-500/5'
                      : 'border-rose-500/90 bg-rose-500/15 animate-pulse'
                    : telemetry.facesDetected === 0
                    ? 'border-rose-400/80 bg-rose-500/10'
                    : telemetry.facesDetected === null
                    ? 'border-slate-400/60 bg-slate-500/5'
                    : 'border-amber-400/80 bg-amber-500/10'
                }`}
              >
                <span
                  className={`text-[9px] font-mono px-1 rounded ${
                    telemetry.facesDetected === 1
                      ? telemetry.identityVerified
                        ? 'text-emerald-400 bg-black/75'
                        : 'text-rose-300 bg-rose-950/90 font-bold'
                      : telemetry.facesDetected === 0
                      ? 'text-rose-400 bg-black/75'
                      : telemetry.facesDetected === null
                      ? 'text-slate-300 bg-black/75'
                      : 'text-amber-400 bg-black/75'
                  }`}
                >
                  {telemetry.facesDetected === 1
                    ? telemetry.identityVerified
                      ? 'Face Verified'
                      : 'Different Person Detected'
                    : telemetry.facesDetected === 0
                    ? 'No Face Detected'
                    : telemetry.facesDetected === null
                    ? 'Scanning Frame...'
                    : `${telemetry.facesDetected} Faces In Frame`}
                </span>
              </div>
            )}
          </div>

          {/* Live AI Telemetry Badges */}
          <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono">
            <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-border">
              <span className="text-slate-500 flex items-center gap-1">
                <UserCheck className="w-3 h-3 text-slate-600" /> Face:
              </span>
              <span
                className={`font-semibold ${
                  telemetry.facesDetected === 1
                    ? telemetry.identityVerified
                      ? 'text-success'
                      : 'text-danger font-bold'
                    : telemetry.facesDetected === null
                    ? 'text-slate-400'
                    : 'text-danger'
                }`}
              >
                {telemetry.facesDetected === null
                  ? 'Scanning...'
                  : telemetry.facesDetected === 0
                  ? 'None Found'
                  : telemetry.facesDetected === 1
                  ? telemetry.identityVerified
                    ? 'Verified'
                    : 'Mismatch'
                  : `${telemetry.facesDetected} Found`}
              </span>
            </div>

            <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-border">
              <span className="text-slate-500 flex items-center gap-1">
                <Eye className="w-3 h-3 text-slate-600" /> Gaze:
              </span>
              <span className={`font-semibold ${telemetry.gazeStatus === 'FOCUSED' ? 'text-success' : 'text-warning'}`}>
                {telemetry.gazeStatus}
              </span>
            </div>

            <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-border">
              <span className="text-slate-500 flex items-center gap-1">
                <Compass className="w-3 h-3 text-slate-600" /> Head:
              </span>
              <span className="font-semibold text-slate-700">{telemetry.headPose}</span>
            </div>

            <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-border">
              <span className="text-slate-500 flex items-center gap-1">
                <Maximize2 className="w-3 h-3 text-slate-600" /> Tabs:
              </span>
              <span className={`font-semibold ${tabSwitches > 0 ? 'text-danger' : 'text-slate-700'}`}>
                {tabSwitches} / 3
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Minimized Compact View summary */}
      {isMinimized && (
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-600 pt-1">
          <span>
            Face:{' '}
            <strong
              className={
                telemetry.facesDetected === 1
                  ? telemetry.identityVerified
                    ? 'text-success'
                    : 'text-danger font-bold'
                  : telemetry.facesDetected === 0
                  ? 'text-danger'
                  : 'text-slate-500'
              }
            >
              {telemetry.facesDetected === 1
                ? telemetry.identityVerified
                  ? 'Verified'
                  : 'Mismatch'
                : telemetry.facesDetected === 0
                ? 'None'
                : telemetry.facesDetected ?? 'Scanning'}
            </strong>
          </span>
          <span>Gaze: <strong className={telemetry.gazeStatus === 'FOCUSED' ? 'text-success' : 'text-slate-700'}>{telemetry.gazeStatus}</strong></span>
          <span>Tabs: <strong className="text-slate-800">{tabSwitches}/3</strong></span>
        </div>
      )}

      {/* Real-time Alert Toast inside HUD */}
      {recentAlert && (
        <div className="p-2 rounded bg-warning-light border border-warning-border text-slate-800 text-[11px] flex items-start gap-1.5 leading-snug mt-1">
          <ShieldAlert className="w-3.5 h-3.5 text-warning shrink-0 mt-0.5" />
          <span>{recentAlert}</span>
        </div>
      )}
    </div>
  );
}
