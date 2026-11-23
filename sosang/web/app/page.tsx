import Link from "next/link";
import { DotNav } from "@/components/home/DotNav";
import { HeroHelix } from "@/components/home/HeroHelix";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { DNA_TYPES } from "@/lib/content";

// 중소경영 홈(web/app/page.tsx)의 구성을 그대로 쓰고 내용을 소상공인용으로 바꿨다.
const CARDS = [
  {
    title: "경영유형", eng: "DNA Type",
    items: ["4축 16문항 양자택일형", "16개 유형 판정", "40~60점 경계 성향 표시", "유형은 우열이 아닌 운영 성향"],
    icon: <path d="M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9M9 7h6M9 17h6" />,
  },
  {
    title: "경영역량", eng: "Capabilities",
    items: ["8대 영역 32문항", "업종별 심화진단 12문항(선택)", "업종별 가중 종합점수·A~E 등급", "강점과 보완 영역"],
    icon: <><path d="M12 2.5l8.5 6.2-3.2 10H6.7l-3.2-10z" /><path d="M12 7.5l4 3-1.5 4.8h-5L8 10.5z" /></>,
  },
  {
    title: "매출·비용", eng: "Finance",
    items: ["항목별 월 비용 입력", "영업잔여액·임대료 비율", "적자·임대료·여유자금 위험", "세무상 이익과 구분 표시"],
    icon: <><path d="M3 20h18" /><path d="M6 16V10M11 16V6M16 16v-4" /></>,
  },
  {
    title: "개선전략", eng: "Strategy",
    items: ["우선 개선전략 3개", "적자면 확장보다 수익구조 먼저", "경영목표·업종 반영", "선정 근거 공개"],
    icon: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><path d="M12 12l6-6M15 5.5h3.5V9" /></>,
  },
  {
    title: "실행계획·보고서", eng: "Action Plan",
    items: ["30·60·90일 실행계획", "기본형 PDF 보고서", "성과지표(KPI) 제시", "재진단(준비 중)"],
    icon: <><path d="M6 2.5h8l4 4v15H6z" /><path d="M14 2.5v4h4M9 13h6M9 17h4" /></>,
  },
];

function TypeCard({ t, hidden }: { t: (typeof DNA_TYPES)[number]; hidden?: boolean }) {
  return (
    <article className="type-card" aria-hidden={hidden || undefined}>
      <div className="type-code">{t[0].split("").map((c, i) => <span key={i}>{c}</span>)}</div>
      <div className="type-name">{t[1]}</div>
      <div className="type-strategy">{t[2]}</div>
    </article>
  );
}

function Track({ list, reverse }: { list: typeof DNA_TYPES; reverse?: boolean }) {
  return (
    <div className={`track${reverse ? " reverse" : ""}`}>
      {list.map((t) => <TypeCard key={t[0]} t={t} />)}
      {list.map((t) => <TypeCard key={`${t[0]}-copy`} t={t} hidden />)}
    </div>
  );
}

