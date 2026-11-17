from pathlib import Path
import re

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

if "function validateSchedule()" not in s:
    validation = r"""
function validateSchedule(){
  const prefix=`${db.year}-${String(db.month+1).padStart(2,'0')}`;
  const monthAssignments=db.assignments.filter(a=>a.date.startsWith(prefix));
  const issues=[];
  const add=(level,date,message)=>issues.push({level,date,message});
  const employees=new Map(db.employees.map(e=>[e.id,e]));
  const byEmployee=new Map();
  for(const e of db.employees)byEmployee.set(e.id,[]);
  for(const a of monthAssignments){
    const e=employees.get(a.employeeId);
    if(!e){add('error',a.date,'Přiřazení odkazuje na neexistujícího zaměstnance.');continue;}
    if(!byEmployee.has(e.id))byEmployee.set(e.id,[]);
    byEmployee.get(e.id).push(a);
    if(e.onlyDay&&a.type==='N')add('error',a.date,e.name+': zaměstnanec smí pouze denní směny.');
    if(e.onlyNight&&a.type==='D')add('error',a.date,e.name+': zaměstnanec smí pouze noční směny.');
    if(e.weekdays&&[0,6].includes(new Date(a.date+'T12:00:00').getDay()))add('error',a.date,e.name+': zaměstnanec smí pracovat pouze Po–Pá.');
    if(e.positions?.length&&!e.positions.includes(a.positionId))add('error',a.date,e.name+': přiřazená pozice neodpovídá jeho kvalifikaci.');
    if(db.absences.some(x=>x.employeeId===e.id&&x.status!=='zamítnuto'&&x.from<=a.date&&x.to>=a.date))add('error',a.date,e.name+': směna koliduje s evidovanou absencí nebo čekající žádostí.');
  }
  for(const d of dateRange(db.year,db.month)){
    const ds=iso(d),weekend=[0,6].includes(d.getDay()),extra=weekend?(db.rules.weekendEx||0):(db.rules.weekdayEx||0);
    for(const type of ['D','N']){
      const arr=monthAssignments.filter(a=>a.date===ds&&a.type===type);
      const expected=(type==='D'?db.rules.dayCount:db.rules.nightCount)+extra;
      if(arr.length<expected)add('error',ds,`${type==='D'?'Denní':'Noční'} směna: chybí ${expected-arr.length} z ${expected} požadovaných míst.`);
      if(arr.length>expected)add('warning',ds,`${type==='D'?'Denní':'Noční'} směna: obsazeno ${arr.length} míst, požadováno ${expected}.`);
      if(db.rules.includeLead&&arr.length&&!arr.some(a=>employees.get(a.employeeId)?.isLead||db.positions.find(p=>p.id===a.positionId)?.lead))add('warning',ds,`${type==='D'?'Denní':'Noční'} směna: není přiřazen vedoucí.`);
    }
    const people=new Set();
    for(const a of monthAssignments.filter(x=>x.date===ds)){
      if(people.has(a.employeeId))add('error',ds,`${employees.get(a.employeeId)?.name||'Zaměstnanec'} má v jednom dni více směn.`);
      people.add(a.employeeId);
    }
    for(const pair of db.rules.excludePairs||[]){
      if(pair.length===2&&pair.every(id=>monthAssignments.some(a=>a.date===ds&&a.employeeId===id))){
        add('error',ds,`Zakázaná dvojice ${employees.get(pair[0])?.name||'?' } + ${employees.get(pair[1])?.name||'?'} je ve stejný den naplánována.`);
      }
    }
  }
  for(const [id,arr] of byEmployee){
    const e=employees.get(id);if(!e||!arr.length)continue;
    arr.sort((a,b)=>a.date.localeCompare(b.date)||a.start.localeCompare(b.start));
    let streak=0,prevDate='';
    for(let i=0;i<arr.length;i++){
      const a=arr[i];
      if(a.date===prevDate)continue;
      const prevDay=new Date(prevDate+'T12:00:00'),curDay=new Date(a.date+'T12:00:00');
      const gap=prevDate?(curDay-prevDay)/86400000:99;
      streak=gap===1?streak+1:1;
      const max=e.maxConsecutive||db.rules.maxConsecutive||4;
      if(streak>max)add('error',a.date,`${e.name}: ${streak} pracovních dnů za sebou (limit ${max}).`);
      if(i>0){
        const prev=arr[i-1];
        if(prev.date!==a.date){
          const dayGap=(new Date(a.date+'T12:00:00')-new Date(prev.date+'T12:00:00'))/86400000;
          const startMin=t=>Number(t.slice(0,2))*60+Number(t.slice(3,5));
          const rest=(dayGap*1440+startMin(a.start)-startMin(prev.start)-duration(prev.start,prev.end)*60)/60;
          if(rest<(db.rules.minRest||0))add('error',a.date,`${e.name}: odpočinek mezi směnami je jen ${Math.max(0,rest).toFixed(1)} h (minimum ${db.rules.minRest} h).`);
          if(prev.type==='N'&&a.type==='D'&&db.rules.avoidNightToDay)add('error',a.date,`${e.name}: nepovolený přechod z noční na denní směnu.`);
        }
      }
      prevDate=a.date;
    }
    const total=arr.reduce((sum,a)=>sum+duration(a.start,a.end),0);
    const cap=e.maxHours||db.rules.maxHours;
    if(cap>0&&total>cap)add('warning','',`${e.name}: plán ${total.toFixed(1)} h překračuje měsíční limit ${cap} h.`);
  }
  return issues;
}
function runScheduleCheck(){
  const issues=validateSchedule(),errors=issues.filter(x=>x.level==='error'),warnings=issues.filter(x=>x.level==='warning');
  const body=`<div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:14px"><div class="rulebox"><b style="font-size:24px">${errors.length}</b><br>Chyby</div><div class="rulebox"><b style="font-size:24px">${warnings.length}</b><br>Upozornění</div></div>`+
    (issues.length?`<div style="max-height:52vh;overflow:auto">${issues.slice(0,100).map(x=>`<div style="padding:9px 4px;border-bottom:1px solid var(--line);font-size:12px"><span class="pill ${x.level==='error'?'bad':'warn'}">${x.level==='error'?'CHYBA':'UPOZORNĚNÍ'}</span> <b>${x.date?esc(fmt(x.date)):'Souhrn'}</b><div style="margin-top:4px">${esc(x.message)}</div></div>`).join('')}</div>${issues.length>100?'<p class="muted small">Zobrazeno prvních 100 zjištění.</p>':''}`:'<div class="rulebox">Nebyly nalezeny žádné chyby ani upozornění. Rozpis prošel dostupnými automatickými kontrolami.</div>');
  showModal('Kontrola rozpisu · '+monthNames[db.month]+' '+db.year,body,null,'<button class="primary" onclick="closeModal()">Hotovo</button>');
}
"""
    marker = "function generateSchedule(){"
    if marker not in s:
        raise SystemExit("Could not find generator insertion point")
    s = s.replace(marker, validation + "\n" + marker, 1)

