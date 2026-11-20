from pathlib import Path
import re
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")

def replace_function(name,next_name,body):
 global s
 pattern=rf"function {name}\([^)]*\)\{{.*?(?=function {next_name}\()"
 m=re.search(pattern,s,re.S)
 if not m: raise SystemExit(f"Could not find function boundary: {name} -> {next_name}")
 s=s[:m.start()]+body+"\n"+s[m.end():]

replace_function("openPosition","deletePosition",r"""
function openPosition(id){
 let p=db.positions.find(x=>x.id===id)||{id:'',name:'',color:'#3267e9',lead:false,shiftType:'D'};
 let type=p.shiftType||'D',start=p.start||(type==='N'?db.rules.nightStart:db.rules.dayStart)||'06:00',end=p.end||(type==='N'?db.rules.nightEnd:db.rules.dayEnd)||'14:00';
 showModal(id?'Upravit pozici':'Nová pracovní pozice',`<form id="posForm" class="formgrid">
 <div class="field full"><label>Název pozice *</label><input name="name" required maxlength="80" value="${esc(p.name||'')}" placeholder="Např. Řezník"></div>
 <div class="field"><label>Barva</label><input name="color" type="color" value="${p.color||'#3267e9'}"></div>
 <div class="field"><label class="checkrow"><input type="checkbox" name="lead" ${p.lead?'checked':''}> Pozice vedoucího směny</label></div>
 <div class="field full"><label>Typ směny</label><select name="shiftType"><option value="D" ${type==='D'?'selected':''}>Denní</option><option value="N" ${type==='N'?'selected':''}>Noční</option></select></div>
 <div class="field"><label>Začátek práce</label><input name="start" type="time" required value="${start}"></div>
 <div class="field"><label>Konec práce</label><input name="end" type="time" required value="${end}"></div>
 <div class="field full muted small">Pokud konec vychází na dřívější čas než začátek, směna pokračuje do následujícího dne.</div>
 </form>`,()=>{
   let f=$('#posForm');if(!f||!f.checkValidity()){f?.reportValidity();return}
   let val=n=>f.querySelector('[name="'+n+'"]')?.value??'';
   let x={...p,id:p.id||uid(),name:val('name').trim(),color:val('color')||'#3267e9',lead:!!f.querySelector('[name="lead"]').checked,shiftType:val('shiftType'),start:val('start'),end:val('end')};
   if(!x.name){toast('Zadej název pozice.');return}
   if(x.start===x.end){toast('Začátek a konec práce nesmí být stejné.');return}
   let i=db.positions.findIndex(a=>a.id===x.id),old=i>=0?db.positions[i]:null;
   if(i>=0)db.positions[i]=x;else db.positions.push(x);
   if(!save()){if(i>=0)db.positions[i]=old;else db.positions.pop();return}
   closeModal();render('positions');toast('Pozice a pracovní doba byly uloženy.');
 },id?`<button class="danger" type="button" onclick="deletePosition('${id}')">Smazat</button>`:'',true);
}
""")

