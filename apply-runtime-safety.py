from pathlib import Path
import re
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")

# Preserve the original local data in memory before normalizing legacy records.
anchor="function save(){"
if "function normalizeSmenyDatabase()" not in s:
    safety = r"""
// Defensive migration: older app versions may have missing or malformed collections.
function normalizeSmenyDatabase(){
 const array=(v)=>Array.isArray(v)?v:[];
 db.employees=array(db.employees).filter(x=>x&&typeof x==='object').map(e=>({...e,
   id:String(e.id||uid()),name:String(e.name||'Neznámý zaměstnanec'),
   positions:array(e.positions).map(String),active:e.active!==false,
   weeklyHours:Number(e.weeklyHours)||40
 }));
 db.positions=array(db.positions).filter(x=>x&&typeof x==='object').map(p=>({...p,
   id:String(p.id||uid()),name:String(p.name||'Pracovní pozice'),
   color:String(p.color||'#3267e9'),lead:!!p.lead,
   shiftType:p.shiftType==='N'?'N':'D',
   start:/^d{2}:d{2}$/.test(p.start||'')?p.start:(p.shiftType==='N'?(db.rules.nightStart||'18:00'):(db.rules.dayStart||'06:00')),
   end:/^d{2}:d{2}$/.test(p.end||'')?p.end:(p.shiftType==='N'?(db.rules.nightEnd||'06:00'):(db.rules.dayEnd||'18:00'))
 }));
 db.absences=array(db.absences).filter(x=>x&&typeof x==='object');
 db.assignments=array(db.assignments).filter(x=>x&&typeof x==='object').map(a=>({...a,
   id:String(a.id||uid()),date:String(a.date||''),type:a.type==='N'?'N':'D',
   employeeId:String(a.employeeId||''),positionId:String(a.positionId||''),
   start:/^d{2}:d{2}$/.test(a.start||'')?a.start:(a.type==='N'?(db.rules.nightStart||'18:00'):(db.rules.dayStart||'06:00')),
   end:/^d{2}:d{2}$/.test(a.end||'')?a.end:(a.type==='N'?(db.rules.nightEnd||'06:00'):(db.rules.dayEnd||'18:00'))
 }));
 db.swaps=array(db.swaps).filter(x=>x&&typeof x==='object');
 db.rules=db.rules&&typeof db.rules==='object'?db.rules:{...defaults.rules};
 db.rules={...defaults.rules,...db.rules};
 for(const k of ['coverageRules','excludePairs','onlyWeekdays'])db.rules[k]=array(db.rules[k]);
 db.rules.staffingByDay=db.rules.staffingByDay&&typeof db.rules.staffingByDay==='object'?db.rules.staffingByDay:{};
 db.rules.dayCount=Math.max(0,Number(db.rules.dayCount)||0);
 db.rules.nightCount=Math.max(0,Number(db.rules.nightCount)||0);
 db.settings=db.settings&&typeof db.settings==='object'?{...defaults.settings,...db.settings}:{...defaults.settings};
 if(!Number.isInteger(db.month)||db.month<0||db.month>11)db.month=today.getMonth();
 if(!Number.isInteger(db.year)||db.year<2020||db.year>2100)db.year=today.getFullYear();
}
try{window.__smenyRawData=localStorage.getItem('smenypro_db');normalizeSmenyDatabase();}
catch(e){console.error('Migrace uložených dat selhala',e);db=structuredClone(defaults);normalizeSmenyDatabase();}
"""
    if anchor not in s: raise SystemExit("Save function insertion anchor not found")
    s=s.replace(anchor,safety+"\n"+anchor,1)

# Replace render with a guarded renderer. Keep the app shell and provide an actionable error panel.
start=s.find("function render(page='dashboard'){")
end=s.find("\nfunction dashboard(){",start)
if start<0 or end<0: raise SystemExit("Render function boundaries not found")
render = r"""
function render(page='dashboard'){
 try{
  const v=$('#view');if(!v)throw new Error('Chybí kontejner hlavního obsahu (#view).');
  $('#crumb').textContent=({dashboard:'Přehled',schedule:'Rozpis směn',employees:'Zaměstnanci',positions:'Pracovní pozice',rules:'Pravidla a generátor',absences:'Absence a volno',reports:'Statistiky a export',settings:'Nastavení vzhledu',swaps:'Výměna směn'})[page]||'Přehled';
  if(page==='dashboard')v.innerHTML=dashboard();
  else if(page==='employees')v.innerHTML=employeesPage();
  else if(page==='positions')v.innerHTML=positionsPage();
  else if(page==='rules')v.innerHTML=rulesPage();
  else if(page==='schedule')v.innerHTML=schedulePage();
  else if(page==='absences')v.innerHTML=absencesPage();
  else if(page==='swaps')v.innerHTML=swapsPage();
  else if(page==='reports')v.innerHTML=reportsPage();
  else if(page==='settings')v.innerHTML=settingsPage();
  else v.innerHTML=dashboard();
 }catch(err){
  console.error('Chyba při vykreslení obrazovky '+page,err);
  const v=$('#view');
  if(v)v.innerHTML='<div class="card" style="margin:16px;border:1px solid #d84b58"><h2>Obrazovku se nepodařilo načíst</h2><p>Aplikace zachovala uložená data. Zkus obrazovku znovu načíst. Pokud problém přetrvá, exportuj zálohu dat a předej ji podpoře.</p><p class="muted small" id="renderErrorText"></p><div class="actions"><button class="primary" onclick="render(\''+String(page).replace(/[^a-z]/g,'')+'\')">Zkusit znovu</button><button class="ghost" onclick="exportJSON()">Zálohovat data</button></div></div>';
  const detail=$('#renderErrorText');if(detail)detail.textContent=String(err&&err.message||err);
 }
}
"""
s=s[:start]+render+s[end:]
p.write_text(s,encoding="utf-8")
print("Added legacy-data normalization and guarded screen rendering.")
