from pathlib import Path
import re

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")
marker = "smeny-pro-modal-actions-top-v2"
if marker in s:
    print("Modal action v2 already applied.")
    raise SystemExit(0)

# The original page has a single shared showModal function. Put every action
# button in its header, rather than relying on a footer's visual positioning.
pattern = re.compile(r"function showModal\(title,body,onSave,extra='',headerActions=false\)\{.*?\}function closeModal\(\)")
replacement = r'''function showModal(title,body,onSave,extra='',headerActions=false,saveLabel='Uložit'){
 $('#modalTitle').textContent=title;
 $('#modalBody').innerHTML=body;
 const closeButton='<button class="ghost" type="button" onclick="closeModal()" aria-label="Zavřít">✕</button>';
 let actions='';
 if(headerActions){
  actions=extra+(onSave?'<button class="primary" type="button" id="modalSave">'+esc(saveLabel)+'</button>':'')+closeButton;
 }else{
  actions=extra+(onSave?'<button class="ghost" type="button" onclick="closeModal()">Zrušit</button><button class="primary" type="button" id="modalSave">'+esc(saveLabel)+'</button>':'')+closeButton;
 }
 $('#modalHeadActions').innerHTML=actions;
 $('#modalFoot').innerHTML='';
 $('#modal').classList.add('show');
 if(onSave)$('#modalSave').onclick=onSave;
}function closeModal()'''
s, n = pattern.subn(lambda _: replacement, s, count=1)
if n != 1:
    raise SystemExit(f"Expected to replace exactly one showModal function, replaced {n}.")

# Add a deliberate confirmation step before every export from the reports page.
s = s.replace("function exportXLSX(){", "function exportXLSXNow(){", 1)
s = s.replace("function exportCSV(){", "function exportCSVNow(){", 1)
export_pattern = re.compile(r"async function exportJSON\(\)\{.*?\}function importJSON\(\)", re.S)
export_replacement = "async function exportJSONNow(){await download(JSON.stringify(db,null,2),'smeny-pro-zaloha-'+yearMonth()+'.json','application/json')}\nfunction confirmExport(format,action,saveLabel){showModal('Potvrdit export','<div class=\"notice\">Opravdu chceš připravit export ve formátu <b>'+esc(format)+'</b>? Soubor se uloží do zařízení.</div>',()=>{closeModal();const result=action();if(result&&typeof result.catch==='function')result.catch(e=>toast('Export se nepodařil: '+String(e&&e.message||e)))},'',false,saveLabel||'Exportovat');}\nfunction exportCSV(){confirmExport('CSV',exportCSVNow,'Exportovat CSV')}\nfunction exportXLSX(){confirmExport('Excel (.xlsx)',exportXLSXNow,'Exportovat Excel')}\nfunction exportJSON(){confirmExport('úplná záloha JSON',exportJSONNow,'Stáhnout zálohu')}\nfunction importJSON()"
s, n = export_pattern.subn(lambda _: export_replacement, s, count=1)
if n != 1:
    raise SystemExit(f"Expected to replace exactly one exportJSON function, replaced {n}.")
if "function confirmExport(format,action,saveLabel)" not in s:
    raise SystemExit("Could not add export confirmation flow.")

# Import now previews the selected file and waits for explicit confirmation
# before replacing the current local database.
import_pattern = re.compile(r"function importJSON\(\)\{.*?\}function resetData\(\)", re.S)
import_replacement = r'''function importJSON(){
 let inp=document.createElement('input');inp.type='file';inp.accept='.json,application/json';
 inp.onchange=()=>{
  let f=inp.files?.[0];if(!f)return;
  let rd=new FileReader();
  rd.onerror=()=>toast('Zálohu se nepodařilo přečíst.');
  rd.onload=()=>{
   let candidate;
   try{
    let x=JSON.parse(rd.result);
    if(!x||typeof x!=='object'||!Array.isArray(x.employees)||!Array.isArray(x.positions)||!Array.isArray(x.assignments)||!Array.isArray(x.absences)||!x.rules||typeof x.rules!=='object')throw Error('Neplatná struktura zálohy.');
    candidate={...structuredClone(defaults),...x};
   }catch(e){console.error('Import zálohy selhal',e);toast('Soubor zálohy není platný. Původní data zůstala zachována.');return}
   showModal('Potvrdit import zálohy','<div class="notice"><b>'+esc(f.name)+'</b><br>Soubor obsahuje '+candidate.employees.length+' zaměstnanců, '+candidate.positions.length+' pozic, '+candidate.assignments.length+' směn a '+candidate.absences.length+' absencí.<br><br>Pokud pokračuješ, aktuální data v tomto zařízení budou nahrazena obsahem zálohy. Bez potvrzení zůstanou beze změny.</div>',()=>{
    const previous=db;
    try{
     db=candidate;
     normalizeSmenyDatabase();
     if(!save()){db=previous;toast('Obnovu se nepodařilo uložit. Původní data zůstala zachována.');return}
     closeModal();render('dashboard');toast('Záloha úspěšně obnovena.');
    }catch(e){db=previous;console.error('Import zálohy selhal',e);toast('Import se nepodařil. Původní data zůstala zachována.')}
   },'',false,'Obnovit data ze zálohy');
  };
  rd.readAsText(f);
 };
 inp.click();
}function resetData()'''
s, n = import_pattern.subn(lambda _: import_replacement, s, count=1)
if n != 1:
    raise SystemExit(f"Expected to replace exactly one importJSON function, replaced {n}.")

css = r'''
<style id="smeny-pro-modal-actions-top-v2">
/* All modal actions are physically rendered in the header; only the form body scrolls. */
.modal{display:flex!important;flex-direction:column!important;overflow:hidden!important}
.modalhead{order:0!important;display:flex!important;align-items:flex-start!important;flex-wrap:wrap!important;gap:10px!important;flex:0 0 auto!important}
#modalTitle{flex:1 1 130px;min-width:0}
#modalHeadActions{display:flex!important;flex:0 1 auto!important;flex-shrink:1!important;flex-wrap:wrap!important;align-items:center!important;justify-content:flex-end!important;gap:8px!important;max-width:100%}
#modalHeadActions button{min-height:40px;flex:0 1 auto;white-space:normal}
#modalFoot{display:none!important}
#modalBody{order:1!important;flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;overscroll-behavior:contain!important}
@media(max-width:700px){.modal{max-height:94vh!important}.modalhead{padding:12px!important;gap:8px!important}#modalHeadActions{justify-content:flex-start!important}}
</style>
'''
if "</head>" not in s:
    raise SystemExit("Cannot find </head>; refusing to insert modal styles.")
s = s.replace("</head>", css + "\n</head>", 1)
p.write_text(s, encoding="utf-8")
print("Modal actions now render in the header; JSON import and CSV/XLSX/JSON exports require explicit confirmation.")
