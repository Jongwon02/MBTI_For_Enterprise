import type { Likert, Survey } from "./types";

// "예시 점포로 채우기"용 가상 점포. 엔진 기준 사례 3(legacy/mvp_v4/example_cafe_v4.json)과 같은 응답이고,
// 총비용 2,100만원을 항목별로 나눴다(합계가 같으면 결과도 같다). 실제 점포 자료가 아니다.
const seq = (prefix: string, start: number, values: number[]) =>
  Object.fromEntries(values.map((v, i) => [`${prefix}${String(start + i).padStart(2, "0")}`, v as Likert]));

const area = (code: string, values: number[]) => seq(code, 1, values);

export const SAMPLE_SURVEY: Survey = {
  store: {
    name: "동네카페(가상)", region: "서울 ○○구", employees: 2,
    major: "FOOD", biz_model: "M03", sub_industry: "커피숍", sales_mode: "offline", goal: "profit",
  },
  finance: { monthly_sales: 2200, material_cost: 800, labor_cost: 600, rent: 320, other_cost: 380 },
  answers: {
    dna: { ...seq("D", 1, [4, 4, 3, 4]), ...seq("D", 5, [4, 4, 5, 4]), ...seq("D", 9, [2, 2, 2, 3]), ...seq("D", 13, [2, 2, 2, 2]) },
    competence: {
      ...area("A", [3, 3, 4, 2]), ...area("B", [4, 4, 5, 3]), ...area("C", [4, 4, 5, 3]), ...area("D", [2, 2, 3, 1]),
      ...area("E", [2, 2, 3, 1]), ...area("F", [3, 3, 4, 2]), ...area("G", [2, 2, 3, 1]), ...area("H", [3, 3, 4, 2]),
    },
    special: { ...area("FOOD-B", [4, 3, 4, 3]), ...area("FOOD-C", [4, 3, 4, 3]), ...area("FOOD-F", [4, 3, 4, 3]) },
  },
  observations: { months_operating: 30, repeat_rate: 35, positive_cashflow_months: 8, channels: 2, staff: 2, sales_prev: 2024 },
  benchmark: null,
};
