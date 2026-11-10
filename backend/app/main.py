from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import run_investigation
from .db import get_db, init_db

app = FastAPI(title="ShasthoBot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


class AnalyzeRequest(BaseModel):
    report_text: str
    patient_name: str = ""


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ShasthoBot"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not req.report_text.strip():
        raise HTTPException(status_code=400, detail="Report text is required")

    result = run_investigation(req.report_text, req.patient_name)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO investigations (patient_name, report_text, tests_found, abnormal_count, status) VALUES (?,?,?,?,?)",
        (
            req.patient_name,
            req.report_text,
            result["tests_found"],
            result["flagged"]["abnormal"],
            "completed",
        ),
    )
    inv_id = cur.lastrowid
    for i, step in enumerate(result["steps"]):
        conn.execute(
            "INSERT INTO investigation_steps (investigation_id, tool_name, tool_input, tool_output, step_order) VALUES (?,?,?,?,?)",
            (inv_id, step["tool"], str(step["input"]), str(step["output"]), i),
        )
    conn.commit()
    conn.close()

    result["investigation_id"] = inv_id
    return result


@app.get("/api/investigations")
def list_investigations():
    conn = get_db()
    rows = conn.execute("SELECT id, patient_name, tests_found, abnormal_count, created_at FROM investigations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/investigations/{inv_id}")
def get_investigation(inv_id: int):
    conn = get_db()
    inv = conn.execute("SELECT * FROM investigations WHERE id = ?", (inv_id,)).fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Investigation not found")
    steps = conn.execute(
        "SELECT * FROM investigation_steps WHERE investigation_id = ? ORDER BY step_order", (inv_id,)
    ).fetchall()
    conn.close()
    return {"investigation": dict(inv), "steps": [dict(s) for s in steps]}


# Serve frontend
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}")
    def spa(path: str):
        f = FRONTEND_DIST / path
        if f.exists() and f.is_file():
            return FileResponse(f)
        return FileResponse(FRONTEND_DIST / "index.html")
