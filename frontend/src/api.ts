export interface Explanation {
  name_en: string;
  name_bn: string;
  value: number;
  unit: string;
  reference: string;
  status: string;
  what_bn: string;
  meaning_bn: string;
  meaning_en: string;
  explanation_bn: string;
}

export interface FlaggedItem {
  name_en: string;
  name_bn: string;
  value: number;
  unit: string;
  reference: string;
  status: string;
  severity: string;
  action_bn: string;
}

export interface Question {
  test: string;
  question_bn: string;
  question_en: string;
}

export interface AnalysisResult {
  investigation_id: number;
  patient_name: string;
  tests_found: number;
  explanations: Explanation[];
  flagged: {
    total: number;
    normal: number;
    abnormal: number;
    items: FlaggedItem[];
  };
  questions: Question[];
  steps: { tool: string; input: unknown; output: unknown }[];
  mode: string;
  disclaimer: string;
  disclaimer_en: string;
  generated_on: string;
}

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => get<{ status: string; app: string }>("/health"),
  analyze: (reportText: string, patientName = "") =>
    post<AnalysisResult>("/analyze", { report_text: reportText, patient_name: patientName }),
};
