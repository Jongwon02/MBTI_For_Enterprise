import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SurveyClient } from "@/components/survey/SurveyClient";

export const metadata = { title: "진단하기 | Biz-DNA" };

export default function DiagnosisPage() {
  return (
    <>
      <SiteHeader active="Diagnosis" />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">Diagnosis</span>
          <h1>기업 경영진단</h1>
          <p>기본진단(기업정보·DNA 24문항·성장단계·경영목표)을 마치면 유형과 단계를 먼저 확인합니다. 이어서 정밀진단(경영역량 64문항·성장계획)을 하면 전략과 보고서를 받습니다. 응답은 자동으로 저장됩니다.</p>
        </div>
      </section>
      <SurveyClient />
      <SiteFooter />
    </>
  );
}
