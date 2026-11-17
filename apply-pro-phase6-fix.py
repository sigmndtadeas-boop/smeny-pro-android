from pathlib import Path
import re
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")

# Phase 6 inserted a call to employeeDayChecks(), but its insertion anchor
# no longer matched after the employee form was upgraded in phase 5.
if "function employeeDayChecks(e)" not in s:
    helper = r"""
function employeeDayChecks(e){
 const all=[1,2,3,4,5,6,7];
 const selected=Array.isArray(e.allowedDays)?e.allowedDays:(e.weekdays?[1,2,3,4,5]:all);
 const names=['Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle'];
 return '<div class="field full"><label>Dostupnost podle dnů v týdnu</label><div class="formgrid">'+names.map((n,i)=>'<label class="checkrow"><input type="checkbox" name="allowedDays" value="'+(i+1)+'" '+(selected.includes(i+1)?'checked':'')+'> '+n+'</label>').join('')+'</div><div class="muted small">Odškrtnuté dny generátor tomuto pracovníkovi nepřidělí.</div></div>';
}
"""
    anchor="function openEmployee(id,draft){"
    if anchor not in s: raise SystemExit("Employee editor anchor not found")
    s=s.replace(anchor,helper+"\n"+anchor,1)

# Persist allowed days with employee data and make an empty selection mean no days.
needle='positions:[...f.querySelectorAll(\'[name="positions"]:checked\')].map(i=>i.value),onlyDay:checked(\'onlyDay\')'
replacement='positions:[...f.querySelectorAll(\'[name="positions"]:checked\')].map(i=>i.value),allowedDays:[...f.querySelectorAll(\'[name="allowedDays"]:checked\')].map(i=>Number(i.value)),onlyDay:checked(\'onlyDay\')'
if needle not in s: raise SystemExit("Employee allowed-days save anchor not found")
s=s.replace(needle,replacement,1)

# Restore the whole assignment editor with explicit named-field access and a
# consistent header Save action. Editing retains the original assignment id.
start=s.find("function openAssignment(")
end=s.find("function editAssignment(id)",start)
if start<0 or end<0: raise SystemExit("Assignment editor boundaries not found")
assignment=r"""
function openAssignment(date=iso(today),id){
 let a=db.assignments.find(x=>x.id===id)||{date,type:'D',employeeId:'',positionId:db.positions[0]?.id||'',start:db.rules.dayStart,end:db.rules.dayEnd,locked:false};
 showModal(id?'Upravit přiřazení':'Přidat směnu',`<form id="asForm" class="formgrid">
 <div class="field"><label>Datum</label><input name="date" type="date" required value="${a.date}"></div>
 <div class="field"><label>Typ směny</label><select name="type"><option value="D" ${a.type==='D'?'selected':''}>Denní</option><option value="N" ${a.type==='N'?'selected':''}>Noční</option></select></div>
 <div class="field"><label>Zaměstnanec</label><select name="employeeId" required><option value="">Vyber zaměstnance</option>${activeEmployees().map(e=>`<option value="${e.id}" ${a.employeeId===e.id?'selected':''}>${esc(e.name)}</option>`).join('')}</select></div>
 <div class="field"><label>Pozice</label><select name="positionId">${db.positions.map(p=>`<option value="${p.id}" ${a.positionId===p.id?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
 <div class="field"><label>Začátek</label><input name="start" type="time" required value="${a.start}"></div>
 <div class="field"><label>Konec</label><input name="end" type="time" required value="${a.end}"></div>
 <div class="field full"><label class="checkrow"><input type="checkbox" name="locked" ${a.locked?'checked':''}> Uzamknout přiřazení proti přegenerování</label></div></form>`,
 ()=>{
   const f=$('#asForm'); if(!f||!f.checkValidity()){f?.reportValidity();return}
   const val=n=>f.querySelector('[name="'+n+'"]')?.value??'';
   const checked=n=>!!f.querySelector('[name="'+n+'"]')?.checked;
   const x={...a,id:a.id||uid(),date:val('date'),type:val('type'),employeeId:val('employeeId'),positionId:val('positionId'),start:val('start'),end:val('end'),locked:checked('locked')};
   const errs=validateAssignment(x,id);
   if(errs.length&&!confirm('Upozornění:\\n'+errs.join('\\n')+'\\n\\nPřesto uložit?'))return;
   const i=db.assignments.findIndex(z=>z.id===x.id),old=i>=0?db.assignments[i]:null;
   if(i>=0)db.assignments[i]=x;else db.assignments.push(x);
   if(!save()){if(i>=0)db.assignments[i]=old;else db.assignments.pop();return}
   closeModal();render('schedule');toast('Směna uložena.');
 },
 id?`<button class="danger" type="button" onclick="deleteAssignment('${id}')">Smazat směnu</button>`:'',
 true
)}
"""
s=s[:start]+assignment+s[end:]
# Ensure manual edits validate the new per-day availability rule too.
needle="if(e.weekdays&&[0,6].includes(new Date(x.date+'T12:00:00').getDay()))errs.push('Zaměstnanec smí pracovat pouze Po–Pá.');"
replacement=needle+"if(Array.isArray(e.allowedDays)&&e.allowedDays.length&&!e.allowedDays.includes(dow(new Date(x.date+'T12:00:00'))+1))errs.push('Zaměstnanec není v tento den dostupný.');"
if needle in s and replacement not in s:s=s.replace(needle,replacement,1)
p.write_text(s,encoding="utf-8")
print("Repaired employee availability editor and shift assignment editor.")
