import { SITE } from "@/lib/site";
import { LogoMark } from "./Logo";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-shell">
        <div>
          <div className="footer-brand"><LogoMark />{SITE.name}</div>
          <p className="footer-copy">
            소상공인 경영진단. 우리 가게의 경영유형과 경영역량, 매출·비용 위험을 스스로 점검하고 먼저 할 일과 90일 실행계획을 받습니다.
          </p>
        </div>
        <div className="footer-meta">
          <p><strong>서비스명</strong>{SITE.name} ({SITE.draftLabel})</p>
          <p><strong>대상</strong>소상공인 · 자영업 점포</p>
          <p><strong>운영</strong>미정</p>
          <p><strong>안내</strong>진단모형의 가중치와 기준점은 시범검증 전 가설값입니다.</p>
        </div>
        <div className="footer-bottom">© 2026 {SITE.name} ({SITE.draftLabel}) · 개발 버전</div>
      </div>
    </footer>
  );
}