export default function Home() {
  return (
    <div className="home-page">
      <SiteHeader />
      <DotNav />
      <main>
        <section className="hero full" id="home">
          <HeroHelix />
          <div className="container hero-grid">
            <div className="hero-copy">
              <span className="eyebrow">Small Business Diagnosis</span>
              <h1>우리 가게,<br />무엇부터 바꿀까요?</h1>
              <p className="lead">
                업종을 고르고 매출·비용과 문항에 답하면 우리 가게의 경영유형, 8대 경영역량, 매출·비용 위험을 진단하고
                먼저 할 개선전략 3가지와 30·60·90일 실행계획을 알려 드립니다. 스마트폰으로도 진단할 수 있습니다.
              </p>
              <div className="hero-actions">
                <Link className="btn btn-primary" href="/diagnosis">무료 자가진단 시작 <span aria-hidden="true">→</span></Link>
                <a className="btn btn-ghost" href="#diagnosis">진단 방법 보기</a>
              </div>
            </div>
            <aside className="sample-card" aria-label="진단 결과 예시">
              <div className="sample-head"><small>Result Preview</small><span className="tag-example">가상 점포 예시</span></div>
              <div className="sample-code">GDRO</div>
              <div className="sample-name">점주주도 차별화형</div>
              <div className="axis-bars" aria-label="4축 성향 점수">
                {([["S", "G", 68.75, true], ["E", "D", 81.25, true], ["R", "N", 31.25, false], ["O", "P", 25, false]] as const).map(([l, r, v, right]) => (
                  <div className="axis-mini" key={l}>
                    {right ? <span>{l}</span> : <b>{l}</b>}
                    <div className="axis-mini-track"><i style={{ left: `${v}%` }} /></div>
                    {right ? <b>{r}</b> : <span>{r}</span>}
                  </div>
                ))}
              </div>
              <div className="sample-rows">
                <div className="sample-row"><span>업종</span><strong>외식업 · 카페</strong></div>
                <div className="sample-row"><span>종합역량</span><strong>48.75점 · D등급</strong></div>
                <div className="sample-row"><span>1순위 전략</span><strong>수익구조 및 현금흐름 개선</strong></div>
              </div>
            </aside>
          </div>
          <div className="scroll-indicator" aria-hidden="true"><small>Scroll</small><div className="scroll-line" /></div>
        </section>

        <section className="why full" id="why">
          <div className="why-visual" aria-hidden="true" />
          <div className="container">
            <span className="eyebrow">Why Self-Diagnosis</span>
            <h2>점수표가 아니라<br /><span className="accent">내일 할 일</span>을 알려 드립니다.</h2>
            <p className="lead">
              약한 곳을 무조건 고치라고 하면 오히려 위험할 수 있습니다. 적자인 가게에 홍보비를 더 쓰라고 권하는 경우가 그렇습니다.
              우리 가게의 운영 성향, 매출·비용 구조, 경영목표를 함께 보고 지금 먼저 할 일을 골라 드립니다.
            </p>
            <div className="questions">
              <article className="question"><small>Q1 · 경영유형</small><h3>우리 가게는 어떤 유형인가?</h3><p>4가지 운영 성향으로 16개 유형 중 하나를 찾습니다.</p></article>
              <article className="question"><small>Q2 · 경영역량</small><h3>무엇을 잘하고 무엇이 약한가?</h3><p>상권·상품·고객·홍보·재무·운영·디지털·미래대응 8개 영역을 봅니다.</p></article>
              <article className="question"><small>Q3 · 매출·비용</small><h3>돈은 남고 있는가?</h3><p>매출에서 비용을 뺀 영업잔여액과 임대료 부담, 여유자금을 확인합니다.</p></article>
              <article className="question"><small>Q4 · 실행계획</small><h3>무엇부터 해야 하는가?</h3><p>우선 개선전략 3개와 30·60·90일에 할 일을 제시합니다.</p></article>
            </div>
          </div>
        </section>

        <section className="diagnosis full" id="diagnosis">
          <div className="container">
            <div className="biz-top">
              <div>
                <span className="eyebrow">Core Diagnosis</span>
                <h2>진단 구성</h2>
                <p>업종에 맞는 가중치와 심화문항으로 계산합니다. 결과와 근거를 PDF 보고서로 정리해 드립니다.</p>
              </div>
              <div className="process" aria-label="진단 진행 순서">
                업종 선택 <i>→</i> 매출·비용 <i>→</i> 경영유형 <i>→</i> 경영역량 <i>→</i> 결과·실행계획
                <strong>응답은 이 기기에 자동 저장됩니다</strong>
              </div>
            </div>
            <div className="cards">
              {CARDS.map((c, i) => (
                <article className="card" key={c.title}>
                  <span className="card-num" aria-hidden="true">{String(i + 1).padStart(2, "0")}</span>
                  <svg className="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{c.icon}</svg>
                  <h3>{c.title}</h3>
                  <div className="eng">{c.eng}</div>
                  <ul>{c.items.map((x) => <li key={x}>{x}</li>)}</ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="model full" id="model">
          <div className="container impact-grid">
            <div>
              <span className="eyebrow">Model at a Glance</span>
              <h2>확인할 수 있는 규칙으로<br /><span className="accent">진단합니다.</span></h2>
              <p>
                점수와 유형, 전략 순위는 규칙기반 진단엔진이 계산합니다. 모든 추천에는 선정 근거와 적용된 규칙,
                문항·가중치 버전이 함께 기록됩니다.
              </p>
              <p className="note">가중치와 기준점은 시범검증 전 가설값이며, 시범진단 결과로 보정합니다.</p>
            </div>
            <div className="stat-grid">
              <div className="stat-box"><h4>진단 문항</h4><div className="num">60<span>문항</span></div><small>유형 16 · 역량 32 · 업종 심화 12</small></div>
              <div className="stat-box"><h4>경영유형</h4><div className="num">16<span>유형</span></div><small>4개 운영 성향 축</small></div>
              <div className="stat-box"><h4>경영역량</h4><div className="num">8<span>영역</span></div><small>업종별 가중치</small></div>
              <div className="stat-box"><h4>업종분류</h4><div className="num">7<span>대분류</span></div><small>20개 경영모델</small></div>
            </div>
          </div>
        </section>

        <section className="types full" id="types">
          <div className="container">
            <div className="types-intro">
              <div><span className="eyebrow">16 DNA Types</span><h2>16가지<br />가게 경영유형</h2></div>
              <div>
                <p>경영목표, 경쟁전략, 고객전략, 운영방식 4개 축의 조합으로 유형이 정해집니다. 유형은 우열이 아니며, 재진단 때 바뀔 수 있습니다.</p>
                <div className="axis-legend">
                  <span><b>G</b>성장확대 · <b>S</b>안정생계</span>
                  <span><b>D</b>차별화 · <b>E</b>가격·효율</span>
                  <span><b>N</b>신규고객 개척 · <b>R</b>단골고객 중심</span>
                  <span><b>P</b>체계적 관리 · <b>O</b>점주 직접운영</span>
                </div>
              </div>
            </div>
          </div>
          <div className="marquee">
            <Track list={DNA_TYPES.slice(0, 8)} />
            <Track list={DNA_TYPES.slice(8)} reverse />
          </div>
        </section>

        <section className="start" id="start">
          <div className="container">
            <span className="eyebrow">Start &amp; Notice</span>
            <h2>진단 시작하기</h2>
            <div className="contact-grid">
              <div className="contact-left">
                <article className="office-card">
                  <div className="office-mark" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10l2-6h14l2 6" /><path d="M4 10v10h16V10" /><path d="M3 10h18M9 20v-6h6v6" /></svg>
                  </div>
                  <div>
                    <h3>점포 자가진단</h3>
                    <p>업종과 매출·비용을 입력하고 문항에 답하면 결과와 실행계획을 바로 확인합니다. 응답은 이 기기(브라우저)에만 저장됩니다.</p>
                    <div className="chips"><span className="chip">자동 저장·이어하기</span><span className="chip">PDF 보고서</span><span className="chip">스마트폰·PC</span></div>
                    <Link className="btn btn-dark" href="/diagnosis">무료 자가진단 시작 <span aria-hidden="true">→</span></Link>
                  </div>
                </article>
                <article className="office-card">
                  <div className="office-mark" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" /></svg>
                  </div>
                  <div>
                    <h3>회원 진단 이력</h3>
                    <p>회원으로 가입하면 진단 이력을 저장하고 다음 진단과 비교할 수 있습니다.</p>
                    <div className="chips"><span className="chip">진단 이력</span><span className="chip">재진단 비교</span></div>
                    <span className="btn btn-line" aria-disabled="true">회원 기능 (준비 중)</span>
                  </div>
                </article>
              </div>
              <aside className="contact-panel">
                <div>
                  <h3>안내</h3>
                  <p className="copy">이 진단은 점주가 직접 답한 내용으로 계산한 예비진단입니다.</p>
                </div>
                <div className="contact-list">
                  <div className="contact-item"><small>데이터</small><p>카드매출·상권 자료와 연결하지 않습니다</p></div>
                  <div className="contact-item"><small>저장</small><p>게스트 응답은 이 기기에만 남습니다</p></div>
                  <div className="contact-item"><small>운영</small><p>운영 주체 확정 후 표시</p></div>
                </div>
                <p className="contact-note">시범 운영 중에는 실제 점포 정보 대신 가상 점포로 체험해 주세요.</p>
              </aside>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
