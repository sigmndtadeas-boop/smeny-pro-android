from pathlib import Path
import re
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")

# Extend defaults for weekday-specific staffing and optimization strategy.
s=s.replace("coverageRules:[],excludePairs:[],onlyWeekdays:[]","coverageRules:[],staffingByDay:{},plannerStrategy:'balanced',excludePairs:[],onlyWeekdays:[]",1)
s=s.replace("db.rules.coverageRules=db.rules.coverageRules||[];","db.rules.coverageRules=db.rules.coverageRules||[];db.rules.staffingByDay=db.rules.staffingByDay||{};db.rules.plannerStrategy=db.rules.plannerStrategy||'balanced';",1)

# Add a compact advanced planning panel with per-weekday headcounts and strategy selection.
panel = r"""
function advancedPlannerPanel(){
 const r=db.rules,days=['Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle'];
 return '<div class="card"><div class="cardhead"><div><h2>Pokročilé řízení generátoru</h2><div class="muted small">Počty lidí lze upravit pro každý den zvlášť. Nastavení má přednost před základními počty směn.</div></div><span class="pill ok">Přesné obsazení</span></div>'+
 '<div class="field"><label>Priorita při sestavování směn</label><select id="plannerStrategy">'+
 '<option value="balanced" '+(r.plannerStrategy==='balanced'?'selected':'')+'>Vyvážený plán – hodiny, směny, noci i víkendy</option>'+
 '<option value="hours" '+(r.plannerStrategy==='hours'?'selected':'')+'>Vyrovnávat hlavně odpracované hodiny</option>'+
 '<option value="nights" '+(r.plannerStrategy==='nights'?'selected':'')+'>Spravedlivě rozdělovat noční směny</option>'+
 '<option value="weekends" '+(r.plannerStrategy==='weekends'?'selected':'')+'>Spravedlivě rozdělovat víkendy</option>'+
 '<option value="fewChanges" '+(r.plannerStrategy==='fewChanges'?'selected':'')+'>Upřednostnit návaznost na předchozí směny</option>'+
 '</select></div><div class="divider" style="height:1px;background:var(--line);margin:15px 0"></div>'+
 '<h3 style="font-size:14px;margin:0 0 8px">Přesný počet lidí podle dne</h3><p class="muted small">Nech prázdné = použije se základní počet a případný EX. Zadaná hodnota je konečný počet včetně všech rolí.</p>'+
 '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;padding:8px 0;border-bottom:1px solid var(--line);font-size:11px;color:var(--muted)"><span>Den</span><span>Denní</span><span>Noční</span></div>'+
 days.map((d,i)=>{let v=r.staffingByDay?.[i+1]||{};return '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line)"><b style="font-size:12px">'+d+'</b><input class="staffing-day" data-day="'+(i+1)+'" data-type="D" type="number" min="0" max="50" placeholder="Základ" value="'+(v.D??'')+'"><input class="staffing-day" data-day="'+(i+1)+'" data-type="N" type="number" min="0" max="50" placeholder="Základ" value="'+(v.N??'')+'"></div>'}).join('')+
 '<div class="field full" style="margin-top:12px"><button type="button" class="ghost" onclick="saveAdvancedPlanner()">Uložit pokročilé nastavení</button></div></div>';
}
function saveAdvancedPlanner(){
 const r=db.rules;r.plannerStrategy=document.getElementById('plannerStrategy')?.value||'balanced';r.staffingByDay={};
 document.querySelectorAll('.staffing-day').forEach(x=>{if(x.value.trim()==='')return;const day=x.dataset.day,type=x.dataset.type;r.staffingByDay[day]=r.staffingByDay[day]||{};r.staffingByDay[day][type]=Math.max(0,Math.min(50,Number(x.value)||0));});
 save();toast('Pokročilé nastavení uloženo.');
}
"""
if "function advancedPlannerPanel()" not in s:
    marker="function rulesPage(){"
    if marker not in s: raise SystemExit("Rules page insertion point not found")
    s=s.replace(marker,panel+"\n"+marker,1)
if "${advancedPlannerPanel()}" not in s:
    s=s.replace("${coverageRulesPanel()}<div class=\"card\"><div class=\"cardhead\"><h2>Generování rozpisu</h2>"," ${advancedPlannerPanel()}${coverageRulesPanel()}<div class=\"card\"><div class=\"cardhead\"><h2>Generování rozpisu</h2>",1)

