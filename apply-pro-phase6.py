from pathlib import Path
import re
root=Path("smeny_pro_mobile_build")
html=root/"www"/"index.html"
s=html.read_text(encoding="utf-8")
css=r"""
:root{--bg:#071225;--panel:#101e34;--ink:#eaf2ff;--muted:#9aacc7;--line:#263956;--nav:#09152a;--blue:#4b91ff;--blue2:#162f52;--green:#36d98a;--red:#ff6576;--amber:#ffc15c;--shadow:0 14px 36px #0004}
body{background:radial-gradient(ellipse at 15% -10%,#183866 0,transparent 38%),var(--bg);color:var(--ink)}
.sidebar{background:linear-gradient(180deg,#0a1730,#081225);border-right:1px solid #203452}
.brand strong{letter-spacing:.35px}.brand small{color:#8fa5c7}.logo{overflow:hidden;padding:0;background:none!important;box-shadow:0 0 24px #1678ff55}.logo img{display:block;width:100%;height:100%;object-fit:cover}
.nav button{color:#a9bad4;transition:background .18s,color .18s,transform .18s}.nav button.active,.nav button:hover{background:linear-gradient(100deg,#1b3d69,#152c4d);color:#fff}
.topbar{background:#0d1a2fef;border-bottom:1px solid #243754;backdrop-filter:blur(14px)}.crumb{color:#9aacc7}.avatar{background:#183d68;color:#b9d8ff}
.content{padding-top:30px}.pagehead h1{font-size:clamp(23px,3vw,30px);letter-spacing:-.8px}
.stat,.card{background:linear-gradient(145deg,#14243c,#0f1b30);border:1px solid #263b5a;border-radius:17px;box-shadow:var(--shadow)}
.stat{position:relative;overflow:hidden}.stat:after{content:"";position:absolute;width:90px;height:90px;right:-38px;top:-40px;border-radius:50%;background:#3d8dff13}
.stat .value{color:#f4f8ff}.stat .label,.muted,.sub{color:var(--muted)}
button{background:#1b2c46;color:#e7f0ff;border:1px solid #2a4162;border-radius:11px;transition:transform .16s,border-color .16s,background .16s}button:hover{border-color:#4b91ff;transform:translateY(-1px)}
button.primary{background:linear-gradient(120deg,#2879ed,#3f9bff);border:0;box-shadow:0 6px 18px #2677ec44;color:#fff}
button.danger{background:#3b1c2a;color:#ff9aa5;border-color:#653044}button.ghost{background:#12223a;border-color:#2a4162}
.field label{color:#b9c9e1}.field input,.field select,.field textarea,.toolbar input,.toolbar select{background:#0a172b;color:#eaf2ff;border:1px solid #2a4162;border-radius:10px}
.field input:focus,.field select:focus,.field textarea:focus{border-color:#4b91ff;box-shadow:0 0 0 3px #4b91ff25}
.checkrow{color:#c4d2e7}.pill{background:#1c304c;color:#c2d5ef}.pill.ok{background:#123d35;color:#70e3b1}.pill.warn{background:#44351d;color:#ffd27b}.pill.bad{background:#48232d;color:#ff9aa5}
th{background:#12223a;color:#9aacc7}th,td{border-color:#263956}tr:hover td{background:#ffffff06}
.day{background:#101e34;border-color:#2a3e5c}.day.today{border-color:#4b91ff}.shiftbox.dayshift{background:#18345a;color:#a9d0ff}.shiftbox.nightshift{background:#2b2553;color:#c8baff}
.modal{background:#101e34;border:1px solid #2b4160}.modalhead,.modalfoot{border-color:#263956}.toast{background:#eaf2ff;color:#09152a;font-weight:700}
.rulebox{background:#122641;border-color:#294568;color:#c2d3eb}.notice{background:#3b301b;color:#ffda8a;border:1px solid #66502b}
.tabs{border-color:#263956}.tabs button.active{color:#7db5ff;border-color:#4b91ff}.progress{background:#263956}.progress span{background:linear-gradient(90deg,#347df0,#36d98a)}
@media(max-width:900px){.sidebar{position:sticky;top:0;z-index:8;padding:9px 12px 8px;gap:8px;border-right:0;border-bottom:1px solid #263956}.brand{padding:2px 4px}.logo{width:32px;height:32px}.brand strong{font-size:15px}.brand small{font-size:10px}.nav{gap:5px;padding-bottom:2px;scrollbar-width:none}.nav::-webkit-scrollbar{display:none}.nav button{padding:8px 10px;font-size:12px;gap:7px;border:1px solid transparent}.nav button.active{border-color:#315b8d}.topbar{height:48px;padding:0 14px}.content{padding:16px 12px 32px}.pagehead{margin-bottom:16px}.card{padding:15px;margin-bottom:12px}.stat{padding:12px}.stat .value{font-size:22px}}
@media(max-width:520px){.stats{gap:9px}.stat{border-radius:13px}.formgrid{gap:11px}.modalback{padding:9px;align-items:flex-end}.modal{max-height:94vh;border-radius:18px 18px 12px 12px}.modalbody{padding:16px}.modalhead{padding:15px 16px}.modalfoot{padding:12px 16px}.actions{width:100%}.actions button{flex:1}.toolbar{gap:6px}.toolbar button{padding:8px 10px}}
.coverage-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}.coverage-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px;padding-top:15px;border-top:1px solid var(--line)}.coverage-days{display:flex;flex-wrap:wrap;gap:12px}.coverage-days .checkrow{min-width:55px}@media(max-width:520px){.coverage-form{grid-template-columns:1fr 1fr}.coverage-form .field.full{grid-column:1/-1}}
"""
s=s.replace("</style>",css+"\n</style>",1)
s=s.replace('<div class="logo">S</div>','<div class="logo"><img src="app-icon.svg" alt="Směny PRO"></div>',1)
s=s.replace("db.rules={...defaults.rules,...db.rules};","db.rules={...defaults.rules,...db.rules};db.rules.coverageRules=db.rules.coverageRules||[];",1)
s=s.replace("includeLead:true,excludePairs:[]","includeLead:true,coverageRules:[],excludePairs:[]",1)