replace_function("openPositionFromEmployee","deleteEmployee",r"""
function openPositionFromEmployee(){
 let f=$('#empForm');if(!f)return;
 let val=n=>f.querySelector('[name="'+n+'"]')?.value??'';
 let checked=n=>!!f.querySelector('[name="'+n+'"]')?.checked;
 let existing=db.employees.find(x=>x.name===val('name')),employeeId=existing?.id||'';
 let draft={id:employeeId,name:val('name'),email:val('email'),phone:val('phone'),weeklyHours:+val('weeklyHours')||40,maxConsecutive:+val('maxConsecutive')||db.rules.maxConsecutive,maxHours:+val('maxHours')||0,positions:[...f.querySelectorAll('[name="positions"]:checked')].map(i=>i.value),onlyDay:checked('onlyDay'),onlyNight:checked('onlyNight'),weekdays:checked('weekdays'),isLead:checked('isLead'),active:checked('active'),notes:val('notes')};
 showModal('Přidat pracovní pozici',`<form id="inlinePosForm" class="formgrid">
 <div class="field full"><label>Název pozice *</label><input name="name" required placeholder="Např. Vedoucí směny"></div>
 <div class="field"><label>Barva</label><input name="color" type="color" value="#3267e9"></div>
 <div class="field"><label class="checkrow"><input type="checkbox" name="lead"> Pozice vedoucího směny</label></div>
 <div class="field full"><label>Typ směny</label><select name="shiftType"><option value="D" selected>Denní</option><option value="N">Noční</option></select></div>
 <div class="field"><label>Začátek práce</label><input name="start" type="time" required value="${db.rules.dayStart||'06:00'}"></div>
 <div class="field"><label>Konec práce</label><input name="end" type="time" required value="${db.rules.dayEnd||'14:00'}"></div>
 <div class="field full muted small">Noční směna může končit následující den.</div>
 </form>`,()=>{
   let pf=$('#inlinePosForm');if(!pf||!pf.checkValidity()){pf?.reportValidity();return}
   let get=n=>pf.querySelector('[name="'+n+'"]')?.value??'';
   let name=get('name').trim();if(!name){toast('Zadej název pozice.');return}
   if(get('start')===get('end')){toast('Začátek a konec práce nesmí být stejné.');return}
   let pos={id:uid(),name,color:get('color')||'#3267e9',lead:!!pf.querySelector('[name="lead"]').checked,shiftType:get('shiftType'),start:get('start'),end:get('end')};
   db.positions.push(pos);if(!save()){db.positions.pop();return}
   draft.positions.push(pos.id);openEmployee(employeeId||undefined,draft);toast('Pozice přidána a vybrána. Dokonči a ulož zaměstnance.');
 },'',true);
}
""")

old="""let type=document.getElementById('coverageType').value,positionId=document.getElementById('coveragePosition').value,count=Number(document.getElementById('coverageCount').value),days="""
new="""let positionId=document.getElementById('coveragePosition').value,type=(db.positions.find(p=>p.id===positionId)?.shiftType||'D'),count=Number(document.getElementById('coverageCount').value),days="""
if old in s:s=s.replace(old,new,1)
else:raise SystemExit("Coverage rule creation anchor not found.")

s=s.replace("x.type===type&&(x.days||[]).includes(key)","(db.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(key)")
s=s.replace("x.type===type&&(x.days||[]).includes(dowKey)","(db.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(dowKey)")

old="const target={type,start:startTime,end:endTime};"
new="const targetFor=slot=>{const pos=slot.positionId?db.positions.find(p=>p.id===slot.positionId):null;return {type:pos?.shiftType||type,start:pos?.start||startTime,end:pos?.end||endTime}};"
if old in s:s=s.replace(old,new,1)
elif "const targetFor=slot=>" not in s:raise SystemExit("Planner target anchor not found.")
s=s.replace("eligible(e,slot,date,target,[])","eligible(e,slot,date,targetFor(slot),[])")
s=s.replace("eligible(e,item.slot,date,target,chosen)","eligible(e,item.slot,date,targetFor(item.slot),chosen)")
old="const assignment={id:uid(),date,type,employeeId:e.id,positionId:item.slot.positionId||"
new="const slotTarget=targetFor(item.slot),assignment={id:uid(),date,type:slotTarget.type,employeeId:e.id,positionId:item.slot.positionId||"
if old in s:s=s.replace(old,new,1)
elif "const slotTarget=targetFor(item.slot),assignment=" not in s:raise SystemExit("Planner assignment anchor not found.")
old="start:startTime,end:endTime,locked:false};"
new="start:slotTarget.start,end:slotTarget.end,locked:false};"
if old in s:s=s.replace(old,new,1)
elif "start:slotTarget.start,end:slotTarget.end" not in s:raise SystemExit("Planner assignment time anchor not found.")

# The position defines its shift type, so do not offer a conflicting type selector here.
s=s.replace('<div class="coverage-form"><div class="field"><label>Typ směny</label><select id="coverageType"><option value="D">Denní</option><option value="N">Noční</option></select></div><div class="field"><label>Požadovaná role</label>','<div class="coverage-form"><div class="field"><label>Požadovaná role</label>')
s=s.replace("(r.type==='D'?'Denní':'Noční')","((db.positions.find(p=>p.id===r.positionId)?.shiftType||r.type)==='D'?'Denní':'Noční')")
p.write_text(s,encoding="utf-8")
print("Phase 8: per-position shift type and working hours applied to both position creation flows and the planner.")
