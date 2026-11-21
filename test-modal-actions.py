from pathlib import Path

html = Path("smeny_pro_mobile_build/www/index.html").read_text(encoding="utf-8")
checks = {
    "modal action v2 patch is present": 'id="smeny-pro-modal-actions-top-v2"' in html,
    "save and cancel actions are rendered in the header": "$('#modalHeadActions').innerHTML=actions" in html and "$('#modalFoot').innerHTML=''" in html,
    "modal footer is hidden and body remains scrollable": "#modalFoot{display:none!important}" in html and "#modalBody{order:1!important;flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important" in html,
    "absence form still has a save callback": "function openAbsence(){showModal('Nová absence'" in html and "Absence uložena." in html,
    "JSON import requires explicit confirmation before save": "showModal('Potvrdit import zálohy'" in html and "Obnovit data ze zálohy" in html,
    "import keeps the current database until the confirmation callback": "const previous=db;" in html and "db=candidate;" in html,
    "CSV export requires confirmation": "function exportCSV(){confirmExport('CSV'" in html,
    "XLSX export requires confirmation": "function exportXLSX(){confirmExport('Excel (.xlsx)'" in html,
    "JSON backup export requires confirmation": "function exportJSON(){confirmExport('úplná záloha JSON'" in html,
}
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + " - " + name)
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Modal UI regression checks failed: " + "; ".join(failed))
print(f"All {len(checks)} modal UI regression checks passed.")
