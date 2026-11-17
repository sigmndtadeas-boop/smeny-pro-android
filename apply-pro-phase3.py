from pathlib import Path
import re
p=Path('smeny_pro_mobile_build/www/index.html')
s=p.read_text(encoding='utf-8')
pattern=r'function reportsPage\(\)\{.*?\}\nfunction duration\('
m=re.search(pattern,s,re.S)
if not m:
    raise SystemExit('Reports page patch target not found')
new=r'''function reportsPage(){
  let prefix=`${db.year}-${String(db.month+1).padStart(2,'0')}`;
  let daysInMonth=new Date(db.year,db.month+1,0).getDate();
  let as=db.assignments.filter(a=>a.date.startsWith(prefix));
  let per=activeEmployees().map(e=>{
    let own=as.filter(a=>a.employeeId===e.id);
    let h=own.reduce((sum,a)=>sum+duration(a.start,a.end),0);
    let fund=(e.weeklyHours||40)*daysInMonth/7;
    let absenceDays=db.absences.filter(a=>a.employeeId===e.id&&a.status==='schváleno').reduce((sum,a)=>{
      let from=a.from>prefix+'-01'?a.from:prefix+'-01';
      let last=prefix+'-'+String(daysInMonth).padStart(2,'0');
      let to=a.to<last?a.to:last;
      if(to<from)return sum;
      return sum+Math.round((new Date(to+'T12:00:00')-new Date(from+'T12:00:00'))/86400000)+1;
    },0);
    return {e,n:own.length,h,d:own.filter(a=>a.type==='D').length,night:own.filter(a=>a.type==='N').length,fund,diff:h-fund,absenceDays};
  });
  let totalHours=per.reduce((n,x)=>n+x.h,0),totalFund=per.reduce((n,x)=>n+x.fund,0),totalAbsences=per.reduce((n,x)=>n+x.absenceDays,0);
  let fmtHours=n=>(Math.round(n*10)/10).toLocaleString('cs-CZ',{maximumFractionDigits:1});
  return pageHead('Statistiky a export','Přehled vytížení zaměstnanců a výstupy pro další použití',`<button class="ghost" onclick="exportCSV()">⇩ Export CSV</button><button class="primary" onclick="exportJSON()">Záloha dat JSON</button>`)+
  `<div class="grid stats"><div class="stat"><div class="label">Odpracované hodiny</div><div class="value">${fmtHours(totalHours)} h</div><div class="hint">Součet naplánovaných směn</div></div><div class="stat"><div class="label">Orientační fond</div><div class="value">${fmtHours(totalFund)} h</div><div class="hint">Podle úvazků a délky měsíce</div></div><div class="stat"><div class="label">Rozdíl proti fondu</div><div class="value">${totalHours-totalFund>=0?'+':''}${fmtHours(totalHours-totalFund)} h</div><div class="hint">Orientační rozdíl, nikoliv mzdový výpočet</div></div><div class="stat"><div class="label">Dny schválených absencí</div><div class="value">${totalAbsences}</div><div class="hint">Včetně překryvu s aktuálním měsícem</div></div></div>`+
  `<div class="card"><div class="cardhead"><h2>Vytížení · ${monthNames[db.month]} ${db.year}</h2><div class="toolbar"><button class="ghost" onclick="window.print()">Tisk / PDF</button></div></div><div class="tablewrap"><table><thead><tr><th>Zaměstnanec</th><th>Směny</th><th>Hodiny</th><th>Denní</th><th>Noční</th><th>Fond*</th><th>Rozdíl</th><th>Absence (dny)</th><th>Vytížení</th></tr></thead><tbody>${per.map(x=>`<tr><td><b>${esc(x.e.name)}</b></td><td>${x.n}</td><td>${fmtHours(x.h)}</td><td>${x.d}</td><td>${x.night}</td><td>${fmtHours(x.fund)}</td><td><span class="pill ${x.diff>=0?'ok':'warn'}">${x.diff>=0?'+':''}${fmtHours(x.diff)} h</span></td><td>${x.absenceDays}</td><td><div class="progress" style="width:110px"><span style="width:${Math.min(100,x.h/Math.max(1,x.fund)*100)}%"></span></div></td></tr>`).join('')}</tbody></table></div><p class="muted small">* Orientační fond se počítá jako týdenní úvazek × počet kalendářních dnů měsíce / 7. Rozdíl není automaticky přesčas ani podklad pro mzdu; nezohledňuje svátky, dovolenou v pracovních dnech ani individuální nerovnoměrné rozvržení.</p></div>`+
  `<div class="card"><div class="cardhead"><h2>Správa dat</h2></div><div class="toolbar"><button class="ghost" onclick="exportJSON()">Exportovat úplnou zálohu</button><button class="ghost" onclick="importJSON()">Importovat zálohu</button><button class="danger" onclick="resetData()">Obnovit ukázková data / vymazat</button></div><p class="muted small">Data jsou uložena pouze v úložišti tohoto zařízení. Pravidelně si stahuj zálohu JSON.</p></div>`
}
function duration('''
s=s[:m.start()]+new+s[m.end():]
p.write_text(s,encoding='utf-8')
print('Phase 3 reports updated.')
