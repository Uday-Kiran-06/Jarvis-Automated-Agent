import React, {
  useState, useEffect, useRef, useCallback
} from 'react';
import './App.css';
import { useClapDetector } from './hooks/useClap';
import { useCoreVisualizer } from './hooks/useCoreVisualizer';

const WAKE_PHRASES  = ['wake up', 'hey', 'activate', 'rise', 'jarvis'];
const SLEEP_PHRASES = ['sleep', 'standby', 'goodbye', "that's all", 'stop listening'];
const SLEEP_AFTER   = 30_000;

export default function App() {
  const [awakened,  setAwakened]  = useState(false);
  const [phase,     setPhase]     = useState('idle');
  const [messages,  setMessages]  = useState([]);
  const [logs,      setLogs]      = useState([{ t: 'System initialized.', type: 'system' }]);

  const canvasRef     = useRef(null);
  const srMainRef     = useRef(null);
  const srWakeRef     = useRef(null);
  const sleepTimer    = useRef(null);
  const awakenedRef   = useRef(false);
  const phaseRef      = useRef('idle');
  const chatEndRef    = useRef(null);
  const logEndRef     = useRef(null);
  const isProcessing  = useRef(false);
  const activateRef   = useRef(null);
  const deactivateRef = useRef(null);

  useEffect(() => { awakenedRef.current = awakened; }, [awakened]);
  useEffect(() => { phaseRef.current    = phase;    }, [phase]);

  useCoreVisualizer(canvasRef, phase, awakened);

  const addLog = useCallback((text, type = 'default') => {
    setLogs(p => [...p.slice(-10), { t: text, type, ts: new Date().toLocaleTimeString() }]);
  }, []);

  const resetSleepTimer = useCallback(() => {
    clearTimeout(sleepTimer.current);
    sleepTimer.current = setTimeout(() => {
      if (awakenedRef.current) {
        addLog('Inactivity timeout. Standby.', 'warning');
        deactivateRef.current?.();
      }
    }, SLEEP_AFTER);
  }, [addLog]);

  const speak = useCallback((text, onDone) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.pitch = 0.85; u.rate = 1.05;
    const v = window.speechSynthesis.getVoices();
    const pick = v.find(x =>
      x.name.includes('Google UK English Male') ||
      x.name.includes('Microsoft David') ||
      x.lang === 'en-GB'
    );
    if (pick) u.voice = pick;
    setPhase('speak');
    u.onend = () => { setPhase('idle'); onDone?.(); };
    window.speechSynthesis.speak(u);
  }, []);

  const send = useCallback(async (text) => {
    isProcessing.current = true;        // 🔒 Lock — mic will NOT restart
    srMainRef.current?.abort();         // Kill mic immediately
    setPhase('think');
    setMessages(p => [...p, { r: 'user', t: text }]);
    addLog(`Processing: "${text}"`, 'system');
    resetSleepTimer();
    try {
      const res  = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: text, provider: 'groq' }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages(p => [...p, { r: 'jarvis', t: data.response }]);
      addLog('Response generated — speaking...', 'system');
      speak(data.response, () => {
        addLog('Jarvis finished speaking — resuming listener.', 'system');
        isProcessing.current = false;  // 🔓 Unlock AFTER speaking done
        setPhase('idle');              // triggers auto-restart below
      });
    } catch (e) {
      isProcessing.current = false;
      setPhase('error');
      addLog(`Error: ${e.message}`, 'error');
      speak("I encountered a system error, Sir.");
      setTimeout(() => setPhase('idle'), 2500);
    }
  }, [resetSleepTimer, speak, addLog]);

  // ── Main SR — continuous, stays open indefinitely ────────────────
  const buildMainSR = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous      = true;   // never times out
    r.interimResults  = true;
    r.lang            = 'en-US';
    r.maxAlternatives = 1;

    let silenceTimer = null;

    r.onstart = () => {
      setPhase('listen');
      addLog('Microphone open — speak anytime.', 'system');
    };

    r.onresult = (e) => {
      let finalText = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
      }
      if (!finalText.trim()) return;

      clearTimeout(silenceTimer);
      const text = finalText.trim();

      silenceTimer = setTimeout(() => {
        if (!awakenedRef.current) return;
        if (SLEEP_PHRASES.some(p => text.toLowerCase().includes(p))) {
          speak('Entering standby mode, Sir.');
          deactivateRef.current?.();
          return;
        }
        r.abort();    // stop listening before processing
        send(text);
      }, 600);
    };

    r.onerror = (e) => {
      if (['no-speech', 'aborted'].includes(e.error)) return;
      addLog(`STT Error: ${e.error}`, 'error');
    };

    r.onend = () => {
      clearTimeout(silenceTimer);
      // Only restart when completely idle and not locked
      if (awakenedRef.current && !isProcessing.current && phaseRef.current === 'idle') {
        setTimeout(() => {
          try {
            if (awakenedRef.current && !isProcessing.current && phaseRef.current === 'idle') {
              r.start();
            }
          } catch (_) {}
        }, 400);
      }
    };

    return r;
  }, [send, speak, addLog]); // eslint-disable-line

  // ── Wake SR — continuous, never has a gap ────────────────────────
  const buildWakeSR = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous     = true;   // never stops, never misses a phrase
    r.interimResults = true;   // catch phrase mid-utterance
    r.lang           = 'en-US';

    // Bias Chrome toward wake phrases
    if (window.SpeechGrammarList) {
      const gl = new window.SpeechGrammarList();
      gl.addFromString(
        '#JSGF V1.0; grammar wake; public <wake> = wake up | hey | activate | rise | jarvis;',
        1
      );
      r.grammars = gl;
    }

    r.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript.toLowerCase().trim();
        if (WAKE_PHRASES.some(p => t.includes(p))) {
          r.abort();
          activateRef.current?.();
          return;
        }
      }
    };

    r.onerror = (e) => {
      if (['no-speech', 'aborted'].includes(e.error)) return;
      console.warn('Wake SR error:', e.error);
    };

    r.onend = () => {
      // Restart immediately with minimal gap (150ms) so nothing is missed
      if (!awakenedRef.current) {
        setTimeout(() => {
          try { if (!awakenedRef.current) r.start(); } catch (_) {}
        }, 150);
      }
    };

    return r;
  }, []); // eslint-disable-line

  // ── Activate ─────────────────────────────────────────────────────
  const activate = useCallback(() => {
    setAwakened(true);
    isProcessing.current = false;  // ensure unlocked on fresh activation
    addLog('Security clearance granted. System Active.', 'system');
    srWakeRef.current?.abort();
    srMainRef.current?.abort();
    const sr = buildMainSR();
    srMainRef.current = sr;
    speak('Jarvis is online and at your service, Sir.', () => {
      try { srMainRef.current?.start(); } catch (_) {}
    });
    resetSleepTimer();
  }, [buildMainSR, resetSleepTimer, speak, addLog]);

  // ── Deactivate ───────────────────────────────────────────────────
  const deactivate = useCallback(() => {
    clearTimeout(sleepTimer.current);
    isProcessing.current = false;
    setAwakened(false);
    setPhase('idle');
    srMainRef.current?.abort();
    addLog('System entering standby.', 'system');
    srWakeRef.current = buildWakeSR();
    setTimeout(() => { try { srWakeRef.current?.start(); } catch (_) {} }, 400);
  }, [buildWakeSR, addLog]);

  // Keep refs in sync
  useEffect(() => { activateRef.current   = activate;   }, [activate]);
  useEffect(() => { deactivateRef.current = deactivate; }, [deactivate]);

  // Auto-restart main SR when returning to idle and not locked
  useEffect(() => {
    if (awakened && phase === 'idle' && !isProcessing.current) {
      const t = setTimeout(() => {
        try {
          if (awakenedRef.current && phaseRef.current === 'idle' && !isProcessing.current) {
            srMainRef.current?.start();
          }
        } catch (_) {}
      }, 600);
      return () => clearTimeout(t);
    }
  }, [awakened, phase]);

  // Init wake SR on mount
  useEffect(() => {
    srWakeRef.current = buildWakeSR();
    setTimeout(() => { try { srWakeRef.current?.start(); } catch (_) {} }, 800);
    return () => { srWakeRef.current?.abort(); srMainRef.current?.abort(); };
  }, []); // eslint-disable-line

  useClapDetector(useCallback(() => {
    if (awakenedRef.current) deactivateRef.current?.();
    else activateRef.current?.();
  }, []), true);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' });  }, [logs]);

  return (
    <div className="app">
      <div className="core-container">
        <canvas ref={canvasRef} className="core-canvas" />
      </div>

      <div className="status-bar">
        <div className="status-pill">
          <div className={`status-dot ${awakened ? phase : 'idle'}`} />
          {awakened ? phase.toUpperCase() : 'STANDBY'}
        </div>
        <div className="status-pill">ENC: AES-256</div>
      </div>

      <div className="side-panel left-panel">
        <div className="panel-title">System Diagnostics</div>
        <div className="stat-item">
          <div className="stat-label">Neural Engine</div>
          <div className="stat-value">Llama 3.3 70B</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Search Provider</div>
          <div className="stat-value">DuckDuckGo</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Audio Stream</div>
          <div className="stat-value">
            {awakened ? (phase === 'listen' ? '● LIVE' : phase.toUpperCase()) : 'Dormant'}
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Wake Method</div>
          <div className="stat-value">Clap ×2 or "Wake Up"</div>
        </div>
      </div>

      <div className="side-panel right-panel">
        <div className="panel-title">Active Communication</div>
        <div className="conversation-container">
          {messages.length === 0 ? (
            <div style={{ opacity: 0.3, fontSize: '0.8rem', textAlign: 'center', marginTop: '50%' }}>
              Awaiting command input...
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.r}`}>
                {m.t}
              </div>
            ))
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="bottom-terminal">
        {logs.map((l, i) => (
          <div key={i} className={`terminal-log ${l.type}`}>
            <span style={{ opacity: 0.4 }}>[{l.ts}]</span> {l.t}
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
