import { LogoMark } from "./Logo";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-shell">
        <div>
          <div className="footer-brand"><LogoMark />Biz-DNA</div>
          <p className="footer-copy">
            중소기업 경영진단 플랫폼. 기업 DNA 유형, 성장단계, 경영역량, 성장전략을 진단하고 실행과 재진단까지 연결합니다.
          </p>
        </div>
        <div className="footer-meta">
          <p><strong>서비스명</strong>Biz-DNA (가칭)</p>
          <p><strong>대상</strong>중소기업 · 창업기업 · 성장기업</p>
          <p><strong>운영</strong>미정</p>
          <p><strong>안내</strong>진단모형의 가중치와 기준점은 시범검증 전 가설값입니다.</p>
        </div>
        <div className="footer-bottom">© 2026 Biz-DNA (가칭) · 개발 버전</div>
      </div>
    </footer>
  );
}