helper=r'''
function employeeDayChecks(e){
 let selected=Array.isArray(e.allowedDays)?e.allowedDays:(e.weekdays?[1,2,3,4,5]:[1,2,3,4,5,6,7]);
 let names=['Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle'];
 return '<div class="field full"><label>Dostupnost podle dnů v týdnu</label><div class="formgrid">'+names.map((n,i)=>'<label class="checkrow"><input type="checkbox" name="allowedDays" value="'+(i+1)+'" '+(selected.includes(i+1)?'checked':'')+'> '+n+'</label>').join('')+'</div><div class="muted small">Odškrtnuté dny generátor tomuto pracovníkovi nepřidělí.</div></div>';
}
'''
if "function employeeDayChecks(e)" not in s:s=s.replace("function openEmployee(id){",helper+"\nfunction openEmployee(id){",1)
s=s.replace('<div class="field full"><label>Poznámka</label><textarea name="notes"',''+chr(36)+'{employeeDayChecks(e)}<div class="field full"><label>Poznámka</label><textarea name="notes"',1)
s=s.replace("positions:[...f.querySelectorAll('[name=positions]:checked')].map(i=>i.value),onlyDay:","positions:[...f.querySelectorAll('[name=positions]:checked')].map(i=>i.value),allowedDays:[...f.querySelectorAll('[name=allowedDays]:checked')].map(i=>+i.value),onlyDay:",1)

panel=r'''
function coverageRulesPanel(){
 let rules=db.rules.coverageRules||[],days=['Po','Út','St','Čt','Pá','So','Ne'];
 let rows=rules.map((r,i)=>'<div class="coverage-row"><div><b>'+esc(posName(r.positionId))+'</b><div class="muted small">'+(r.type==='D'?'Denní':'Noční')+' · '+(r.days||[]).map(d=>days[d-1]).join(', ')+' · '+r.count+'×</div></div><button class="danger" onclick="removeCoverageRule('+i+')">Odebrat</button></div>').join('');
 let opts=db.positions.map(p=>'<option value="'+p.id+'">'+esc(p.name)+'</option>').join('');
 return '<div class="card"><div class="cardhead"><div><h2>Vlastní obsazení podle rolí</h2><div class="muted small">Nastav, kolik lidí konkrétní role musí být v denní nebo noční směně.</div></div><span class="pill ok">Flexibilní plán</span></div><div class="rulebox" style="margin-bottom:13px">Jakmile pro určitý den nastavíš vlastní pravidla, generátor pro tento den použije přesně tyto role a počty místo obecných počtů směn. Dny bez vlastních pravidel dál používají původní nastavení.</div>'+(rows||'<div class="empty">Zatím používáš základní počty směn. Přidej první pravidlo níže.</div>')+'<div class="coverage-form"><div class="field"><label>Typ směny</label><select id="coverageType"><option value="D">Denní</option><option value="N">Noční</option></select></div><div class="field"><label>Požadovaná role</label><select id="coveragePosition">'+opts+'</select></div><div class="field"><label>Počet pracovníků</label><input id="coverageCount" type="number" min="1" max="30" value="1"></div><div class="field full"><label>Platí pro dny</label><div class="coverage-days">'+days.map((d,i)=>'<label class="checkrow"><input type="checkbox" class="coverageDay" value="'+(i+1)+'" checked> '+d+'</label>').join('')+'</div></div><div class="field full"><button type="button" class="primary" onclick="addCoverageRule()">＋ Přidat pravidlo obsazení</button></div></div></div>';
}
function addCoverageRule(){
 let type=document.getElementById('coverageType').value,positionId=document.getElementById('coveragePosition').value,count=Number(document.getElementById('coverageCount').value),days=[...document.querySelectorAll('.coverageDay:checked')].map(x=>Number(x.value));
 if(!positionId||!days.length||!Number.isInteger(count)||count<1||count>30){toast('Vyber roli, alespoň jeden den a platný počet.');return}
 db.rules.coverageRules=db.rules.coverageRules||[];
 db.rules.coverageRules.push({id:uid(),type:type,positionId:positionId,count:count,days:days});
 save();render('rules');toast('Pravidlo obsazení přidáno.');
}
function removeCoverageRule(i){db.rules.coverageRules.splice(i,1);save();render('rules');}
'''
if "function coverageRulesPanel()" not in s:s=s.replace("function rulesPage(){",panel+"\nfunction rulesPage(){",1)
s=s.replace('<div class="card"><div class="cardhead"><h2>Generování rozpisu</h2>',''+chr(36)+'{coverageRulesPanel()}<div class="card"><div class="cardhead"><h2>Generování rozpisu</h2>',1)

