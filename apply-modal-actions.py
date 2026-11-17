from pathlib import Path
import re

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

old = '<div class="modalhead"><h2 id="modalTitle"></h2><button class="ghost" onclick="closeModal()">✕</button></div>'
new = '<div class="modalhead"><h2 id="modalTitle"></h2><div id="modalHeadActions" style="display:flex;align-items:center;gap:8px;flex-shrink:0"><button class="ghost" type="button" onclick="closeModal()" aria-label="Zrušit">✕</button></div></div>'
if s.count(old) != 1:
    raise SystemExit(f"Modal header target count: {s.count(old)}")
s = s.replace(old, new, 1)

old = """function showModal(title,body,onSave,extra=''){ $('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;$('#modalFoot').innerHTML=extra+(onSave?'<button class="ghost" onclick="closeModal()">Zrušit</button><button class="primary" id="modalSave">Uložit</button>':'');$('#modal').classList.add('show');if(onSave)$('#modalSave').onclick=onSave}"""
new = """function showModal(title,body,onSave,extra='',headerActions=false){ $('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;if(headerActions){$('#modalHeadActions').innerHTML=extra+(onSave?'<button class="primary" type="button" id="modalSave">Uložit</button>':'')+'<button class="ghost" type="button" onclick="closeModal()" aria-label="Zrušit">✕</button>';$('#modalFoot').innerHTML=''}else{$('#modalHeadActions').innerHTML='<button class="ghost" type="button" onclick="closeModal()" aria-label="Zavřít">✕</button>';$('#modalFoot').innerHTML=extra+(onSave?'<button class="ghost" onclick="closeModal()">Zrušit</button><button class="primary" id="modalSave">Uložit</button>':'')}$('#modal').classList.add('show');if(onSave)$('#modalSave').onclick=onSave}"""
if old not in s:
    raise SystemExit("showModal target not found")
s = s.replace(old, new, 1)

s, n = re.subn(r"(toast\('Zaměstnanec uložen\.'\)\},id\?.*?:'')\);\}\nfunction openPositionFromEmployee", r"\1,true);}\nfunction openPositionFromEmployee", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"Employee save header target count: {n}")

s, n = re.subn(r"(toast\('Pozice uložena\.'\)\},id\?.*?:'')\)\}", r"\1,true)}", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"Position save header target count: {n}")

old_inline = "toast('Pozice přidána a vybrána. Dokonči a ulož zaměstnance.');});}"
new_inline = "toast('Pozice přidána a vybrána. Dokonči a ulož zaměstnance.');},'',true);}"
if s.count(old_inline) != 1:
    raise SystemExit(f"Inline position target count: {s.count(old_inline)}")
s = s.replace(old_inline, new_inline, 1)

p.write_text(s, encoding="utf-8")
print("Employee and position forms now show Save beside the X in the header.")
