"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogoMark } from "./Logo";

const NAV = [
  { href: "/#why", label: "About", sub: "소개·진단 방법" },
  { href: "/#types", label: "DNA Types", sub: "16개 유형" },
  { href: "/diagnosis", label: "Diagnosis", sub: "진단하기" },
  { href: "/diagnosis/result", label: "Report", sub: "결과·보고서" },
  { href: "/#start", label: "Notice", sub: "공지·문의" },
];

export function SiteHeader({ active }: { active?: string }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`site-header${scrolled ? " scrolled" : ""}`}>
      <div className="header-shell">
        <Link className="logo" href="/" aria-label="Biz-DNA 처음으로">
          <LogoMark />
          <span>Biz-DNA <small>가칭</small></span>
        </Link>
        <nav className="header-nav" aria-label="주 메뉴">
          {NAV.map((n) => (
            <Link key={n.label} className={`nav-link${active === n.label ? " active" : ""}`} href={n.href}>
              {n.label}
            </Link>
          ))}
        </nav>
        <Link className="header-cta" href="/diagnosis">진단 시작 <span aria-hidden="true">→</span></Link>
        <button
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="mobileMenu"
          aria-label={open ? "메뉴 닫기" : "메뉴 열기"}
          onClick={() => setOpen((v) => !v)}
        >
          <span /><span /><span />
        </button>
      </div>
      {open && (
        <nav className="mobile-menu" id="mobileMenu" aria-label="모바일 메뉴" onClick={() => setOpen(false)}>
          {NAV.map((n) => (
            <Link key={n.label} href={n.href}>{n.label} <span>{n.sub}</span></Link>
          ))}
          <Link className="mobile-cta" href="/diagnosis">진단 시작</Link>
        </nav>
      )}
    </header>
  );
}
