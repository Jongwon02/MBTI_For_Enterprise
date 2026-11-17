import { LoginForm } from "@/components/auth/LoginForm";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata = { title: "로그인 | Biz-DNA" };

export default function LoginPage() {
  return (
    <>
      <SiteHeader />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">Sign in</span>
          <h1>로그인</h1>
          <p>회원으로 진단하면 응답이 내 계정에 저장됩니다. 가입 없이 게스트로도 진단할 수 있습니다.</p>
        </div>
      </section>
      <div className="auth-body"><LoginForm /></div>
      <SiteFooter />
    </>
  );
}