# Persist the strategy when the main rules form is saved.
needle="r.includeLead=$('#includeLead').checked;save();toast('Pravidla uložena.')"
if needle in s:
    s=s.replace(needle,"r.includeLead=$('#includeLead').checked;r.plannerStrategy=$('#plannerStrategy')?.value||r.plannerStrategy||'balanced';save();toast('Pravidla uložena.')",1)

# Replace the old one-pass greedy generator with a constraint-first, backtracking planner.
start=s.find("function generateSchedule(){")
end=s.find("\n\nasync function exportXLSX()",start)
if start<0 or end<0: raise SystemExit("Generator replacement boundaries not found")
generator = r"""
function generateSchedule(){
 saveRules();
 if(document.getElementById('plannerStrategy'))saveAdvancedPlanner();
 const year=db.year,month=db.month,dates=dateRange(year,month),r=db.rules,employees=activeEmployees(),keep=$('#keepLocked')?.checked??true;
 if(!employees.length){toast('Nejdříve přidej zaměstnance.');return}
 const prefix=`${year}-${String(month+1).padStart(2,'0')}`;
 const existing=db.assignments.filter(a=>a.date.startsWith(prefix));
 if(existing.length&&!confirm(`V měsíci už existuje ${existing.length} přiřazení. ${keep?'Uzamčená zůstanou, ostatní budou nahrazena.':'Všechna budou nahrazena.'} Pokračovat?`))return;
 const locked=keep?existing.filter(a=>a.locked):[];
 db.assignments=db.assignments.filter(a=>!a.date.startsWith(prefix)||(keep&&a.locked));
 const issues=[],created=0;
 const employeeById=new Map(employees.map(e=>[e.id,e]));
 const hours=Object.fromEntries(employees.map(e=>[e.id,db.assignments.filter(a=>a.employeeId===e.id).reduce((sum,a)=>sum+duration(a.start,a.end),0)]));
 const counts=Object.fromEntries(employees.map(e=>[e.id,{all:0,night:0,weekend:0,days:new Set()}]));
 for(const a of db.assignments){const c=counts[a.employeeId];if(c){c.all++;if(a.type==='N')c.night++;if([0,6].includes(new Date(a.date+'T12:00:00').getDay()))c.weekend++;c.days.add(a.date)}}
 const startMinutes=t=>Number(t.slice(0,2))*60+Number(t.slice(3,5));
 const isUnavailable=(e,date)=>db.absences.some(a=>a.employeeId===e.id&&a.status!=='zamítnuto'&&a.from<=date&&a.to>=date);
 const getRequiredCount=(date,type,weekend)=>{
   const day=new Date(date+'T12:00:00').getDay(),key=day===0?7:day;
   const custom=r.staffingByDay?.[key]?.[type];
   return custom!==undefined&&custom!==''?Number(custom):Number(type==='D'?r.dayCount:r.nightCount)+(weekend?Number(r.weekendEx||0):Number(r.weekdayEx||0));
 };
 const scoreCandidate=(e,type,date,previous)=>{
   const c=counts[e.id],contract=Math.max(1,Number(e.weeklyHours||40));
   const normalizedHours=hours[e.id]*40/contract;
   let score=normalizedHours*1.1+c.all*2;
   if(r.plannerStrategy==='hours')score=normalizedHours*3+c.all*.2;
   if(r.plannerStrategy==='nights')score=c.night*8+normalizedHours*.35+c.all*.2;
   if(r.plannerStrategy==='weekends')score=c.weekend*9+normalizedHours*.35+c.all*.2;
   if(r.plannerStrategy==='fewChanges')score=normalizedHours*.5+c.all*.2+(previous&&previous.type!==type?5:0)+(previous&&previous.type===type?-3:0);
   if(type==='D'&&previous?.type==='N')score+=12;
   if(e.isLead&&r.includeLead)score-=.2;
   return score;
 };
 const eligible=(e,slot,date,target,chosen)=>{
   const day=new Date(date+'T12:00:00').getDay(),dowKey=day===0?7:day;
   if(e.onlyDay&&target.type==='N'||e.onlyNight&&target.type==='D')return false;
   if(Array.isArray(e.allowedDays)&&!e.allowedDays.includes(dowKey))return false;
   if(!Array.isArray(e.allowedDays)&&e.weekdays&&[0,6].includes(day))return false;
   if(slot.positionId){
     const pos=db.positions.find(p=>p.id===slot.positionId);
     if(pos?.lead){if(!(e.isLead||(e.positions||[]).some(pid=>db.positions.some(p=>p.id===pid&&p.lead))))return false}
     if((e.positions||[]).length&&!(e.positions||[]).includes(slot.positionId))return false;
   }else if(r.includeLead&&slot.lead){if(!(e.isLead||(e.positions||[]).some(pid=>db.positions.some(p=>p.id===pid&&p.lead))))return false}
   else if((e.positions||[]).length&&!e.positions.some(pid=>db.positions.some(p=>p.id===pid&&!p.lead)))return false;
   if(isUnavailable(e,date)||chosen.some(x=>x.employeeId===e.id)||db.assignments.some(a=>a.employeeId===e.id&&a.date===date))return false;
   for(const pair of r.excludePairs||[]){if(pair.includes(e.id)){const other=pair.find(id=>id!==e.id);if(chosen.some(x=>x.employeeId===other)||db.assignments.some(a=>a.employeeId===other&&a.date===date))return false}}
   const prev=db.assignments.filter(a=>a.employeeId===e.id&&a.date<date).sort((a,b)=>b.date.localeCompare(a.date))[0];
   if(prev){
     const gap=(new Date(date+'T12:00:00')-new Date(prev.date+'T12:00:00'))/86400000;
     if(gap===1){
       const rest=24-duration(prev.start,prev.end)+(startMinutes(target.start)-startMinutes(prev.end))/60;
       if(r.avoidNightToDay&&prev.type==='N'&&target.type==='D')return false;
       if(rest<Number(r.minRest||0))return false;
     }
   }
   const max=Number(e.maxConsecutive||r.maxConsecutive||4);
   let streak=0;for(let k=1;k<=max;k++){const pd=new Date(date+'T12:00:00');pd.setDate(pd.getDate()-k);if(db.assignments.some(a=>a.employeeId===e.id&&a.date===iso(pd)))streak++;else break}
   if(streak>=max)return false;
   const cap=Number(e.maxHours||r.maxHours||0);
   if(cap>0&&hours[e.id]+duration(target.start,target.end)>cap)return false;
   return true;
 };
 let totalCreated=0,totalRequired=0;
 for(const d of dates){
   const date=iso(d),weekend=[0,6].includes(d.getDay()),dowKey=d.getDay()===0?7:d.getDay();
   for(const type of ['D','N']){
     const count=getRequiredCount(date,type,weekend),startTime=type==='D'?r.dayStart:r.nightStart,endTime=type==='D'?r.dayEnd:r.nightEnd;
     totalRequired+=count;
     const roleRules=(r.coverageRules||[]).filter(x=>x.type===type&&(x.days||[]).includes(dowKey)&&Number(x.count)>0);
     let slots=[];
     if(roleRules.length){
       roleRules.forEach(rule=>{for(let i=0;i<Number(rule.count);i++)slots.push({positionId:rule.positionId,lead:!!db.positions.find(p=>p.id===rule.positionId)?.lead})});
       if(slots.length!==count){
         issues.push(`${fmt(date)} · ${type==='D'?'Denní':'Noční'}: pravidla rolí požadují ${slots.length} míst, ale nastavený počet je ${count}. Uprav počty nebo pravidla rolí.`);
         continue;
       }
     }else{
       const leadPosition=db.positions.find(p=>p.lead);
       for(let i=0;i<count;i++)slots.push({positionId:i===0&&r.includeLead&&leadPosition?leadPosition.id:null,lead:i===0&&!!r.includeLead});
     }
     const fixed=db.assignments.filter(a=>a.date===date&&a.type===type);
     if(fixed.length>count){issues.push(`${fmt(date)} · ${type==='D'?'Denní':'Noční'}: uzamčených směn je ${fixed.length}, požadováno pouze ${count}.`);continue}
     // Locked assignments satisfy matching role slots first, then generic slots.
     for(const a of fixed){
       let idx=a.positionId?slots.findIndex(x=>x.positionId===a.positionId): -1;
       if(idx<0)idx=slots.findIndex(x=>!x._filled&&!x.positionId);
       if(idx<0)idx=slots.findIndex(x=>!x._filled);
       if(idx>=0)slots[idx]._filled=true;
     }
     const open=slots.filter(x=>!x._filled);
     if(!open.length)continue;
     const target={type,start:startTime,end:endTime};
     const candidatesBySlot=open.map(slot=>({slot,candidates:employees.filter(e=>eligible(e,slot,date,target,[]))}));
     candidatesBySlot.sort((a,b)=>a.candidates.length-b.candidates.length);
     let nodes=0,solution=null;
     const chosen=[];
     const search=depth=>{
       if(depth===candidatesBySlot.length){solution=chosen.slice();return true}
       if(++nodes>25000)return false;
       const item=candidatesBySlot[depth];
       const ranked=item.candidates.filter(e=>eligible(e,item.slot,date,target,chosen)).sort((a,b)=>scoreCandidate(a,type,date,db.assignments.filter(x=>x.employeeId===a.id).sort((x,y)=>y.date.localeCompare(x.date))[0])-scoreCandidate(b,type,date,db.assignments.filter(x=>x.employeeId===b.id).sort((x,y)=>y.date.localeCompare(x.date))[0])||a.name.localeCompare(b.name,'cs'));
       for(const e of ranked){
         const assignment={id:uid(),date,type,employeeId:e.id,positionId:item.slot.positionId||((item.slot.lead?db.positions.find(p=>p.lead)?.id:null)||e.positions?.find(pid=>!db.positions.find(p=>p.id===pid)?.lead)||e.positions?.[0]||db.positions.find(p=>!p.lead)?.id||db.positions[0]?.id),start:startTime,end:endTime,locked:false};
         chosen.push(assignment);
         if(search(depth+1))return true;
         chosen.pop();
       }
       return false;
     };
     if(!search(0)){
       issues.push(`${fmt(date)} · ${type==='D'?'Denní':'Noční'}: nepodařilo se kompletně obsadit směnu. Volných míst: ${open.length}. Zkontroluj dostupnost, kvalifikace, odpočinek a limity.`);
       continue;
     }
     solution.forEach(a=>{db.assignments.push(a);hours[a.employeeId]+=duration(a.start,a.end);const c=counts[a.employeeId];c.all++;if(type==='N')c.night++;if(weekend)c.weekend++;c.days.add(date);totalCreated++});
   }
 }
 db.lastGeneration=new Date().toISOString();save();render('schedule');
 const gaps=issues.length,monthAssigned=db.assignments.filter(a=>a.date.startsWith(prefix)).length;
 showModal('Generování dokončeno',`<div class="grid" style="grid-template-columns:repeat(2,1fr);gap:10px"><div class="rulebox"><b style="font-size:24px">${totalCreated}</b><br>Nově vytvořených míst</div><div class="rulebox"><b style="font-size:24px">${gaps}</b><br>Problémové směny</div></div><p>${gaps?'Některé směny nebylo možné kompletně sestavit. Generátor je označil a nevydává je za obsazené.':'Všechny směny byly sestaveny v požadovaném počtu.'}</p><p class="muted small">Celkem je v měsíci ${monthAssigned} přiřazení. Uzamčené směny byly zachovány.</p>${gaps?`<div style="max-height:220px;overflow:auto;font-size:12px">${issues.map(x=>`<div style="padding:7px;border-bottom:1px solid var(--line)">${esc(x)}</div>`).join('')}</div>`:''}<div class="notice" style="margin-top:14px">Generátor nejprve hledá kompletní sestavu směny a kontroluje všechna tvrdá omezení. Pokud ji nenajde, oznámí konkrétní problém místo vytvoření částečně obsazené směny. Výsledek je stále návrh ke kontrole.</div>`,()=>{closeModal();render('schedule')},'<button class="ghost" onclick="closeModal()">Zavřít</button>');
}
"""
s=s[:start]+generator+s[end:]

# Make validation use day-specific staffing and role rules rather than only global defaults.
old="const expected=(type==='D'?db.rules.dayCount:db.rules.nightCount)+extra;"
new="const dowKey=d.getDay()===0?7:d.getDay(),custom=db.rules.staffingByDay?.[dowKey]?.[type],roleRules=(db.rules.coverageRules||[]).filter(x=>x.type===type&&(x.days||[]).includes(dowKey)&&Number(x.count)>0),expected=custom!==undefined&&custom!==''?Number(custom):(roleRules.length?roleRules.reduce((n,x)=>n+Number(x.count),0):(type==='D'?db.rules.dayCount:db.rules.nightCount)+extra);"
if old in s:s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("Phase 7: constraint-first exact staffing planner, backtracking, weekday headcounts and strategy controls applied.")
