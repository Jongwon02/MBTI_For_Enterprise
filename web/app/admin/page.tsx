import { AdminClient } from "@/components/admin/AdminClient";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata = { title: "관리자 | Biz-DNA", robots: { index: false, follow: false } };

export default function AdminPage() {
  return (
    <>
      <SiteHeader active="Admin" />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">Admin</span>
          <h1>경영자 데이터 탐색</h1>
          <p>통계 활용에 동의한 회원의 진단 결과를 가명으로 모아 실시간으로 살펴봅니다.</p>
        </div>
      </section>
      <AdminClient />
      <SiteFooter />
    </>
  );
}
