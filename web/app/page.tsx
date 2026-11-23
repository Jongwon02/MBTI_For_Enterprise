import Link from "next/link";
import { LogoMark } from "@/components/Logo";

// 사이트 첫 화면: 중소기업 진단(/sme)과 소상공인 진단(/sosang, 별도 Next.js 앱)을 고른다.
// 소상공인 화면은 다른 앱(vercel.json sosang-web 서비스)이라 Link가 아니라 <a>로 이동한다.
export default function Gate() {
  return (
    <div className="choose">
      <header className="choose-head">
        <span className="choose-logo"><LogoMark />Biz-DNA <small>가칭</small></span>
      </header>
      <main className="choose-main">
        <span className="eyebrow">Business Diagnosis</span>
        <h1>어떤 진단을<br />시작할까요?</h1>
        <p className="choose-lead">사업 형태에 맞는 진단을 골라 주세요. 두 진단은 문항과 결과 구성이 다르고, 회원 계정도 따로 씁니다.</p>

        <div className="choose-grid">
          <Link className="choose-card sme" href="/sme">
            <span className="choose-tag">중소기업 · 창업기업 · 성장기업</span>
            <h2>중소기업<br />경영진단</h2>
            <p>기업 DNA 유형, 성장단계, 8대 경영역량을 진단하고 우선 성장전략 3개를 제시합니다.</p>
            <ul>
              <li>100문항 · 기본진단과 정밀진단</li>
              <li>16개 DNA 유형 · S1~S5 성장단계</li>
              <li>PDF 보고서 · 회원은 진단 이력 저장</li>
            </ul>
            <span className="choose-go">중소기업 진단으로 <i aria-hidden="true">→</i></span>
          </Link>

          <a className="choose-card sosang" href="/sosang">
            <span className="choose-tag">소상공인 · 점포 운영</span>
            <h2>소상공인<br />경영진단</h2>
            <p>업종과 매출·비용을 입력하고 문항에 답하면 가게의 경영유형, 경영역량, 매출·비용 위험과 개선전략을 진단합니다.</p>
            <ul>
              <li>60문항 · 업종별 심화문항 포함</li>
              <li>16개 경영유형 · 8대 경영역량</li>
              <li>30·60·90일 실행계획 · PDF 보고서</li>
            </ul>
            <span className="choose-go">소상공인 진단으로 <i aria-hidden="true">→</i></span>
          </a>
        </div>

        <p className="choose-note">진단모형의 가중치와 기준점은 시범검증 전 가설값입니다.</p>
      </main>
    </div>
  );
}