old_targets="targets=[{type:'D',count:r.dayCount,start:r.dayStart,end:r.dayEnd},{type:'N',count:r.nightCount,start:r.nightStart,end:r.nightEnd}]"
new_targets="targets=((r.coverageRules||[]).some(x=>(x.days||[]).includes(dow(d)+1))?['D','N'].map(type=>{let specs=(r.coverageRules||[]).filter(x=>x.type===type&&(x.days||[]).includes(dow(d)+1)).flatMap(x=>Array.from({length:x.count},()=>({positionId:x.positionId})));return {type,count:specs.length,specs,start:type==='D'?r.dayStart:r.nightStart,end:type==='D'?r.dayEnd:r.nightEnd}}).filter(x=>x.count>0):[{type:'D',count:r.dayCount,start:r.dayStart,end:r.dayEnd},{type:'N',count:r.nightCount,start:r.nightStart,end:r.nightEnd}])"
if old_targets not in s:raise SystemExit("Could not find legacy generator target definition")
s=s.replace(old_targets,new_targets,1)
s=s.replace("for(let target of targets){let count=target.count+(weekend?r.weekendEx:r.weekdayEx);for(let slot=0;slot<count;slot++){let candidates=employees.filter(e=>{","for(let target of targets){let count=target.specs?target.count:target.count+(weekend?r.weekendEx:r.weekdayEx);for(let slot=0;slot<count;slot++){let requiredPosition=target.specs?.[slot]?.positionId||null;let candidates=employees.filter(e=>{",1)
old_qual="if(e.positions?.length&&!e.positions.some(pid=>db.positions.some(p=>p.id===pid&&(slot===0&&r.includeLead&&p.lead||!p.lead))))return false;"
new_qual="if(requiredPosition&&!(e.positions||[]).includes(requiredPosition))return false;if(!requiredPosition&&e.positions?.length&&!e.positions.some(pid=>db.positions.some(p=>p.id===pid&&(slot===0&&r.includeLead&&p.lead||!p.lead))))return false;"
if old_qual not in s:raise SystemExit("Could not find legacy qualification filter")
s=s.replace(old_qual,new_qual,1)
s=s.replace("if(e.weekdays&&weekend)return false;","if(Array.isArray(e.allowedDays)&&e.allowedDays.length&&!e.allowedDays.includes(dow(d)+1))return false;if(!Array.isArray(e.allowedDays)&&e.weekdays&&weekend)return false;",1)
old_pos="let positionId=(slot===0&&r.includeLead&&chosen.isLead?db.positions.find(p=>p.lead)?.id:null)||((chosen.positions||[]).find(pid=>!db.positions.find(p=>p.id===pid)?.lead)||chosen.positions?.[0])||db.positions.find(p=>!p.lead)?.id||db.positions[0]?.id;"
new_pos="let positionId=requiredPosition||(slot===0&&r.includeLead&&chosen.isLead?db.positions.find(p=>p.lead)?.id:null)||((chosen.positions||[]).find(pid=>!db.positions.find(p=>p.id===pid)?.lead)||chosen.positions?.[0])||db.positions.find(p=>!p.lead)?.id||db.positions[0]?.id;"
if old_pos not in s:raise SystemExit("Could not find assignment position selector")
s=s.replace(old_pos,new_pos,1)
html.write_text(s,encoding="utf-8")

