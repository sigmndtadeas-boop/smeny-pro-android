from pathlib import Path
import re
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")
pattern=r"function openPosition\(id\)\{.*?(?=\nfunction deletePosition\(id\))"
m=re.search(pattern,s,re.S)
if not m: raise SystemExit("Position editor boundaries not found.")
editor = r"""
function openPosition(id){
 let p=db.positions.find(x=>x.id===id)||{id:'',name:'',color:'#3267e9',lead:false,shiftType:'D',start:db.rules.dayStart||'06:00',end:db.rules.dayEnd||'14:00'};
 let type=p.shiftType||'D',start=p.start||(type==='N'?db.rules.nightStart:db.rules.dayStart)||'06:00',end=p.end||(type==='N'?db.rules.nightEnd:db.rules.dayEnd)||'14:00';
 showModal(id?'Upravit pozici':'Nová pozice',\`<form id="posForm" class="formgrid">
 <div class="field full"><label>Název pozice *</label><input name="name" required maxlength="80" value="\${esc(p.name||'')}" placeholder="Např. Řezník"></div>
 <div class="field"><label>Barva</label><input name="color" type="color" value="\${p.color||'#3267e9'}"></div>
 <div class="field"><label class="checkrow"><input type="checkbox" name="lead" \${p.lead?'checked':''}> Pozice vedoucího směny</label></div>
 <div class="field full"><label>Typ směny</label><select name="shiftType"><option value="D" \${type==='D'?'selected':''}>Denní</option><option value="N" \${type==='N'?'selected':''}>Noční</option></select></div>
 <div class="field"><label>Začátek práce</label><input name="start" type="time" required value="\${start}"></div>
 <div class="field"><label>Konec práce</label><input name="end" type="time" required value="\${end}"></div>
 <div class="field full muted small">Konec dříve než začátek znamená pokračování směny do následujícího dne.</div>
 </form>\`,()=>{
   let f=$('#posForm');if(!f||!f.checkValidity()){f?.reportValidity();return}
   let val=n=>f.querySelector('[name="'+n+'"]')?.value??'';
   let x={...p,id:p.id||uid(),name:val('name').trim(),color:val('color')||'#3267e9',lead:!!f.querySelector('[name="lead"]').checked,shiftType:val('shiftType'),start:val('start'),end:val('end')};
   if(!x.name){toast('Zadej název pozice.');return}
   if(x.start===x.end){toast('Začátek a konec směny nesmí být stejné.');return}
   let i=db.positions.findIndex(a=>a.id===x.id),old=i>=0?db.positions[i]:null;
   if(i>=0)db.positions[i]=x;else db.positions.push(x);
   if(!save()){if(i>=0)db.positions[i]=old;else db.positions.pop();return}
   closeModal();render('positions');toast('Pozice a její pracovní doba byly uloženy.');
 },'',true);
}
"""
s=s[:m.start()]+editor+s[m.end():]
old="let type=document.getElementById('coverageType').value,positionId=document.getElementById('coveragePosition').value,count=Number(document.getElementById('coverageCount').value),days="
new="let positionId=document.getElementById('coveragePosition').value,type=(db.positions.find(p=>p.id===positionId)?.shiftType||document.getElementById('coverageType').value),count=Number(document.getElementById('coverageCount').value),days="
if old in s:s=s.replace(old,new,1)
elif new not in s:raise SystemExit("Coverage rule creation anchor not found.")
s=s.replace("x.type===type&&(x.days||[]).includes(key)","(db.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(key)")
s=s.replace("x.type===type&&(x.days||[]).includes(dowKey)","(db.positions.find(p=>p.id===x.positionId)?.shiftType||x.type)===type&&(x.days||[]).includes(dowKey)")
old="const target={type,start:startTime,end:endTime};"
new="const target={type,start:startTime,end:endTime},targetFor=slot=>{const pos=slot.positionId?db.positions.find(p=>p.id===slot.positionId):null;return {type,start:pos?.start||startTime,end:pos?.end||endTime}};"
if old in s:s=s.replace(old,new,1)
elif "targetFor=slot=>" not in s:raise SystemExit("Planner target time anchor not found.")
s=s.replace("eligible(e,slot,date,target,[])","eligible(e,slot,date,targetFor(slot),[])")
s=s.replace("eligible(e,item.slot,date,target,chosen)","eligible(e,item.slot,date,targetFor(item.slot),chosen)")
old="const assignment={id:uid(),date,type,employeeId:e.id,positionId:item.slot.positionId||"
new="const slotTarget=targetFor(item.slot),assignment={id:uid(),date,type:slotTarget.type,employeeId:e.id,positionId:item.slot.positionId||"
if old in s:s=s.replace(old,new,1)
elif "const slotTarget=targetFor(item.slot),assignment=" not in s:raise SystemExit("Planner assignment creation anchor not found.")
old="start:startTime,end:endTime,locked:false};"
new="start:slotTarget.start,end:slotTarget.end,locked:false};"
if old in s:s=s.replace(old,new,1)
elif "start:slotTarget.start,end:slotTarget.end" not in s:raise SystemExit("Planner assignment time anchor not found.")
p.write_text(s,encoding="utf-8")
print("Phase 8: per-position shift types and working hours added to the editor and role-based planner.")
