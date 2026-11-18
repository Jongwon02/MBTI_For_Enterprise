# Biz-DNA website design system (borrowed from the Vista Consulting Group site)

References: the 2 capture PDFs in `홈페이지양식/` (home, business areas) and the HTML/CSS of https://vistacg.co.kr/ (analyzed 2026-11-16).

## 0. Borrowing principles

**Take layout, color system, typography, component shapes, and motion; do not take content or brand assets.**

| Take | Do not take |
| --- | --- |
| Full-screen sections, scroll snap, right-side dot navigation | VCG logo, company name, slogan ("We will open the way to happiness.") and other copy |
| Header that turns from transparent into a glass pill | Photos used on the site (replace with our own picks) |
| Eyebrow labels (`— OUR PHILOSOPHY`), large bold headings, blue emphasis words | Logos of public agencies (MSS, local governments, etc.). Never use logos of organizations we have no partnership with |
| White cards with a gradient top line, black stats section, sub-page hero + left sidebar | Track-record numbers (e.g. "1,214억"). Biz-DNA has no measured statistics, so never invent numbers |

The reference site is also Nuxt + Tailwind + Pretendard. Our stack (Next.js + Tailwind + Pretendard) can reproduce the same style directly.

## 1. Design tokens

### Color

| Token | Value | Use (on the original site) |
| --- | --- | --- |
| `--primary` | `#1d1d1f` | Default body and heading text |
| `--blue` | `#0071e3` | Accent: eyebrows, emphasis words, active dot, hover, number units |
| `--blue-deep` | `#0068d9` / `#0c4f9a` | Darker hover blue, chip text |
| `--gray-bg` | `#f5f5f7` | Sub-page body background, office cards |
| `--gray-text` | `#86868b` | Secondary paragraphs |
| `--black` | `#020202` / `#000` | Hero and stats section background |
| `--navy` | `#0a1628` | Start of the sub-page hero gradient |
| `--footer` | `#0f0f11` | Footer |
| `--section-light` | `#f9f9f9`, `#f7f7f8` | Philosophy and partner section backgrounds |
| `--chip-bg` / `--chip-text` | `#e8f3ff` / `#0d4e96` | Tag chips |
| `--line-light` | `rgba(0,0,0,.08)` | Dividers |
| Slate family | `#0f172a`, `#334155`, `#475569`, `#64748b` | Card body text |

> Consistent with the earlier CLAUDE.md direction of "navy, blue, teal". The web uses the palette above, and PDF reports use the same blue (`#0071e3`) and navy (`#0a1628`). 2.0's teal `#0D838B` remains only as a secondary chart color.

### Typography

- Font: **Pretendard** (`cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css`), fallback `system-ui, -apple-system, Segoe UI, sans-serif`
- Headings are weight 800 with tight tracking (`letter-spacing: -.04em ~ -.06em`). Korean text uses `word-break: keep-all`.

| Element | Size | Notes |
| --- | --- | --- |
| Hero h1 | `clamp(3rem, 7vw, 5.6rem)` | Line height 1.07 |
| Section h2 | `clamp(2.4rem, 5vw, 4rem)` – `4.6rem` | Line height 1.08–1.18 |
| Sub-page h1 | `clamp(2rem, 4vw, 3rem)` | |
| Lead paragraph | `clamp(1.05rem, 2vw, 1.45rem)` | `--gray-text`, line height 1.72 |
| Eyebrow | 15px / 800 / `letter-spacing .18em` / uppercase | 34px × 1px blue line in front |
| Nav links | 14px / 700 / `.06em` / uppercase | |
| Chips | `.78rem` / 800 | |

### Shape, shadow, motion

- Container: `width: min(1280px, 100%)`, sub-page side padding `8%`
- Radii: cards 30px, contact panel 34px, logo cards 20px, small cards 14px, chips and buttons 999px
- Card shadow: `0 18px 40px #10182814`, on hover `0 28px 56px #1018281f`
- Reveal `.reveal`: `opacity 0 → 1`, `translateY(42px) → 0`, `1.85s cubic-bezier(.2,1,.3,1)`
- Sub-page entry: `pageEnterUp .72s cubic-bezier(.22,1,.36,1)`; sidebar and content rise in sequence at 0.04 / 0.12 / 0.18 s
- Disable animations under `prefers-reduced-motion`

## 2. Layout patterns

### Home: full-screen section scroll
- On desktop, `scroll-snap-type: y mandatory` snaps each `100vh` section. **At 900px and below, snapping is off** and normal scrolling applies (`section { padding: 96px 20px 34px }`).
- Fixed **dot navigation** on the right (11px circles; the active dot is blue and scaled 1.55×; hover shows the section name). Dots turn dark over light sections.

### Header
- Default: fixed at the top, transparent background, white text, `padding 32px`. Logo, 5 uppercase menu items, white pill CTA.
- On scroll (`.scrolled`) it becomes a **glass pill**: `background #ffffffb8`, `backdrop-filter: saturate(180%) blur(18px)`, `border-radius 999px`, dark text, black CTA.
- Menu hover: a 2px underline grows from the left. Dropdowns hold sub-menus.
- Mobile: menu and CTA hidden, hamburger button → accordion menu (`border-radius 18px` groups).

