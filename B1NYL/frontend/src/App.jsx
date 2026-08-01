import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, CheckSquare, Square, AlertTriangle, Send } from 'lucide-react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import Building3D from './components/Building3D';
import WorkerDot from './components/WorkerDot';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [workers, setWorkers] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  
  const [alerts, setAlerts] = useState([]);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    fetchWorkers();
    fetchAlerts();
    
    const interval = setInterval(() => {
      fetchWorkers();
      fetchAlerts();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchWorkers = async () => {
    try {
      const res = await fetch(`${API_BASE}/workers`);
      const data = await res.json();
      setWorkers(data);
    } catch (err) {
      console.error("Failed to fetch workers", err);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`);
      const data = await res.json();
      setAlerts(data);
    } catch (err) {
      console.error("Failed to fetch alerts", err);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
        method: 'POST'
      });
      // Fetch alerts immediately after resolving
      fetchAlerts();
      fetchWorkers();
    } catch (err) {
      console.error("Failed to resolve alert", err);
    }
  };

  const toggleWorker = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const selectAll = () => {
    if (selectedIds.size === workers.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(workers.map(w => w.id)));
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => {
      setToast(prev => ({ ...prev, show: false }));
    }, 3000);
  };

  const updateWorkerPosition = async (id, x, y, z) => {
    // Optimistic update
    setWorkers(prev => prev.map(w => w.id === id ? { ...w, position: { x, y, z } } : w));
    try {
      await fetch(`${API_BASE}/workers/${id}/position`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, z })
      });
    } catch (err) {
      console.error("Failed to update position", err);
    }
  };

  const resetPositions = async () => {
    // Optimistic update
    setWorkers(prev => prev.map(w => ({ ...w, position: { ...w.position, y: 0 } })));
    try {
      await fetch(`${API_BASE}/workers/reset`, {
        method: 'POST'
      });
      showToast("모든 노동자의 위치가 1층으로 초기화되었습니다.", "success");
    } catch (err) {
      console.error("Failed to reset positions", err);
      showToast("초기화 실패", "error");
    }
  };

  const startRecording = async () => {
    if (selectedIds.size === 0) {
      showToast("먼저 지시를 전달할 노동자를 선택해주세요.", "error");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      showToast("마이크 접근 권한이 필요합니다.", "error");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
      showToast("음성을 분석하고 전송중입니다...", "success");
    }
  };

  const sendAudio = async (blob) => {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    formData.append('selected_workers', Array.from(selectedIds).join(','));

    try {
      const res = await fetch(`${API_BASE}/broadcast`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setIsProcessing(false);
      
      if (res.ok) {
        setTranscribedText(data.text);
        showToast(`전송되었습니다!`, "success");
      } else {
        showToast(`전송 실패: ${data.detail}`, "error");
      }
    } catch (err) {
      console.error("Upload error", err);
      setIsProcessing(false);
      showToast("서버와 통신할 수 없습니다.", "error");
    }
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <h1>Smart Hardhat 3D Control</h1>
          <p>현장 인력 모니터링 및 실시간 지시 대시보드</p>
        </div>
        <div className="btn-group">
          <button className="btn" onClick={resetPositions} style={{ marginRight: '8px' }}>
            🔄 1층으로 초기화
          </button>
          <button className="btn" onClick={selectAll}>
            {selectedIds.size === workers.length && workers.length > 0 ? (
              <><CheckSquare size={20} /> 선택 해제</>
            ) : (
              <><CheckSquare size={20} /> 전체 선택</>
            )}
          </button>
        </div>
      </header>

      <main className="glass-panel" style={{ height: '700px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, position: 'relative', borderRadius: '16px', overflow: 'hidden', background: '#e2e8f0' }}>
          <Canvas camera={{ position: [20, 15, 20], fov: 45 }}>
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 20, 10]} intensity={1.5} />
            
            <Building3D />
            
            {workers.map(worker => (
              <WorkerDot 
                key={worker.id} 
                worker={worker} 
                isSelected={selectedIds.has(worker.id)} 
                onClick={toggleWorker} 
                onPositionChange={updateWorkerPosition}
              />
            ))}
            
            <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2 - 0.05} />
          </Canvas>
          <div style={{ position: 'absolute', top: '16px', left: '16px', color: 'var(--text-secondary)', fontSize: '0.9rem', pointerEvents: 'none', background: 'rgba(255,255,255,0.8)', padding: '8px 12px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
            🖱️ 마우스 좌클릭 드래그로 회전, 휠로 확대/축소할 수 있습니다.
          </div>
        </div>

        <div className="controls-section" style={{ marginTop: '1rem', paddingTop: '1rem' }}>
          <div className="mic-wrapper">
            <div className={`recording-status ${isRecording ? 'active' : ''}`}>
              ● 녹음 중... 마우스를 떼면 전송됩니다
            </div>
            <button 
              className={`mic-btn ${isRecording ? 'recording' : ''}`}
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
            >
              {isRecording ? <Mic size={36} /> : <MicOff size={36} />}
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)' }}>버튼을 누른 채로 말하세요. (Push to Talk)</p>
          
          {isProcessing && (
            <div style={{ marginTop: '0.5rem', padding: '1rem', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-blue)', fontWeight: '600' }}>
              ⏳ 음성을 변환하고 있습니다...
            </div>
          )}
          {!isProcessing && transcribedText && (
            <div style={{ marginTop: '0.5rem', padding: '1rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.05)', color: 'var(--text-primary)', border: '1px solid rgba(16, 185, 129, 0.2)', maxWidth: '600px', textAlign: 'center' }}>
              <span style={{ color: 'var(--accent-green)', fontWeight: 'bold', marginRight: '8px' }}>인식된 내용:</span>
              <span>{transcribedText}</span>
            </div>
          )}
        </div>
      </main>

      <div className={`toast ${toast.show ? 'show' : ''} ${toast.type}`}>
        {toast.type === 'error' ? <AlertTriangle size={20} /> : <Send size={20} />}
        {toast.message}
      </div>

      {/* 긴급 낙상 팝업 오버레이 */}
      {alerts.length > 0 && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(239, 68, 68, 0.4)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
          <div style={{ background: 'white', padding: '3rem', borderRadius: '24px', boxShadow: '0 25px 50px -12px rgba(239, 68, 68, 0.5)', maxWidth: '500px', width: '90%', textAlign: 'center', animation: 'pulse 2s infinite' }}>
            <AlertTriangle size={80} color="#ef4444" style={{ margin: '0 auto 1.5rem auto' }} />
            <h2 style={{ color: '#ef4444', fontSize: '2rem', marginBottom: '1rem', fontWeight: '800' }}>긴급: 낙상 발생!</h2>
            <p style={{ fontSize: '1.2rem', color: '#334155', marginBottom: '2rem' }}>
              <strong>{workers.find(w => w.id === alerts[0].worker_id)?.name || '알 수 없는 노동자'}</strong>님의 기기에서 <strong>"{alerts[0].message}"</strong>(이)가 보고되었습니다. 신속한 확인이 필요합니다!
            </p>
            <button 
              style={{ background: '#ef4444', color: 'white', border: 'none', padding: '1rem 2rem', fontSize: '1.1rem', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer', width: '100%', boxShadow: '0 4px 14px 0 rgba(239, 68, 68, 0.39)' }}
              onClick={() => resolveAlert(alerts[0].id)}
            >
              상황 확인 및 알림 닫기
            </button>
          </div>
          <style>{`
            @keyframes pulse {
              0%, 100% { transform: scale(1); }
              50% { transform: scale(1.02); }
            }
          `}</style>
        </div>
      )}
    </div>
  );
}

export default App;
