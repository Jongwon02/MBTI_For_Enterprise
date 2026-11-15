import { ResultClient } from "@/components/result/ResultClient";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata = { title: "진단 결과 | Biz-DNA" };

export default function ResultPage() {
  return (
    <>
      <SiteHeader active="Report" />
      <ResultClient />
      <SiteFooter />
    </>
  );
}
