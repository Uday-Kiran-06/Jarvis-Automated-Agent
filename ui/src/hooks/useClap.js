import { useEffect, useRef, useCallback } from 'react';

/**
 * useClapDetector — detects two sharp claps via Web Audio API
 * @param {function} onDoubleClap — fires when 2 claps detected within 800ms
 * @param {boolean}  enabled      — only run when true
 */
export function useClapDetector(onDoubleClap, enabled = true) {
  const audioCtxRef  = useRef(null);
  const analyserRef  = useRef(null);
  const streamRef    = useRef(null);
  const rafRef       = useRef(null);
  const clapTimesRef = useRef([]);
  const floorRef     = useRef(0);
  const callbackRef  = useRef(onDoubleClap);

  useEffect(() => { callbackRef.current = onDoubleClap; }, [onDoubleClap]);

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioCtxRef.current = ctx;

      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const buf = new Uint8Array(analyser.frequencyBinCount);

      // Calibrate ambient noise for 600ms
      let samples = 0, sum = 0;
      const calibrate = setInterval(() => {
        analyser.getByteTimeDomainData(buf);
        const rms = Math.sqrt(buf.reduce((s, v) => s + (v - 128) ** 2, 0) / buf.length);
        sum += rms; samples++;
      }, 20);

      setTimeout(() => {
        clearInterval(calibrate);
        
        // Increase threshold to prevent normal speech/noise from triggering it.
        // A clap is significantly louder than ambient noise.
        floorRef.current = (sum / samples) + 40; // threshold = floor + 40

        let lastPeak = 0;
        // Increase cooldown to prevent one long noise from triggering multiple peaks
        const COOLDOWN = 250; // ms between peaks

        const tick = () => {
          analyser.getByteTimeDomainData(buf);
          const rms = Math.sqrt(buf.reduce((s, v) => s + (v - 128) ** 2, 0) / buf.length);
          const now = performance.now();

          if (rms > floorRef.current && now - lastPeak > COOLDOWN) {
            lastPeak = now;
            clapTimesRef.current = [...clapTimesRef.current.filter(t => now - t < 800), now];

            if (clapTimesRef.current.length >= 2) {
              clapTimesRef.current = [];
              callbackRef.current();
            }
          }

          rafRef.current = requestAnimationFrame(tick);
        };

        tick();
      }, 600);

    } catch (e) {
      console.warn('Clap detector: mic access denied', e);
    }
  }, []);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
  }, []);

  useEffect(() => {
    if (enabled) start();
    else stop();
    return stop;
  }, [enabled, start, stop]);
}
