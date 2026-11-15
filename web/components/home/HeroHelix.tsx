"use client";

import { useEffect, useRef } from "react";

/** 히어로 배경의 DNA 나선. 화면에 보일 때만 그리고, 움직임 줄이기 설정이면 정지 화면만 그린다. */
export function HeroHelix() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, t = 0, raf = 0, visible = true;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const narrow = w < 900;
      const cx = narrow ? w * 0.82 : w * 0.72;
      const amp = narrow ? Math.min(70, w * 0.16) : Math.min(150, w * 0.1);
      const step = 22;
      const count = Math.ceil((h + 80) / step);
      for (let i = 0; i < count; i++) {
        const y = -40 + i * step;
        const phase = i * 0.32 + t;
        const x1 = cx + Math.sin(phase) * amp;
        const x2 = cx + Math.sin(phase + Math.PI) * amp;
        const d1 = (Math.cos(phase) + 1) / 2;
        const d2 = 1 - d1;
        if (i % 2 === 0) {
          ctx.strokeStyle = `rgba(143, 212, 255, ${0.06 + 0.2 * Math.min(d1, d2)})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
        }
        ctx.fillStyle = `rgba(0, 113, 227, ${0.25 + 0.6 * d1})`;
        ctx.beginPath(); ctx.arc(x1, y, 2 + 2.6 * d1, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = `rgba(255, 255, 255, ${0.12 + 0.45 * d2})`;
        ctx.beginPath(); ctx.arc(x2, y, 1.6 + 2.2 * d2, 0, Math.PI * 2); ctx.fill();
      }
    };
    const loop = () => {
      if (!visible) { raf = 0; return; }
      t += 0.008; draw();
      raf = requestAnimationFrame(loop);
    };
    const onResize = () => { resize(); draw(); };
    resize(); draw();
    window.addEventListener("resize", onResize);
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible && !raf && !reduce) raf = requestAnimationFrame(loop);
    });
    io.observe(canvas);
    if (!reduce) raf = requestAnimationFrame(loop);
    return () => { cancelAnimationFrame(raf); io.disconnect(); window.removeEventListener("resize", onResize); };
  }, []);

  return <canvas className="hero-canvas" ref={ref} aria-hidden="true" />;
}
