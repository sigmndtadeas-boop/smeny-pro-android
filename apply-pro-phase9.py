from pathlib import Path
import re

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {n}")
    s = s.replace(old, new, 1)

# Persist an explicit policy for incomplete drafts. Default is strict/no partial save.
if "plannerAllowPartial" not in s:
    s = s.replace(
        "plannerStrategy:'balanced',excludePairs:[]",
        "plannerStrategy:'balanced',plannerAllowPartial:false,excludePairs:[]",
        1
    )
    s = s.replace(
        "db.rules.plannerStrategy=db.rules.plannerStrategy||'balanced';",
        "db.rules.plannerStrategy=db.rules.plannerStrategy||'balanced';db.rules.plannerAllowPartial=!!db.rules.plannerAllowPartial;",
        1
    )

# Add the partial-plan option to the advanced planner panel.
old = "'</select></div><div class=\"divider\""
new = "'</select></div><label class=\"checkrow\" style=\"margin-top:10px\"><input id=\"plannerAllowPartial\" type=\"checkbox\" '+(r.plannerAllowPartial?'checked':'')+'> Povolit uložení i částečného návrhu, pokud některé směny nelze obsadit</label><div class=\"divider\""
if "id=\"plannerAllowPartial\"" not in s:
    if old not in s:
        raise SystemExit("Advanced planner strategy panel anchor not found")
    s = s.replace(old, new, 1)

old = "r.plannerStrategy=document.getElementById('plannerStrategy')?.value||'balanced';r.staffingByDay={};"
new = "r.plannerStrategy=document.getElementById('plannerStrategy')?.value||'balanced';r.plannerAllowPartial=!!document.getElementById('plannerAllowPartial')?.checked;r.staffingByDay={};"
replace_once(old, new, "Persist partial-plan policy")

# Replace the previous day-by-day greedy planner with a staged, day-level constraint solver.
start = s.find("function generateSchedule(){")
end = s.find("\n\nasync function exportXLSX()", start)
if start < 0 or end < 0:
    raise SystemExit("Generator replacement boundaries not found")

