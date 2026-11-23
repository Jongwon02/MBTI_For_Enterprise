import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SurveyClient } from "@/components/survey/SurveyClient";
import { SITE } from "@/lib/site";

export const metadata = { title: `자가진단 | ${SITE.name}` };

export default function DiagnosisPage() {
  return (
    <>
      <SiteHeader active="Diagnosis" />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">Self Diagnosis</span>
          <h1>우리 가게 자가진단</h1>
          <p>업종·매출·비용을 입력하고 경영유형 16문항, 경영역량 32문항에 답합니다. 업종별 심화진단과 실적자료는 선택입니다. 응답은 이 기기에 자동으로 저장됩니다.</p>
        </div>
      </section>
      <SurveyClient />
      <SiteFooter />
    </>
  );
}
