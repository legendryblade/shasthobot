import { useEffect, useState } from "react";
import { api, AnalysisResult } from "./api";

const SAMPLES = [
  {
    label: "CBC (normal)",
    text: `Complete Blood Count (CBC)

Hemoglobin: 14.2 g/dL (12-16)
WBC: 7.5 x10^9/L (4-11)
RBC: 4.8 x10^12/L (4-5.5)
Platelet: 250 x10^9/L (150-450)
PCV: 42% (36-48)
ESR: 10 mm/hr (0-20)`,
  },
  {
    label: "CBC (anemia + infection)",
    text: `Complete Blood Count (CBC)

Hemoglobin: 9.8 g/dL (12-16)
WBC: 14.2 x10^9/L (4-11)
RBC: 3.5 x10^12/L (4-5.5)
Platelet: 180 x10^9/L (150-450)
PCV: 30% (36-48)
ESR: 35 mm/hr (0-20)`,
  },
  {
    label: "Diabetes panel",
    text: `Diabetes Panel

Blood Glucose (Fasting): 8.4 mmol/L (3.9-6.1)
HbA1c: 7.8% (4.0-6.5)
Creatinine: 95 µmol/L (44-133)
Uric Acid: 480 µmol/L (120-420)`,
  },
  {
    label: "Lipid + liver",
    text: `Lipid Profile & Liver Function

Total Cholesterol: 6.8 mmol/L (0-5.2)
Triglycerides: 2.9 mmol/L (0-1.7)
SGOT / AST: 55 U/L (0-40)
SGPT / ALT: 68 U/L (0-41)
Creatinine: 110 µmol/L (44-133)`,
  },
];

