"use client";

import { useEffect, useState } from "react";

const SECTIONS = [
  { id: "home", label: "Home", tone: "dark" },
  { id: "why", label: "Why", tone: "light" },
  { id: "diagnosis", label: "Diagnosis", tone: "light" },
  { id: "model", label: "Model", tone: "dark" },
  { id: "types", label: "16 Types", tone: "light" },
  { id: "start", label: "Start", tone: "light" },
];

export function DotNav() {
  const [active, setActive] = useState("home");

  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((en) => en.isIntersecting && setActive(en.target.id)),
      { rootMargin: "-45% 0px -45% 0px" },
    );
    SECTIONS.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) io.observe(el);
    });
    return () => io.disconnect();
  }, []);

  const light = SECTIONS.find((s) => s.id === active)?.tone === "light";
  return (
    <nav className={`dot-nav${light ? " on-light" : ""}`} aria-label="섹션 이동">
      {SECTIONS.map((s) => (
        <a key={s.id} href={`#${s.id}`} className={active === s.id ? "active" : ""} aria-label={s.label}>
          <span>{s.label}</span>
        </a>
      ))}
    </nav>
  );
}
