import { ResultClient } from "@/components/result/ResultClient";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SITE } from "@/lib/site";

export const metadata = { title: `진단 결과 | ${SITE.name}` };

export default function ResultPage() {
  return (
    <>
      <SiteHeader active="Report" />
      <ResultClient />
      <SiteFooter />
    </>
  );
}