export default function App() {
  const [reportText, setReportText] = useState("");
  const [patientName, setPatientName] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"results" | "questions" | "agent">("results");
  const [health, setHealth] = useState<{ status: string; app: string } | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(String(e)));
  }, []);

  async function analyze() {
    if (!reportText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.analyze(reportText, patientName);
      setResult(r);
      setTab("results");
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">স</div>
          <div className="logo-text">
            Shastho<span>Bot</span>
          </div>
        </div>
        <div className="header-badge">
          {health ? "Agent ready • Bangla explanations" : "Connecting..."}
        </div>
      </header>

      <main className="main">
        <div className="card">
          <div className="card-title">মেডিকেল রিপোর্ট বিশ্লেষণ</div>
          <div className="card-subtitle">
            Paste your lab report below. ShasthoBot explains each value in Bangla, flags
            abnormal results, and suggests questions for your doctor. It never diagnoses.
          </div>

          <div style={{ marginBottom: 12 }}>
            <input
              type="text"
              placeholder="Patient name (optional)"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "#0f172a",
                color: "var(--text)",
                fontSize: 15,
                outline: "none",
                marginBottom: 10,
              }}
            />
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 6 }}>
                Try a sample report:
              </div>
              {SAMPLES.map((s) => (
                <button key={s.label} className="sample-btn" onClick={() => setReportText(s.text)}>
                  {s.label}
                </button>
              ))}
            </div>
            <textarea
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              placeholder={`Paste your lab report here...\n\nExample:\nHemoglobin: 14.2 g/dL (12-16)\nWBC: 7.5 x10^9/L (4-11)\nBlood Glucose (Fasting): 5.4 mmol/L (3.9-6.1)`}
            />
          </div>

          <button className="btn btn-primary" onClick={analyze} disabled={loading}>
            {loading ? "বিশ্লেষণ চলছে..." : "🔬 বিশ্লেষণ করুন"}
          </button>
        </div>

        {error && (
          <div className="card" style={{ borderColor: "rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.08)" }}>
            <strong style={{ color: "var(--red)" }}>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="spinner" />
            ShasthoBot is analyzing your report...
          </div>
        )}

        {result && !loading && (
          <>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-value">{result.tests_found}</div>
                <div className="stat-label">Tests Found</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{result.flagged.normal}</div>
                <div className="stat-label">Normal</div>
              </div>
              <div className="stat-card">
                <div className="stat-value red">{result.flagged.abnormal}</div>
                <div className="stat-label">Abnormal</div>
              </div>
              <div className="stat-card">
                <div className="stat-value amber">{result.questions.length}</div>
                <div className="stat-label">Questions</div>
              </div>
            </div>

            <div className="tabs">
              <button className={`tab ${tab === "results" ? "active" : ""}`} onClick={() => setTab("results")}>
                বিস্তারিত ব্যাখ্যা
              </button>
              <button className={`tab ${tab === "questions" ? "active" : ""}`} onClick={() => setTab("questions")}>
                ডাক্তারকে জিজ্ঞাসা
              </button>
              <button className={`tab ${tab === "agent" ? "active" : ""}`} onClick={() => setTab("agent")}>
                Agent Log
              </button>
            </div>

            {tab === "results" && (
              <div>
                {result.explanations.map((e, i) => (
                  <div key={i} className={`result-card ${e.status !== "normal" ? "abnormal" : ""}`}>
                    <div className="result-header">
                      <div>
                        <div className="result-name">{e.name_en}</div>
                        <div className="result-name-bn">{e.name_bn}</div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span className={`badge badge-${e.status}`}>
                          {e.status === "normal" ? "Normal" : e.status === "high" ? "High" : e.status === "low" ? "Low" : "Unknown"}
                        </span>
                        <div className={`result-value ${e.status}`}>
                          {e.value} <span style={{ fontSize: 14, fontWeight: 400 }}>{e.unit}</span>
                        </div>
                      </div>
                    </div>
                    <div className="result-meta">
                      Reference: {e.reference || "N/A"}
                    </div>
                    <div className="result-explanation">{e.explanation_bn}</div>
                  </div>
                ))}
              </div>
            )}

            {tab === "questions" && (
              <div className="card">
                <div className="card-title">ডাক্তারকে জিজ্ঞাসা করুন</div>
                <div className="card-subtitle">
                  Questions to ask your doctor based on your report.
                </div>
                {result.questions.map((q, i) => (
                  <div key={i} className="question-card">
                    <div className="question-bn">{q.question_bn}</div>
                    <div className="question-en">{q.question_en}</div>
                  </div>
                ))}
              </div>
            )}

            {tab === "agent" && (
              <div className="card">
                <div className="card-title" style={{ fontSize: 18 }}>
                  Agent Execution Log
                </div>
                <div className="card-subtitle">
                  Bounded tool loop — {result.steps.length} steps, deterministic mode
                </div>
                <div className="agent-steps">
                  {result.steps.map((s, i) => (
                    <div key={i} className="agent-step">
                      <div className="step-num">{i + 1}</div>
                      <div>
                        <span className="step-tool">{s.tool}</span>
                        <span className="step-desc"> — {describeStep(s.tool, s.output)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="disclaimer">
              <strong>⚠ দ্রষ্টব্য</strong>
              {result.disclaimer}
              <br />
              <span style={{ color: "var(--text-muted)" }}>{result.disclaimer_en}</span>
            </div>
          </>
        )}

        {!result && !loading && (
          <div className="empty-state">
            <div className="empty-icon">🩺</div>
            <h2>রিপোর্ট দিন, ব্যাখ্যা পান</h2>
            <p>Paste a lab report above or try a sample to see ShasthoBot in action.</p>
          </div>
        )}
      </main>
    </div>
  );
}

function describeStep(tool: string, output: unknown): string {
  if (Array.isArray(output)) {
    const n = output.length;
    if (tool === "parse_report") return `Parsed ${n} tests from report`;
    if (tool === "explain_values") return `Explained ${n} values in Bangla`;
    if (tool === "flag_abnormal") return `Flagged ${n} abnormal values`;
    if (tool === "suggest_questions") return `Generated ${n} doctor questions`;
    return `Processed ${n} items`;
  }
  if (output && typeof output === "object") {
    const o = output as Record<string, unknown>;
    if (typeof o.tests_found === "number") return `Found ${o.tests_found} tests`;
    if (typeof o.abnormal === "number") return `${o.abnormal} abnormal of ${o.total}`;
  }
  return "Completed";
}
