import type { Metadata } from "next";
import { SITE } from "@/lib/site";
import "./globals.css";
import "./styles/site.css";
import "./styles/survey.css";
import "./styles/result.css";
import "./styles/account.css";
import "./styles/sosang.css";

export const metadata: Metadata = {
  title: `${SITE.name} | 소상공인 경영진단`,
  description: SITE.description,
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