### Sub-pages
- **Sub hero**: 380px tall, navy gradient + photo (multiply), eyebrow and h1 at bottom left.
- **Body**: `--gray-bg` background. Sticky left sidebar (section name + menu; active item has white background and a 3px blue bar) + content on the right.
- Content cards: 3-column grid (`vcg-card-grid--business`), number badge, title, description, tag chips at the bottom.

### Footer
- `#0f0f11` background, 2 columns (logo / address, CEO, business registration number, contact), copyright line below. Floating round social buttons (52px) at bottom right.

## 3. Section mapping: Vista home → Biz-DNA home

| # | Vista section | Background | Biz-DNA section | Content |
| --- | --- | --- | --- | --- |
| 1 | Hero | Black + photo | **Hero** | Eyebrow `BIZ-DNA DIAGNOSIS`, large heading (e.g. "우리 회사의 경영 DNA를 찾아드립니다"), one-line description, 2 CTAs "무료 기본진단 시작" / "진단 방법 보기", scroll indicator |
| 2 | Our Philosophy | `#f9f9f9` + photo on the right | **Why Biz-DNA** | Not a score-only diagnosis but a "growth path fitted to type, stage, and constraints". PRD section 2's four questions (what type / which stage / what obstacle / which strategy) as blue emphasis words |
| 3 | Core Capabilities (carousel of 5 cards + flow chips) | Light blue gradient | **Diagnosis structure** | Flow chips: company info → basic → full → results & report → execution & re-diagnosis. 5 cards: ① DNA type (16) ② growth stage (S1–S5) ③ 8 competences ④ tailored growth strategies (12) ⑤ report & re-diagnosis |
| 4 | Proven Impact (black, 4 numbers) | Black | **Model at a glance** | 4 stat boxes as the **model spec**: 16 types / 8 competences / 5 stages / 12 strategies (or 100 items). No usage numbers until measured statistics exist |
| 5 | Partners (2 rows of infinitely scrolling logos) | `#f7f7f8` | **16 DNA Types** | **16 type cards** (4-letter code + type name) instead of logo cards, with the same infinite scroll. Hover shows the basic growth strategy. Notice that types are not ranked |
| 6 | Office & Contact | White + black panel | **Start / Contact** | Left: start-diagnosis card, institution/consultant adoption inquiry card. Right black panel: contact, agency information |
| 7 | Footer | `#0f0f11` | Footer | Service name, operator info, "pilot model, hypothetical values" notice, privacy policy link |

## 4. Sitemap (draft)

Like Vista, the top menu has 5 uppercase English items and a CTA.

| Menu | Sub-pages | Layout |
| --- | --- | --- |
| ABOUT | About Biz-DNA · how it works · model (4 axes, 8 competences, 5 stages, 12 strategies) | Sub-page + sidebar |
| DNA TYPES | 16-type list · type detail | Card grid (4×4); detail as sub-page |
| DIAGNOSIS | Company info · basic · full | Survey layout (section 5) |
| REPORT | Result dashboard · report download · history and re-diagnosis | Dashboard (login required) |
| NOTICE | Notices · FAQ | Sub-page list |
| CTA `진단 시작` | Login/sign-up → diagnosis | |

Logged-in consultants, agencies, and admins get an extra header menu (P1). Implemented so far: a "관리자" link for admins (`/admin`).

## 5. Applying it to key screens

### Survey (FR-03)
- A low sub hero (240px) showing "기본진단 · DNA 유형 (1/4)". Body on `--gray-bg`.
- The sticky left sidebar becomes the **step navigation** (DNA 4 axes → 8 competence domains → growth plan). Completed steps get the blue bar; the current step a white background.
- Item cards: white, 30px radius, 4px blue gradient line on top. DNA items place the two tendency phrases at both ends with 5 pill buttons in between. Competence items use a 5-point pill scale.
- A fixed bottom bar (previous / interim save / next) and a progress bar.

### Result dashboard (FR-10)
- Top: **black section** (Impact style): DNA 4-letter code at hero size, type name, growth stage, total score and grade as 4 stat boxes.
- Below, white cards on `--gray-bg`: DNA 4-axis bars (boundary zone 40–60 shaded), 8-competence radar, growth-stage progress bar (S1–S5), 3 priority strategies (number badge + reasons + action chips), deferred strategies with reasons.
- Chart colors: default `#0071e3`, comparison/secondary series `#0a1628` and `#8fd4ff`, strengths (≥ 70) teal `#0D838B`.

### Responsive breakpoints
- ≤ 1100px: business cards 4 → 3 → 2 columns
- ≤ 900px: snap off, header menu becomes hamburger, dot navigation shrinks
- ≤ 640px: 1-column cards, 16px side gutters, 13px eyebrows

## 6. Images

- Vista overlays dark gradients on Unsplash photos (office, aerial forest, buildings). Biz-DNA uses the same treatment but **with newly chosen photos** (e.g. meetings, manufacturing floors, data imagery). Check licenses, then store them in `web/public/images/`. Never hotlink.
- Consider abstract SVG graphics with DNA, helix, or network motifs as hero accents.
- The logo mark is `web/components/Logo.tsx`; the browser tab icon `web/app/icon.svg` is the same mark on a white rounded tile.
