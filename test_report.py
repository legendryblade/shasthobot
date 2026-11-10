import json
import urllib.request

REAL_REPORT = """LABORATORY REPORT
City Diagnostic Center, Dhaka
Patient: Abdul Karim
Age: 45 | Sex: Male
Date: 2026-11-08

HEMATOLOGY
Hemoglobin: 10.8 g/dL (13.2-16.6)
WBC: 13.5 x10^9/L (3.4-9.6)
RBC: 3.9 x10^12/L (4.35-5.65)
Platelet: 120 x10^9/L (135-317)
PCV: 33% (38.3-48.6)
ESR: 45 mm/hr (0-20)

BIOCHEMISTRY
Blood Glucose (Fasting): 8.9 mmol/L (3.9-6.1)
HbA1c: 7.2% (4.0-6.5)
Total Cholesterol: 5.8 mmol/L (0-5.2)
Triglycerides: 2.4 mmol/L (0-1.7)
Creatinine: 100 µmol/L (44-133)
Uric Acid: 450 µmol/L (120-420)
SGOT / AST: 48 U/L (0-40)
SGPT / ALT: 62 U/L (0-41)
"""

req = urllib.request.Request(
    "http://127.0.0.1:8837/api/analyze",
    data=json.dumps({"report_text": REAL_REPORT, "patient_name": "Abdul Karim"}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())

print(f"Tests found: {result['tests_found']}")
print(f"Normal: {result['flagged']['normal']} | Abnormal: {result['flagged']['abnormal']}")
print(f"Questions: {len(result['questions'])}")
print(f"Steps: {[s['tool'] for s in result['steps']]}")
print()
print("=== ABNORMAL VALUES ===")
for item in result["flagged"]["items"]:
    print(f"  {item['name_en']}: {item['value']} ({item['status']}) — {item['action_bn']}")
print()
print("=== DOCTOR QUESTIONS ===")
for q in result["questions"]:
    print(f"  BN: {q['question_bn']}")
    print(f"  EN: {q['question_en']}")
print()
print("=== SAMPLE EXPLANATION (Hemoglobin) ===")
for e in result["explanations"]:
    if e["name_en"].startswith("Hemoglobin"):
        print(f"  {e['explanation_bn']}")
