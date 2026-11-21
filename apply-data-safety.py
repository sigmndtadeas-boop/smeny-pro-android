from pathlib import Path

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    s = s.replace(old, new, 1)

# Import into a temporary candidate and restore the live database if persistence fails.
old_import = "function importJSON(){let inp=document.createElement('input');inp.type='file';inp.accept='.json,application/json';inp.onchange=()=>{let f=inp.files[0],rd=new FileReader();rd.onload=()=>{try{let x=JSON.parse(rd.result);if(!x.employees||!x.rules||!x.assignments)throw Error();db={...defaults,...x};save();render('dashboard');toast('Záloha úspěšně obnovena.')}catch(e){toast('Soubor zálohy není platný.')}};rd.readAsText(f)};inp.click()}"
new_import = r"""function importJSON(){
 let inp=document.createElement('input');inp.type='file';inp.accept='.json,application/json';
 inp.onchange=()=>{
  let f=inp.files?.[0];if(!f)return;
  let rd=new FileReader();
  rd.onerror=()=>toast('Zálohu se nepodařilo přečíst.');
  rd.onload=()=>{
   const previous=db;
   try{
    let x=JSON.parse(rd.result);
    if(!x||typeof x!=='object'||!Array.isArray(x.employees)||!Array.isArray(x.positions)||!Array.isArray(x.assignments)||!Array.isArray(x.absences)||!x.rules||typeof x.rules!=='object')throw Error('Neplatná struktura zálohy.');
    const candidate={...structuredClone(defaults),...x};
    db=candidate;
    normalizeSmenyDatabase();
    if(!save()){db=previous;toast('Obnovu se nepodařilo uložit. Původní data zůstala zachována.');return}
    render('dashboard');toast('Záloha úspěšně obnovena.');
   }catch(e){db=previous;console.error('Import zálohy selhal',e);toast('Soubor zálohy není platný. Původní data zůstala zachována.')}
  };
  rd.readAsText(f);
 };
 inp.click();
}"""
replace_once(old_import, new_import, "Safe JSON import")

# Deletions now roll back in-memory changes if local storage refuses the write.
replace_once(
"function deleteAssignment(id){if(!confirm('Smazat toto přiřazení?'))return;db.assignments=db.assignments.filter(a=>a.id!==id);save();closeModal();render('schedule')}",
"function deleteAssignment(id){if(!confirm('Smazat toto přiřazení?'))return;const previous=db.assignments;db.assignments=previous.filter(a=>a.id!==id);if(!save()){db.assignments=previous;return}closeModal();render('schedule');toast('Směna smazána.')}",
"Safe assignment deletion"
)
replace_once(
"function deleteEmployee(id){if(!confirm('Opravdu smazat zaměstnance? Historické přiřazení zůstane zachováno.'))return;db.employees=db.employees.filter(e=>e.id!==id);save();closeModal();render('employees');toast('Zaměstnanec smazán.')}",
"function deleteEmployee(id){if(!confirm('Opravdu smazat zaměstnance? Historické přiřazení zůstane zachováno.'))return;const previous=db.employees;db.employees=previous.filter(e=>e.id!==id);if(!save()){db.employees=previous;return}closeModal();render('employees');toast('Zaměstnanec smazán.')}",
"Safe employee deletion"
)
replace_once(
"function deletePosition(id){if(db.employees.some(e=>(e.positions||[]).includes(id))&&!confirm('Pozici používají zaměstnanci. Opravdu ji smazat?'))return;db.positions=db.positions.filter(p=>p.id!==id);save();closeModal();render('positions')}",
"function deletePosition(id){if(db.employees.some(e=>(e.positions||[]).includes(id))&&!confirm('Pozici používají zaměstnanci. Opravdu ji smazat?'))return;const previous=db.positions;db.positions=previous.filter(p=>p.id!==id);if(!save()){db.positions=previous;return}closeModal();render('positions');toast('Pozice smazána.')}",
"Safe position deletion"
)

# Schedule generation is a transaction: if saving fails, restore the complete pre-generation state.
needle = "function generateSchedule(){\n saveRules();"
replace_once(needle, "function generateSchedule(){\n const beforeGeneration=structuredClone(db);\n saveRules();", "Generation snapshot")
needle = "db.lastGeneration=new Date().toISOString();save();render('schedule');"
replace_once(
needle,
"db.lastGeneration=new Date().toISOString();if(!save()){db=beforeGeneration;render('schedule');toast('Rozpis se nepodařilo uložit. Původní rozpis byl obnoven.');return}render('schedule');",
"Generation rollback"
)

p.write_text(s, encoding="utf-8")
print("Applied transactional JSON import, safe delete rollback, and schedule-generation rollback.")
