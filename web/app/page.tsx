import Link from "next/link";
import { DotNav } from "@/components/home/DotNav";
import { HeroHelix } from "@/components/home/HeroHelix";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { DNA_TYPES } from "@/lib/content";

const CARDS = [
  {
    title: "DNA 유형", eng: "DNA Type",
    items: ["4축 24문항 상대선택", "16개 유형 판정", "40~60점 경계 성향 표시", "유형은 우열이 아닌 전략 성향"],
    icon: <path d="M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9M9 7h6M9 17h6" />,
  },
  {
    title: "성장단계", eng: "Growth Stage",
    items: ["6개 지표 가중평균", "단계별 필수 통과조건", "S1 탐색기 ~ S5 규모화기", "업력이 아닌 사업화 상태 기준"],
    icon: <><path d="M3 20h4v-4h4v-4h4V8h4V4" /><path d="M3 20h18" /></>,
  },
  {
    title: "경영역량", eng: "Capabilities",
    items: ["8대 영역 64문항", "영역별 100점 환산", "가중 종합점수와 A~E 등급", "강점과 우선 보완영역"],
    icon: <><path d="M12 2.5l8.5 6.2-3.2 10H6.7l-3.2-10z" /><path d="M12 7.5l4 3-1.5 4.8h-5L8 10.5z" /></>,
  },
  {
    title: "성장전략", eng: "Strategy",
    items: ["12개 전략군 우선순위", "현금흐름·시장검증 규칙 우선", "선행조건 미충족 전략은 보류", "추천 근거와 적용 규칙 공개"],
    icon: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><path d="M12 12l6-6M15 5.5h3.5V9" /></>,
  },
  {
    title: "보고서·재진단", eng: "Report",
    items: ["기본형 보고서 즉시 제공", "정밀형 심층 보고서", "90일 실행계획과 KPI", "3·6·12개월 재진단"],
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
              <span className="eyebrow">Biz-DNA Diagnosis</span>
              <h1>Find the DNA<br />of your business.</h1>
              <p className="lead">
                100개 문항에 답하면 기업 DNA 유형, 성장단계, 8대 경영역량, 우선 성장전략을 한 번에 진단합니다.
                진단을 마치면 바로 기본형 보고서를 받아 볼 수 있습니다.
              </p>
              <div className="hero-actions">
                <Link className="btn btn-primary" href="/diagnosis">무료 기본진단 시작 <span aria-hidden="true">→</span></Link>
                <a className="btn btn-ghost" href="#diagnosis">진단 방법 보기</a>
              </div>
            </div>
            <aside className="sample-card" aria-label="진단 결과 예시">
              <div className="sample-head"><small>Result Preview</small><span className="tag-example">가상기업 예시</span></div>
              <div className="sample-code">GICO</div>
              <div className="sample-name">기술중심 성장형</div>
              <div className="axis-bars" aria-label="4축 성향 점수">
                {([["S", "G", 79.17, true], ["E", "I", 83.33, true], ["C", "N", 33.33, false], ["O", "P", 29.17, false]] as const).map(([l, r, v, right]) => (
                  <div className="axis-mini" key={l}>
                    {right ? <span>{l}</span> : <b>{l}</b>}
                    <div className="axis-mini-track"><i style={{ left: `${v}%` }} /></div>
                    {right ? <b>{r}</b> : <span>{r}</span>}
                  </div>
                ))}
              </div>
              <div className="sample-rows">
                <div className="sample-row"><span>성장단계</span><strong>S3 사업화 안정기</strong></div>
                <div className="sample-row"><span>종합역량</span><strong>61.87점 · C등급</strong></div>
                <div className="sample-row"><span>우선 전략</span><strong>재무·자금관리</strong></div>
              </div>
            </aside>
          </div>
          <div className="scroll-indicator" aria-hidden="true"><small>Scroll</small><div className="scroll-line" /></div>
        </section>

        <section className="why full" id="why">
          <div className="why-visual" aria-hidden="true" />
          <div className="container">
            <span className="eyebrow">Why Biz-DNA</span>
            <h2>점수표가 아니라<br /><span className="accent">성장 경로</span>를 진단합니다.</h2>
            <p className="lead">
              약한 영역을 그대로 고치라고 권하면 오히려 위험할 수 있습니다. 자금이 부족한 기업에 마케팅 확대를 권하는 경우가 그렇습니다.
              Biz-DNA는 기업의 성향과 사업화 단계, 성장을 막는 제약을 함께 보고 지금 먼저 할 일을 알려 드립니다.
            </p>
            <div className="questions">
              <article className="question"><small>Q1 · DNA 유형</small><h3>우리는 어떤 기업인가?</h3><p>4가지 경영성향 축으로 16개 유형 중 하나를 찾습니다.</p></article>
              <article className="question"><small>Q2 · 성장단계</small><h3>지금 어느 단계인가?</h3><p>업력이 아닌 사업화 상태로 S1~S5 단계를 판정합니다.</p></article>
              <article className="question"><small>Q3 · 성장제약</small><h3>무엇이 성장을 막는가?</h3><p>현금흐름, 시장검증, 수익성, 창업자 의존 등 제약을 찾습니다.</p></article>
              <article className="question"><small>Q4 · 성장전략</small><h3>무엇부터 해야 하는가?</h3><p>12개 전략군 가운데 우선 전략 3개와 실행과제를 제시합니다.</p></article>
            </div>
          </div>
        </section>

        <section className="diagnosis full" id="diagnosis">
          <div className="container">
            <div className="biz-top">
              <div>
                <span className="eyebrow">Core Diagnosis</span>
                <h2>진단 구성</h2>
                <p>네 가지 결과는 서로 독립적으로 계산합니다. 결과와 근거를 보고서로 정리하고, 실행과 재진단까지 이어집니다.</p>
              </div>
              <div className="process" aria-label="진단 진행 순서">
                기업정보 <i>→</i> 기본진단 <i>→</i> 정밀진단 <i>→</i> 결과·보고서 <i>→</i> 실행·재진단
                <strong>진단부터 재진단까지 한 곳에서</strong>
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
              <h2>검증할 수 있는 규칙으로<br /><span className="accent">진단합니다.</span></h2>
              <p>
                점수와 유형은 규칙기반 진단엔진이 계산합니다. AI는 결과를 설명할 뿐 점수나 순위를 바꾸지 않습니다.
                모든 추천에는 근거와 적용된 규칙, 문항·가중치 버전이 함께 기록됩니다.
              </p>
              <p className="note">가중치와 기준점은 시범검증 전 가설값이며, 시범진단 결과로 보정합니다.</p>
            </div>
            <div className="stat-grid">
              <div className="stat-box"><h4>진단 문항</h4><div className="num">100<span>문항</span></div><small>DNA 24 · 역량 64 · 계획 12</small></div>
              <div className="stat-box"><h4>기업 DNA 유형</h4><div className="num">16<span>유형</span></div><small>4개 경영성향 축</small></div>
              <div className="stat-box"><h4>경영역량</h4><div className="num">8<span>영역</span></div><small>영역별 8문항</small></div>
              <div className="stat-box"><h4>성장전략</h4><div className="num">12<span>전략군</span></div><small>우선 전략 3개 제시</small></div>
            </div>
          </div>
        </section>

        <section className="types full" id="types">
          <div className="container">
            <div className="types-intro">
              <div><span className="eyebrow">16 DNA Types</span><h2>16가지<br />기업 DNA</h2></div>
              <div>
                <p>성장지향, 경쟁전략, 시장전략, 경영방식 4개 축의 조합으로 유형이 정해집니다. 유형은 우열이 아니며, 재진단 때 바뀔 수 있습니다.</p>
                <div className="axis-legend">
                  <span><b>G</b>성장확장 · <b>S</b>안정내실</span>
                  <span><b>I</b>혁신차별 · <b>E</b>효율경쟁</span>
                  <span><b>N</b>시장개척 · <b>C</b>기존시장집중</span>
                  <span><b>P</b>조직체계 · <b>O</b>창업자주도</span>
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
            <span className="eyebrow">Start &amp; Contact</span>
            <h2>진단 시작하기</h2>
            <div className="contact-grid">
              <div className="contact-left">
                <article className="office-card">
                  <div className="office-mark" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21V9l6-4v4l6-4v4l6-4v16z" /><path d="M7 17h2M11 17h2M15 17h2" /></svg>
                  </div>
                  <div>
                    <h3>기업 진단</h3>
                    <p>기업정보를 입력하고 기본진단에 답하면 유형과 단계를 바로 확인할 수 있습니다. 정밀진단까지 마치면 전략과 실행계획이 담긴 보고서를 받습니다.</p>
                    <div className="chips"><span className="chip">중간저장 지원</span><span className="chip">PDF 보고서</span><span className="chip">PC·모바일</span></div>
                    <Link className="btn btn-dark" href="/diagnosis">무료 기본진단 시작 <span aria-hidden="true">→</span></Link>
                  </div>
                </article>
                <article className="office-card">
                  <div className="office-mark" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18M5 21V10l7-5 7 5v11" /><path d="M9 21v-6h6v6" /></svg>
                  </div>
                  <div>
                    <h3>기관·컨설턴트</h3>
                    <p>운영기관은 소속 기업의 유형 분포와 성장장애를 보고, 컨설턴트는 담당 기업의 결과와 실행과제를 함께 관리합니다.</p>
                    <div className="chips"><span className="chip">업종별 통계</span><span className="chip">담당 기업 관리</span><span className="chip">성과 추적</span></div>
                    <span className="btn btn-line" aria-disabled="true">도입 문의 (준비 중)</span>
                  </div>
                </article>
              </div>
              <aside className="contact-panel">
                <div>
                  <h3>Contact Us</h3>
                  <p className="copy">서비스 도입과 시범진단 참여에 관한 문의를 받습니다.</p>
                </div>
                <div className="contact-list">
                  <div className="contact-item"><small>운영</small><p>운영 주체 확정 후 표시</p></div>
                  <div className="contact-item"><small>연락처</small><p>서비스 개설 후 표시</p></div>
                  <div className="contact-item"><small>이메일</small><p>서비스 개설 후 표시</p></div>
                </div>
                <p className="contact-note">입력하신 기업정보와 진단결과는 해당 기업과 권한을 받은 담당자만 볼 수 있습니다.</p>
              </aside>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
