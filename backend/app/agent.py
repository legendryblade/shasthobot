import re
from datetime import date

from .knowledge import TESTS, lookup


def _parse_value(s: str) -> float | None:
    s = s.strip().replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def _parse_range(s: str) -> tuple[float | None, float | None]:
    m = re.findall(r"-?\d+(?:\.\d+)?", s)
    if len(m) >= 2:
        return float(m[0]), float(m[1])
    if len(m) == 1:
        return None, float(m[0])
    return None, None


def _classify(test: dict, value: float) -> str:
    low = test.get("low")
    high = test.get("high")
    if low is not None and value < low:
        return "low"
    if high is not None and value > high:
        return "high"
    return "normal"


def tool_parse_report(report_text: str) -> dict:
    """Extract test name, value, unit from free-form report text."""
    results = []
    lines = report_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Pattern 1: "Name: value unit (range)"
        m = re.match(
            r"^([A-Za-z][A-Za-z0-9\s/\-()\.]{1,50}?)\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z/%0-9\^\.]*)(?:\s*\(?\s*([\d\.\-]+\s*[-–]\s*[\d\.]+)\s*\)?)?",
            line,
        )
        if not m:
            # Pattern 2: "Name    value    unit    range"
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 2:
                name = parts[0].strip().strip(":")
                val = _parse_value(parts[1])
                unit = parts[2].strip() if len(parts) > 2 else ""
                ref = parts[3].strip() if len(parts) > 3 else ""
                m = (name, str(val), unit, ref) if val is not None else None
            else:
                m = None

        if m:
            if isinstance(m, re.Match):
                name, val, unit, ref = m.group(1), float(m.group(2)), m.group(3), m.group(4)
            else:
                name, val, unit, ref = m
                val = _parse_value(str(val))
                if val is None:
                    continue

            kb = lookup(name)
            if kb:
                results.append(
                    {
                        "test_key": kb["name_en"],
                        "name_en": kb["name_en"],
                        "name_bn": kb["name_bn"],
                        "value": val,
                        "unit": unit or kb["unit"],
                        "reference": ref or f"{kb['low']} - {kb['high']}",
                    }
                )
            else:
                results.append(
                    {
                        "test_key": name,
                        "name_en": name,
                        "name_bn": name,
                        "value": val,
                        "unit": unit,
                        "reference": ref or "",
                    }
                )

    return {"tests_found": len(results), "tests": results}


def tool_explain_values(parsed: dict) -> dict:
    explanations = []
    for t in parsed["tests"]:
        kb = TESTS.get(_kb_key(t["name_en"]))
        if not kb:
            explanations.append(
                {
                    "name_en": t["name_en"],
                    "name_bn": t["name_bn"],
                    "value": t["value"],
                    "unit": t["unit"],
                    "status": "unknown",
                    "explanation_bn": "এই পরীক্ষার তথ্য আমাদের ডেটাবেসে নেই।",
                    "meaning_bn": "",
                }
            )
            continue

        status = _classify(kb, t["value"])
        if status == "high":
            meaning = kb["high_bn"]
            meaning_en = kb["high_en"]
        elif status == "low":
            meaning = kb["low_bn"]
            meaning_en = kb["low_en"]
        else:
            meaning = "আপনার মান স্বাভাবিক পরিসরে আছে।"
            meaning_en = "Your value is within the normal range."

        explanations.append(
            {
                "name_en": kb["name_en"],
                "name_bn": kb["name_bn"],
                "value": t["value"],
                "unit": t["unit"],
                "reference": f"{kb['low']} - {kb['high']} {kb['unit']}",
                "status": status,
                "what_bn": kb["what_bn"],
                "meaning_bn": meaning,
                "meaning_en": meaning_en,
                "explanation_bn": f"{kb['what_bn']} {kb['name_bn']} এর স্বাভাবিক মান {kb['low']} - {kb['high']} {kb['unit']}। {meaning}",
            }
        )
    return {"explanations": explanations}


def _kb_key(name_en: str) -> str | None:
    for key, v in TESTS.items():
        if v["name_en"].lower() == name_en.lower():
            return key
    return None


def tool_flag_abnormal(explanations: dict) -> dict:
    abnormal = []
    for e in explanations["explanations"]:
        if e["status"] in ("high", "low"):
            abnormal.append(
                {
                    "name_en": e["name_en"],
                    "name_bn": e["name_bn"],
                    "value": e["value"],
                    "unit": e["unit"],
                    "reference": e.get("reference", ""),
                    "status": e["status"],
                    "severity": "moderate",
                    "action_bn": "এই মান স্বাভাবিকের বাইরে। ডাক্তারকে দেখান।",
                }
            )
    return {
        "total": len(explanations["explanations"]),
        "normal": len(explanations["explanations"]) - len(abnormal),
        "abnormal": len(abnormal),
        "items": abnormal,
    }


def _find_test(name_en: str) -> dict | None:
    """Find a knowledge-base test by its English display name."""
    target = name_en.lower().strip()
    for kb in TESTS.values():
        if kb["name_en"].lower() == target:
            return kb
    # Fallback: match if the name_en contains the kb name
    for kb in TESTS.values():
        if kb["name_en"].lower() in target:
            return kb
    return None


def tool_suggest_questions(abnormal: dict, explanations: dict) -> dict:
    questions = []
    seen = set()
    for item in abnormal["items"]:
        kb = _find_test(item["name_en"])
        if kb and kb["name_en"] not in seen:
            seen.add(kb["name_en"])
            questions.append(
                {
                    "test": item["name_en"],
                    "question_bn": kb["question_bn"],
                    "question_en": kb["question_en"],
                }
            )
    if not questions:
        questions.append(
            {
                "test": "general",
                "question_bn": "আমার সামগ্রিক স্বাস্থ্য অবস্থা কী?",
                "question_en": "How is my overall health?",
            }
        )
    return {"questions": questions}


def run_investigation(report_text: str, patient_name: str = "") -> dict:
    """Bounded agent loop: parse -> explain -> flag -> suggest."""
    steps = []

    parsed = tool_parse_report(report_text)
    steps.append({"tool": "parse_report", "input": {"chars": len(report_text)}, "output": parsed})

    explained = tool_explain_values(parsed)
    steps.append({"tool": "explain_values", "input": {"tests": parsed["tests_found"]}, "output": explained})

    flagged = tool_flag_abnormal(explained)
    steps.append({"tool": "flag_abnormal", "input": {"tests": parsed["tests_found"]}, "output": flagged})

    questions = tool_suggest_questions(flagged, explained)
    steps.append({"tool": "suggest_questions", "input": {"abnormal": flagged["abnormal"]}, "output": questions})

    return {
        "patient_name": patient_name,
        "tests_found": parsed["tests_found"],
        "explanations": explained["explanations"],
        "flagged": flagged,
        "questions": questions["questions"],
        "steps": steps,
        "mode": "deterministic",
        "disclaimer": "এটি শুধুমাত্র তথ্য উপস্থাপন। এটি চিকিৎসা নির্ণয় নয়। সবসময় একজন যোগ্য চিকিৎসকের পরামর্শ নিন।",
        "disclaimer_en": "This is for information only. It is not a medical diagnosis. Always consult a qualified doctor.",
        "generated_on": date.today().isoformat(),
    }
