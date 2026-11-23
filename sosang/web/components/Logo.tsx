// 중소경영 Logo.tsx를 복사해 강조 색만 메인 색(--accent)으로 바꿨다. app/icon.svg도 같이 바꾼다.
export function LogoMark() {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M9 3c0 7 14 7 14 13S9 22 9 29" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M23 3c0 7-14 7-14 13s14 6 14 13" stroke="var(--accent)" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M11 7.5h10M11 24.5h10M13.5 12h5M13.5 20h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" opacity=".55" />
    </svg>
  );
}