# App icon: custom calendar/clock with electric blue and green shift arrows.
import cairosvg
icon_svg=r'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#071b43"/><stop offset=".55" stop-color="#071329"/><stop offset="1" stop-color="#062d2a"/></linearGradient><linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff"/><stop offset=".55" stop-color="#c7d9f5"/><stop offset="1" stop-color="#7294c5"/></linearGradient><linearGradient id="blue" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#52f1ff"/><stop offset="1" stop-color="#0874ff"/></linearGradient><linearGradient id="green" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c2ff57"/><stop offset="1" stop-color="#00c96b"/></linearGradient></defs><rect width="512" height="512" rx="112" fill="url(#bg)"/><path d="M104 170A181 181 0 0 1 396 108" fill="none" stroke="url(#blue)" stroke-width="28" stroke-linecap="round"/><path d="M375 73l48 34-53 23" fill="none" stroke="#20caff" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/><path d="M408 342A181 181 0 0 1 116 405" fill="none" stroke="url(#green)" stroke-width="28" stroke-linecap="round"/><path d="M137 441l-51-34 53-24" fill="none" stroke="#4bea82" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/><rect x="105" y="140" width="302" height="278" rx="38" fill="url(#metal)"/><rect x="124" y="184" width="264" height="215" rx="24" fill="#07162d"/><rect x="157" y="116" width="28" height="75" rx="14" fill="url(#metal)"/><rect x="327" y="116" width="28" height="75" rx="14" fill="url(#metal)"/><g fill="url(#blue)"><rect x="147" y="211" width="52" height="47" rx="10"/><rect x="215" y="211" width="52" height="47" rx="10"/><rect x="147" y="273" width="52" height="47" rx="10"/></g><g fill="url(#green)"><rect x="313" y="211" width="52" height="47" rx="10"/><rect x="313" y="273" width="52" height="47" rx="10"/></g><g fill="#28466e"><rect x="215" y="273" width="52" height="47" rx="10"/><rect x="147" y="335" width="52" height="44" rx="10"/><rect x="215" y="335" width="52" height="44" rx="10"/><rect x="313" y="335" width="52" height="44" rx="10"/></g><circle cx="256" cy="296" r="57" fill="#061329" stroke="#9eb9e7" stroke-width="8"/><path d="M256 262v36l28 15" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><circle cx="256" cy="296" r="7" fill="#fff"/></svg>'''
www=root/"www"
(www/"app-icon.svg").write_text(icon_svg,encoding="utf-8")
android=root/"android"/"app"/"src"/"main"/"res"
sizes={"mipmap-mdpi":48,"mipmap-hdpi":72,"mipmap-xhdpi":96,"mipmap-xxhdpi":144,"mipmap-xxxhdpi":192}
for folder,size in sizes.items():
 d=android/folder;d.mkdir(parents=True,exist_ok=True)
 cairosvg.svg2png(bytestring=icon_svg.encode(),write_to=str(d/"ic_launcher.png"),output_width=size,output_height=size)
 cairosvg.svg2png(bytestring=icon_svg.encode(),write_to=str(d/"ic_launcher_round.png"),output_width=size,output_height=size)
foreground=icon_svg.replace('<rect width="512" height="512" rx="112" fill="url(#bg)"/>','')
drawable=android/"drawable-nodpi";drawable.mkdir(parents=True,exist_ok=True)
cairosvg.svg2png(bytestring=foreground.encode(),write_to=str(drawable/"smeny_launcher_foreground.png"),output_width=432,output_height=432)
bg=android/"drawable"/"smeny_launcher_background.xml";bg.parent.mkdir(parents=True,exist_ok=True)
bg.write_text('<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle"><corners android:radius="96dp"/><gradient android:angle="135" android:startColor="#071B43" android:centerColor="#071329" android:endColor="#062D2A"/></shape>',encoding="utf-8")
adaptive=android/"mipmap-anydpi-v26";adaptive.mkdir(parents=True,exist_ok=True)
xml='<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android"><background android:drawable="@drawable/smeny_launcher_background"/><foreground android:drawable="@drawable/smeny_launcher_foreground"/></adaptive-icon>'
(adaptive/"ic_launcher.xml").write_text(xml,encoding="utf-8")
(adaptive/"ic_launcher_round.xml").write_text(xml,encoding="utf-8")
print("Phase 6: flexible role coverage, weekday availability, refreshed UI and new launcher icon applied.")
