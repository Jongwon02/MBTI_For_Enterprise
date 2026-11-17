import { SignupForm } from "@/components/auth/SignupForm";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata = { title: "회원가입 | Biz-DNA" };

export default function SignupPage() {
  return (
    <>
      <SiteHeader />
      <section className="sub-hero">
        <div className="container">
          <span className="eyebrow">Sign up</span>
          <h1>회원가입</h1>
          <p>이메일로 가입하고 진단 결과를 내 계정에 보관하세요.</p>
        </div>
      </section>
      <div className="auth-body"><SignupForm /></div>
      <SiteFooter />
    </>
  );
}
