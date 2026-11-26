import { useEffect, useRef } from 'react';

export default function DottedGlowBackground({
  className = '',
  gap = 16,
  radius = 1.4,
  color = 'rgba(255, 255, 255, 0.22)',
  glowColor = 'rgba(56, 189, 248, 0.85)',
  opacity = 0.75,
  speedMin = 0.4,
  speedMax = 1.2,
  speedScale = 0.8,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let dots = [];

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const { width, height } = container.getBoundingClientRect();
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      dots = [];
      const cols = Math.ceil(width / gap) + 1;
      const rows = Math.ceil(height / gap) + 1;
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          dots.push({
            x: i * gap + (j % 2 === 0 ? 0 : gap * 0.5),
            y: j * gap,
            phase: Math.random() * Math.PI * 2,
            speed: speedMin + Math.random() * (speedMax - speedMin),
          });
        }
      }
    };

    const observer = new ResizeObserver(resize);
    observer.observe(container);
    resize();

    const startTime = performance.now();

    const draw = (now) => {
      const elapsed = (now - startTime) / 1000;
      const { width, height } = container.getBoundingClientRect();
      ctx.clearRect(0, 0, width, height);

      ctx.save();
      ctx.globalAlpha = opacity;

      for (let i = 0; i < dots.length; i++) {
        const d = dots[i];
        const wave = 0.5 + 0.5 * Math.sin(elapsed * d.speed * speedScale + d.phase);
        const alpha = 0.15 + wave * 0.85;

        ctx.beginPath();
        ctx.arc(d.x, d.y, radius, 0, Math.PI * 2);

        if (wave > 0.78) {
          ctx.shadowColor = glowColor;
          ctx.shadowBlur = 8 * (wave - 0.78) * 4.5;
          ctx.fillStyle = glowColor;
        } else {
          ctx.shadowBlur = 0;
          ctx.fillStyle = color;
        }

        ctx.globalAlpha = opacity * alpha;
        ctx.fill();
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(draw);
    };

    animationFrameId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
    };
  }, [gap, radius, color, glowColor, opacity, speedMin, speedMax, speedScale]);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}