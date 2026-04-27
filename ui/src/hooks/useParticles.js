import { useEffect, useRef } from 'react';

const PHASE_COLOR = {
  listen:  { r: 255, g:  61, b:  90 },
  think:   { r: 255, g: 179, b:   0 },
  speak:   { r:   0, g: 229, b: 255 },
  active:  { r:   0, g: 229, b: 255 },
  idle:    { r:  80, g: 150, b: 255 },
};

function randomBetween(a, b) { return a + Math.random() * (b - a); }

class DustParticle {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.reset();
    // Start randomly on screen initially
    this.x = randomBetween(0, w);
    this.y = randomBetween(0, h);
  }

  reset() {
    this.x = randomBetween(0, this.w);
    // Spawn mostly near the bottom to drift up, but sometimes anywhere
    this.y = Math.random() > 0.2 ? this.h + randomBetween(10, 100) : randomBetween(0, this.h);
    this.vx = randomBetween(-0.3, 0.3);
    this.vy = randomBetween(-0.5, -2.0); // Drift upwards
    this.size = randomBetween(1.0, 4.0);
    this.life = randomBetween(0.3, 1.0);
    this.decay = randomBetween(0.002, 0.006);
    this.wobbleSpeed = randomBetween(0.01, 0.05);
    this.wobble = randomBetween(0, Math.PI * 2);
  }

  update(phase) {
    let speedMult = 1.0;

    if (phase === 'listen') {
      speedMult = 0.2; // Slow down like time is frozen/waiting
    } else if (phase === 'think') {
      speedMult = 3.0; // Speed up to show processing
    } else if (phase === 'speak') {
      speedMult = 1.5;
    } else if (phase === 'idle') {
      speedMult = 0.5; // Very slow lazy drift
    }

    this.wobble += this.wobbleSpeed;
    this.x += (this.vx + Math.sin(this.wobble) * 0.5) * speedMult;
    this.y += this.vy * speedMult;

    this.life -= this.decay;

    // Reset if dead or completely off screen
    if (this.life <= 0 || this.y < -50 || this.x < -50 || this.x > this.w + 50) {
      this.reset();
      this.life = 1;
    }
  }

  draw(ctx, colorStr) {
    ctx.save();
    ctx.globalAlpha = Math.max(0.1, this.life);
    ctx.shadowBlur = 15;
    ctx.shadowColor = colorStr;
    ctx.fillStyle = colorStr;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

export function useParticles(canvasRef, phase, awakened) {
  const particlesRef = useRef([]);
  const rafRef = useRef(null);
  const phaseRef = useRef(phase);
  const awakenedRef = useRef(awakened);

  useEffect(() => { phaseRef.current = phase; }, [phase]);
  useEffect(() => { awakenedRef.current = awakened; }, [awakened]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      // Re-initialize boundaries for existing particles
      particlesRef.current.forEach(p => {
        p.w = canvas.width;
        p.h = canvas.height;
      });
    };
    resize();
    window.addEventListener('resize', resize);

    const MAX_PARTICLES = 600;
    
    const initParticles = () => {
      particlesRef.current = [];
      for (let i = 0; i < MAX_PARTICLES; i++) {
        particlesRef.current.push(new DustParticle(canvas.width, canvas.height));
      }
    };
    initParticles();

    const loop = () => {
      rafRef.current = requestAnimationFrame(loop);
      
      // Clean clear
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const currentPhase = awakenedRef.current ? phaseRef.current : 'idle';
      const c = PHASE_COLOR[currentPhase] || PHASE_COLOR.idle;
      const colorStr = `rgb(${c.r}, ${c.g}, ${c.b})`;

      // Optional: Add a subtle overall ambient glow at the bottom
      try {
        ctx.save();
        const glow = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - 300);
        glow.addColorStop(0, `rgba(${c.r}, ${c.g}, ${c.b}, 0.15)`);
        glow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.restore();
      } catch(e) {}

      particlesRef.current.forEach(p => {
        p.update(currentPhase);
        p.draw(ctx, colorStr);
      });
    };

    loop();

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [canvasRef]);
}
