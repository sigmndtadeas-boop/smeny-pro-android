from pathlib import Path
p=Path("smeny_pro_mobile_build/www/index.html")
s=p.read_text(encoding="utf-8")

def rep(old,new,label):
    global s
    n=s.count(old)
    if n != 1:
        raise SystemExit(f"Expected exactly one target for {label}, found {n}")
    s=s.replace(old,new,1)

# Put modal actions into the title row only for employee/position forms.
rep('<div class="modalhead"><h2 id="modalTitle"></h2><button class="ghost" onclick="closeModal()">✕</button></div>',
    '<div class="modalhead"><h2 id="modalTitle"></h2><div id="modalHeadActions" style="display:flex;align-items:center;gap:8px;flex-shrink:0"><button class="ghost" type="button" onclick="closeModal()" aria-label="Zrušit">✕</button></div></div>',
    "modal header actions container")

old="function showModal(title,body,onSave,extra=''){ $('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;$('#modalFoot').innerHTML=extra+(onSave?'<button class=\"ghost\" onclick=\"closeModal()\">Zrušit</button><button class=\"primary\" id=\"modalSave\">Uložit</button>':'');$('#modal').classList.add('show');if(onSave)$('#modalSave').onclick=onSave}"
new="function showModal(title,body,onSave,extra='',headerActions=false){ $('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;if(headerActions){$('#modalHeadActions').innerHTML=extra+(onSave?'<button class=\"primary\" type=\"button\" id=\"modalSave\">Uložit</button>':'')+'<button class=\"ghost\" type=\"button\" onclick=\"closeModal()\" aria-label=\"Zrušit\">✕</button>';$('#modalFoot').innerHTML=''}else{$('#modalHeadActions').innerHTML='<button class=\"ghost\" type=\"button\" onclick=\"closeModal()\" aria-label=\"Zavřít\">✕</button>';$('#modalFoot').innerHTML=extra+(onSave?'<button class=\"ghost\" onclick=\"closeModal()\">Zrušit</button><button class=\"primary\" id=\"modalSave\">Uložit</button>':'')}$('#modal').classList.add('show');if(onSave)$('#modalSave').onclick=onSave}"
rep(old,new,"modal action placement")

# Employee form: include save beside X in the header.
old="id?'<button class=\"danger\" type=\"button\" onclick=\"deleteEmployee(\''+id+'\')\">Smazat</button>':'');}"
new="id?'<button class=\"danger\" type=\"button\" onclick=\"deleteEmployee(\''+id+'\')\">Smazat</button>':'',true);}"
rep(old,new,"employee modal header save")

# Position form: include save beside X in the header.
old="id?`<button class=\"danger\" onclick=\"deletePosition('${id}')\">Smazat</button>`:'')}"
new="id?`<button class=\"danger\" type=\"button\" onclick=\"deletePosition('${id}')\">Smazat</button>`:'',true)}"
rep(old,new,"position modal header save")

# Inline position form opened from employee form: same header action row.
old="toast('Pozice přidána a vybrána. Dokonči a ulož zaměstnance.');},'',true);}"
new="toast('Pozice přidána a vybrána. Dokonči a ulož zaměstnance.');},'',true);}"
rep(old,new,"inline position modal header save")

p.write_text(s,encoding="utf-8")
print("Employee and position forms now have a persistent header action row: Save + X.")
