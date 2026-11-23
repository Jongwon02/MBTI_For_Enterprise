"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SITE } from "@/lib/site";
import { LogoMark } from "./Logo";

// 중소경영 SiteHeader를 복사해 고쳤다. 회원 기능(로그인·마이페이지·관리자)은 계정 분리(CLAUDE.md 3.4) 뒤에 붙인다.
const NAV = [
  { href: "/#why", label: "About", sub: "소개·진단 방법" },
  { href: "/#types", label: "DNA Types", sub: "16개 유형" },
  { href: "/diagnosis", label: "Diagnosis", sub: "진단하기" },
  { href: "/diagnosis/result", label: "Report", sub: "결과·보고서" },
  { href: "/#start", label: "Notice", sub: "안내" },
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
        <Link className="logo" href="/" aria-label={`${SITE.name} 처음으로`}>
          <LogoMark />
          <span>{SITE.short} <em className="logo-tag">{SITE.tag}</em> <small>{SITE.draftLabel}</small></span>
        </Link>
        <nav className="header-nav" aria-label="주 메뉴">
          {NAV.map((n) => (
            <Link key={n.label} className={`nav-link${active === n.label ? " active" : ""}`} href={n.href}>
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="header-right">
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
