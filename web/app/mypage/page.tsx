import { MyPageClient } from "@/components/mypage/MyPageClient";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata = { title: "마이페이지 | Biz-DNA" };

export default function MyPage() {
  return (
    <>
      <SiteHeader active="MyPage" />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">My Page</span>
          <h1>마이페이지</h1>
          <p>중간저장한 진단을 이어서 하고, 최종저장한 진단평가지를 다시 확인합니다.</p>
        </div>
      </section>
      <MyPageClient />
      <SiteFooter />
    </>
  );
}
