from pathlib import Path

html = Path("smeny_pro_mobile_build/www/index.html").read_text(encoding="utf-8")

checks = {
    "legacy positions remain compatible with day and night shifts":
        "p&&(!p.shiftType||p.shiftType===slot.shiftType)" in html,
    "legacy employee qualifications remain compatible with both shift types":
        "(!p.shiftType||p.shiftType===target.type)" in html,
    "partial day assignment fallback is present":
        "const partial=[];" in html and "rankedFor(item,partial)" in html,
    "partial schedules are enabled by default for older databases":
        "plannerAllowPartial:true" in html,
    "a completely empty generation never replaces the current schedule":
        "if(missing&&created===0)" in html,
    "locked assignments are preserved when requested":
        "existing.filter(a=>a.locked)" in html,
    "rest checks include shifts after the generated month":
        "const outside=work.assignments.filter(a=>a.date>endDate)" in html,
}

failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + " - " + name)

if failed:
    raise SystemExit("Planner regression checks failed: " + "; ".join(failed))

print(f"All {len(checks)} planner regression checks passed.")