generator = r"""
function plannerMinutes(t){return Number(t.slice(0,2))*60+Number(t.slice(3,5))}
function plannerInterval(a){
 const start=Date.parse(a.date+'T00:00:00')+plannerMinutes(a.start)*60000;
 let end=Date.parse(a.date+'T00:00:00')+plannerMinutes(a.end)*60000;
 if(end<=start)end+=86400000;
 return {start,end};
}
function plannerRestHours(a,b){
 const x=plannerInterval(a),y=plannerInterval(b);
 return (y.start-x.end)/3600000;
}
function commitPartialPlan(){
 const pending=window.__smenyPendingPlan;
 if(!pending)return;
 const before=window.__smenyBeforePlan;
 db=pending;
 if(!save()){db=before;window.__smenyPendingPlan=null;window.__smenyBeforePlan=null;render('schedule');return}
 window.__smenyPendingPlan=null;window.__smenyBeforePlan=null;
 closeModal();render('schedule');toast('Částečný návrh byl uložen. Neobsazená místa zůstala označena v kontrole.');
}
function generateSchedule(){
 saveRules();
 if(document.getElementById('plannerStrategy'))saveAdvancedPlanner();
 const before=db,work=structuredClone(db),year=work.year,month=work.month,r=work.rules;
 const dates=dateRange(year,month),employees=work.employees.filter(e=>e.active!==false);
 const keep=$('#keepLocked')?.checked??true,prefix=String(year)+'-'+String(month+1).padStart(2,'0');
 if(!employees.length){toast('Nejdříve přidej aktivní zaměstnance.');return}
 const existing=work.assignments.filter(a=>String(a.date||'').startsWith(prefix));
 if(existing.length&&!confirm('V měsíci už existuje '+existing.length+' přiřazení. '+(keep?'Uzamčené zůstanou, ostatní budou nahrazeny.':'Všechna budou nahrazena.')+' Pokračovat?'))return;
 const locked=keep?existing.filter(a=>a.locked):[];
 work.assignments=work.assignments.filter(a=>!String(a.date||'').startsWith(prefix)||(keep&&a.locked));
 const issues=[],employeeMap=new Map(employees.map(e=>[e.id,e]));
 const hours=Object.fromEntries(employees.map(e=>[e.id,work.assignments.filter(a=>a.employeeId===e.id).reduce((n,a)=>n+duration(a.start,a.end),0)]));
 const totals=Object.fromEntries(employees.map(e=>[e.id,{all:0,night:0,weekend:0}]));
 for(const a of work.assignments){const t=totals[a.employeeId];if(t){t.all++;if(a.type==='N')t.night++;if([0,6].includes(new Date(a.date+'T12:00:00').getDay()))t.weekend++}}
 const unavailable=(e,date)=>work.absences.some(a=>a.employeeId===e.id&&a.status!=='zamítnuto'&&a.from<=date&&a.to>=date);
 const dayKey=d=>d.getDay()===0?7:d.getDay();
 const required=(date,type,d)=>{
   const k=dayKey(d),custom=r.staffingByDay?.[k]?.[type];
   const rules=(r.coverageRules||[]).filter(x=>(work.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(k)&&Number(x.count)>0);
   const roleTotal=rules.reduce((n,x)=>n+Number(x.count),0);
   return custom!==undefined&&custom!==''?Math.max(0,Number(custom)):(roleTotal?roleTotal:Number(type==='D'?r.dayCount:r.nightCount)+(d.getDay()===0||d.getDay()===6?Number(r.weekendEx||0):Number(r.weekdayEx||0)));
 };
 const shiftFor=(date,type,positionId)=>{
   const pos=work.positions.find(p=>p.id===positionId);
   const actualType=pos?.shiftType||type;
   return {date,type:actualType,start:pos?.start||(actualType==='D'?r.dayStart:r.nightStart),end:pos?.end||(actualType==='D'?r.dayEnd:r.nightEnd),positionId};
 };
 const employeeShifts=e=>work.assignments.filter(a=>a.employeeId===e.id).sort((a,b)=>a.date.localeCompare(b.date)||a.start.localeCompare(b.start));
 const resolveSlot=(e,slot,date)=>{
   const typed=(e.positions||[]).map(id=>work.positions.find(p=>p.id===id)).filter(p=>p&&(!p.shiftType||p.shiftType===slot.shiftType));
   let pos=slot.positionId?work.positions.find(p=>p.id===slot.positionId):(slot.lead?typed.find(p=>p.lead):typed.find(p=>!p.lead)||typed[0]);
   if(!pos&&!slot.positionId)pos=work.positions.find(p=>(!p.shiftType||p.shiftType===slot.shiftType)&&(slot.lead?p.lead:!p.lead));
   return {...slot,positionId:pos?.id||slot.positionId||null,target:shiftFor(date,slot.shiftType,pos?.id||slot.positionId)};
 };
 const eligible=(e,slot,date,chosen)=>{
   if(!e||e.active===false||unavailable(e,date))return false;
   const target=slot.target,k=dayKey(new Date(date+'T12:00:00'));
   if((e.onlyDay&&target.type==='N')||(e.onlyNight&&target.type==='D'))return false;
   if(Array.isArray(e.allowedDays)&&!e.allowedDays.includes(k))return false;
   if(!Array.isArray(e.allowedDays)&&e.weekdays&&[0,6].includes(new Date(date+'T12:00:00').getDay()))return false;
   if(slot.lead&&!e.isLead&&!((e.positions||[]).some(id=>work.positions.some(p=>p.id===id&&p.lead))))return false;
   if(slot.positionId&&(e.positions||[]).length&&!(e.positions||[]).includes(slot.positionId))return false;
   if(!slot.lead&&!slot.positionId&&(e.positions||[]).length&&!e.positions.some(id=>work.positions.some(p=>p.id===id&&!p.lead&&(!p.shiftType||p.shiftType===target.type))))return false;
   if(chosen.some(a=>a.employeeId===e.id)||work.assignments.some(a=>a.employeeId===e.id&&a.date===date))return false;
   for(const pair of r.excludePairs||[]){
     if(pair.includes(e.id)){const other=pair.find(id=>id!==e.id);if(chosen.some(a=>a.employeeId===other)||work.assignments.some(a=>a.employeeId===other&&a.date===date))return false}
   }
   const proposed={...target,date,employeeId:e.id};
   const all=employeeShifts(e);
   for(const a of all){
     const gap=Math.abs((Date.parse(date+'T12:00:00')-Date.parse(a.date+'T12:00:00'))/86400000);
     if(gap===0)return false;
     const old=plannerInterval(a),next=plannerInterval(proposed);
     if(next.start<old.end&&old.start<next.end)return false;
     if(a.date<date&&plannerRestHours(a,proposed)<Number(r.minRest||0))return false;
     if(a.date>date&&plannerRestHours(proposed,a)<Number(r.minRest||0))return false;
     if(r.avoidNightToDay&&a.date<date&&a.type==='N'&&proposed.type==='D'&&gap===1)return false;
     if(r.avoidNightToDay&&a.date>date&&proposed.type==='N'&&a.type==='D'&&gap===1)return false;
   }
   const allDates=[...all.map(a=>a.date),...chosen.filter(a=>a.employeeId===e.id).map(a=>a.date),date].sort();
   let streak=0,previous=null;
   for(const ds of allDates){streak=previous&&((Date.parse(ds+'T12:00:00')-Date.parse(previous+'T12:00:00'))/86400000===1)?streak+1:1;if(ds===date&&streak>Number(e.maxConsecutive||r.maxConsecutive||4))return false;previous=ds}
   const cap=Number(e.maxHours||r.maxHours||0);
   if(cap>0&&hours[e.id]+duration(target.start,target.end)>cap)return false;
   return true;
 };
 const score=(e,type,date)=>{
   const t=totals[e.id],contract=Math.max(1,Number(e.weeklyHours||40)),normalized=hours[e.id]*40/contract;
   let v=normalized*1.1+t.all*2;
   if(r.plannerStrategy==='hours')v=normalized*3+t.all*.2;
   if(r.plannerStrategy==='nights')v=t.night*8+normalized*.35+t.all*.2;
   if(r.plannerStrategy==='weekends')v=t.weekend*9+normalized*.35+t.all*.2;
   if(r.plannerStrategy==='fewChanges'){
     const prev=employeeShifts(e).filter(a=>a.date<date).at(-1);
     v=normalized*.5+t.all*.2+(prev&&prev.type!==type?5:0)+(prev&&prev.type===type?-3:0);
   }
   return v+(e.isLead&&r.includeLead?-.2:0);
 };
 let created=0,requiredTotal=0,completeDays=0;
 for(const d of dates){
   const date=iso(d),daySlots=[];
   for(const type of ['D','N']){
     const count=required(date,type,d);requiredTotal+=count;
     const rules=(r.coverageRules||[]).filter(x=>(work.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(dayKey(d))&&Number(x.count)>0);
     let slots=[];
     if(rules.length)rules.forEach(rule=>{for(let i=0;i<Number(rule.count);i++)slots.push({positionId:rule.positionId})});
     else{
       const leadPos=work.positions.find(p=>p.lead&&(!p.shiftType||p.shiftType===type));
       for(let i=0;i<count;i++)slots.push({positionId:i===0&&r.includeLead?leadPos?.id:null,lead:i===0&&!!r.includeLead});
     }
     if(slots.length!==count){issues.push(fmt(date)+' · '+(type==='D'?'Denní':'Noční')+': součet pozic ('+slots.length+') neodpovídá požadovanému počtu ('+count+').');continue}
     const fixed=work.assignments.filter(a=>a.date===date&&a.type===type);
     if(fixed.length>count){issues.push(fmt(date)+' · '+type+': uzamčených směn je více než požadovaných míst.');continue}
     for(const a of fixed){
       let idx=a.positionId?slots.findIndex(x=>!x.filled&&x.positionId===a.positionId):-1;
       if(idx<0)idx=slots.findIndex(x=>!x.filled&&!x.positionId);
       if(idx<0)idx=slots.findIndex(x=>!x.filled);
       if(idx>=0)slots[idx].filled=true;
     }
     slots.filter(x=>!x.filled).forEach(slot=>daySlots.push({...slot,shiftType:type,target:shiftFor(date,type,slot.positionId)}));
   }
   if(issues.some(x=>x.startsWith(fmt(date)+' ·')))continue;
   const candidates=daySlots.map(slot=>({slot,list:employees.filter(e=>eligible(e,resolveSlot(e,slot,date),date,[]))}));
   candidates.sort((a,b)=>a.list.length-b.list.length);
   let nodes=0,solution=null;const chosen=[];
   const solve=depth=>{
     if(depth===candidates.length){solution=chosen.slice();return true}
     if(++nodes>60000)return false;
     const item=candidates[depth],ranked=item.list.map(e=>({e,slot:resolveSlot(e,item.slot,date)})).filter(x=>eligible(x.e,x.slot,date,chosen)).sort((a,b)=>score(a.e,a.slot.shiftType,date)-score(b.e,b.slot.shiftType,date)||a.e.name.localeCompare(b.e.name,'cs'));
     for(const candidate of ranked){
       const e=candidate.e,slot=candidate.slot,assignment={id:uid(),date,type:slot.target.type,employeeId:e.id,positionId:slot.positionId||e.positions?.[0]||work.positions.find(p=>!p.lead)?.id||work.positions[0]?.id,start:slot.target.start,end:slot.target.end,locked:false};
       chosen.push(assignment);
       if(solve(depth+1))return true;
       chosen.pop();
     }
     return false;
   };
   if(!solve(0)){
     issues.push(fmt(date)+' · Nelze kompletně obsadit všechny denní a noční pozice současně. Prověř dostupnost, kvalifikace, odpočinek, absence a limity.');
     continue;
   }
   for(const a of solution){work.assignments.push(a);hours[a.employeeId]+=duration(a.start,a.end);const t=totals[a.employeeId];t.all++;if(a.type==='N')t.night++;if([0,6].includes(d.getDay()))t.weekend++;created++}
   completeDays++;
 }
 // Check rest against already planned shifts after the target month.
 const endDate=iso(new Date(year,month+1,0));
 const outside=work.assignments.filter(a=>a.date>endDate);
 for(const a of work.assignments.filter(a=>a.date.startsWith(prefix))){
   const next=outside.filter(x=>x.employeeId===a.employeeId).sort((x,y)=>x.date.localeCompare(y.date))[0];
   if(next&&plannerRestHours(a,next)<Number(r.minRest||0))issues.push(fmt(a.date)+' · '+(employeeMap.get(a.employeeId)?.name||'Zaměstnanec')+': po poslední směně měsíce není dodržen odpočinek před další směnou.');
 }
 const missing=issues.length>0,allowPartial=!!r.plannerAllowPartial;
 if(missing&&!allowPartial){
   window.__smenyPendingPlan=null;window.__smenyBeforePlan=null;db=before;
   showModal('Rozpis nebyl uložen – nalezeny problémy',
    '<div class="notice">Původní rozpis zůstal beze změny. Generátor nedokázal sestavit všechny směny bez porušení pravidel.</div><p><b>Kompletně sestavené dny:</b> '+completeDays+' / '+dates.length+'</p><p><b>Nově připravená místa:</b> '+created+'</p><div style="max-height:45vh;overflow:auto">'+issues.slice(0,100).map(x=>'<div style="padding:8px 2px;border-bottom:1px solid var(--line);font-size:12px">'+esc(x)+'</div>').join('')+'</div><p class="muted small">Pokud chceš přijmout i neúplný návrh, zapni tuto možnost v Pokročilém řízení generátoru a spusť plánování znovu.</p>',
    null,'<button class="primary" onclick="closeModal()">Zavřít</button>');
   return;
 }
 db=work;
 db.lastGeneration=new Date().toISOString();
 if(!save()){db=before;render('schedule');toast('Uložení selhalo. Původní rozpis byl obnoven.');return}
 render('schedule');
 showModal(missing?'Částečný návrh uložen':'Rozpis úspěšně sestaven',
  '<div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:10px"><div class="rulebox"><b style="font-size:24px">'+created+'</b><br>Nová místa</div><div class="rulebox"><b style="font-size:24px">'+issues.length+'</b><br>Problémy</div></div><p>Kompletně sestaveno '+completeDays+' z '+dates.length+' dnů. Původní uzamčené směny zůstaly zachovány.</p>'+(missing?'<div style="max-height:38vh;overflow:auto">'+issues.slice(0,100).map(x=>'<div style="padding:7px;border-bottom:1px solid var(--line);font-size:12px">'+esc(x)+'</div>').join('')+'</div>':'<div class="rulebox">Všechny požadované směny jsou obsazené.</div>'),
  ()=>{closeModal();render('schedule')},'<button class="ghost" onclick="closeModal()">Zavřít</button>');
}
"""
s = s[:start] + generator + s[end:]
p.write_text(s, encoding="utf-8")
print("Phase 9: staged two-shift constraint solver, cross-midnight rest checks, strict save protection and partial-plan option applied.")