old_button = '<button class="ghost" onclick="exportCSV()">⇩ CSV</button><button class="primary" onclick="nav(\'rules\')">✦ Generovat</button>'
new_button = '<button class="ghost" onclick="exportCSV()">⇩ CSV</button><button class="ghost" onclick="runScheduleCheck()">✓ Kontrola</button><button class="primary" onclick="nav(\'rules\')">✦ Generovat</button>'
if old_button in s and 'onclick="runScheduleCheck()"' not in s:
    s=s.replace(old_button,new_button,1)

old_rules = '<button class="primary" onclick="generateSchedule()">✦ Vygenerovat rozpis</button>'
new_rules = '<button class="ghost" onclick="runScheduleCheck()">✓ Zkontrolovat rozpis</button><button class="primary" onclick="generateSchedule()">✦ Vygenerovat rozpis</button>'
if old_rules in s and 'Zkontrolovat rozpis' not in s:
    s=s.replace(old_rules,new_rules,1)

# Normalize workload by contracted hours and balance nights/weekends as part of the optimizer.
old_score = "candidates.sort((a,b)=>{let score=e=>{let h=workload[e.id]||0,n=db.assignments.filter(a=>a.employeeId===e.id&&a.type==='N').length,all=db.assignments.filter(a=>a.employeeId===e.id).length;return (r.preferFair?h*1.1:0)+all*3+n*1.5+(nightLast[e.id]&&target.type==='D'?20:0)+(e.isLead&&slot===0&&r.includeLead?-12:0)+Math.random()*.2};return score(a)-score(b)});"
new_score = "candidates.sort((a,b)=>{let score=e=>{let own=db.assignments.filter(a=>a.employeeId===e.id),contract=Math.max(1,e.weeklyHours||40),load=(workload[e.id]||0)*40/contract,n=own.filter(a=>a.type==='N').length,weekends=own.filter(a=>[0,6].includes(new Date(a.date+'T12:00:00').getDay())).length,all=own.length;return (r.preferFair?load*1.1:0)+all*3+n*1.5+(r.weekendCount?weekends*2.5:0)+(nightLast[e.id]&&target.type==='D'?20:0)+(e.isLead&&slot===0&&r.includeLead?-12:0)};return score(a)-score(b)||a.name.localeCompare(b.name,'cs')});"
if old_score in s:
    s=s.replace(old_score,new_score,1)
elif new_score not in s:
    raise SystemExit("Could not find optimizer scoring expression")

p.write_text(s,encoding="utf-8")
print("Phase 1: fairer planner and schedule validation added.")
