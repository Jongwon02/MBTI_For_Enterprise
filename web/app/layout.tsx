import type { Metadata } from "next";
import "./globals.css";
import "./styles/site.css";
import "./styles/survey.css";
import "./styles/result.css";
import "./styles/account.css";
import "./styles/admin.css";

export const metadata: Metadata = {
  title: "Biz-DNA | 중소기업 경영진단",
  description: "기업 DNA 유형, 성장단계, 8대 경영역량, 우선 성장전략을 진단하는 중소기업 경영진단 플랫폼",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
