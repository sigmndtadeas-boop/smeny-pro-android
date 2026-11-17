from pathlib import Path
p=Path('smeny_pro_mobile_build/www/index.html')
s=p.read_text(encoding='utf-8')

def replace(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'Patch target not found: {label}')
    s=s.replace(old,new,1)

replace("settings:{org:'Moje organizace'}", "settings:{org:'Moje organizace',theme:'system'}", 'settings defaults')
replace("function save(){localStorage.setItem('smenypro_db',JSON.stringify(db))}", "function save(){try{localStorage.setItem('smenypro_db',JSON.stringify(db));return true}catch(e){console.error('Uložení dat selhalo',e);toast('Data se nepodařilo uložit. Zkontroluj volné místo a oprávnění aplikace.');return false}}", 'safe save')
replace("function toast(t){", "function applyTheme(){let t=db.settings?.theme||'system';let dark=t==='dark'||(t==='system'&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.body.dataset.theme=dark?'dark':'light'}function setTheme(t){db.settings.theme=t;applyTheme();save();toast('Vzhled byl uložen.')}if(window.matchMedia){window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change',()=>{if((db.settings?.theme||'system')==='system')applyTheme()})}applyTheme();function toast(t){", 'theme functions')
replace('<button data-page="reports"><span class="ico">▥</span>Statistiky a export</button></nav>', '<button data-page="reports"><span class="ico">▥</span>Statistiky a export</button><button data-page="settings"><span class="ico">⚙</span>Nastavení vzhledu</button></nav>', 'desktop settings nav')
if "settings:'Nastavení vzhledu'" not in s:
    s=s.replace("reports:'Statistiky a export'})[page];", "reports:'Statistiky a export',settings:'Nastavení vzhledu'})[page];",1)
replace("if(page==='reports')v.innerHTML=reportsPage();}", "if(page==='reports')v.innerHTML=reportsPage();if(page==='settings')v.innerHTML=settingsPage();}", 'settings render')
settings="function settingsPage(){let t=db.settings?.theme||'system';return pageHead('Nastavení vzhledu','Přizpůsob si aplikaci podle světelných podmínek', '')+`<div class=\"card\"><div class=\"cardhead\"><h2>Vzhled aplikace</h2></div><div class=\"field\"><label for=\"themeSelect\">Barevný režim</label><select id=\"themeSelect\" onchange=\"setTheme(this.value)\"><option value=\"light\" ${t==='light'?'selected':''}>Světlý</option><option value=\"dark\" ${t==='dark'?'selected':''}>Tmavý</option><option value=\"system\" ${t==='system'?'selected':''}>Automaticky podle telefonu</option></select></div><p class=\"muted small\" style=\"margin-top:12px\">Zvolený vzhled se uloží v tomto zařízení a zůstane zachován i po restartu aplikace.</p></div>`}"
replace('function reportsPage(){',settings+'function reportsPage(){','settings page')
replace("let f=$('#posForm');if(!f.reportValidity())return;let x={id:p.id||uid(),name:f.name.value.trim(),color:f.color.value,lead:f.lead.checked};", "let f=$('#posForm');if(!f.reportValidity())return;let el=n=>f.elements.namedItem(n);let x={id:p.id||uid(),name:el('name').value.trim(),color:el('color').value,lead:el('lead').checked};", 'position form fields')
replace("let f=$('#empForm');if(!f.reportValidity())return;let x=Object.fromEntries(new FormData(f));", "let f=$('#empForm');if(!f.reportValidity())return;let el=n=>f.elements.namedItem(n);let x=Object.fromEntries(new FormData(f));", 'employee form access')
replace("onlyDay:f.onlyDay.checked,onlyNight:f.onlyNight.checked,weekdays:f.weekdays.checked,isLead:f.isLead.checked,active:f.active.checked", "onlyDay:el('onlyDay').checked,onlyNight:el('onlyNight').checked,weekdays:el('weekdays').checked,isLead:el('isLead').checked,active:el('active').checked", 'employee checkbox access')
if 'id="mobileMore"' in s and "nav('settings');closeMobileMore()" not in s:
    s=s.replace('<button onclick="nav(\'reports\');closeMobileMore()"><span>▥</span>Statistiky</button>', '<button onclick="nav(\'reports\');closeMobileMore()"><span>▥</span>Statistiky</button><button onclick="nav(\'settings\');closeMobileMore()"><span>⚙</span>Nastavení</button>', 1)
dark_css=""" 
body[data-theme="dark"]{--bg:#101521;--panel:#192232;--ink:#edf2fb;--muted:#a3aec1;--line:#303c50;--nav:#0b111d;--blue:#6e94ff;--blue2:#24385f;--shadow:0 8px 28px #0003;background:var(--bg);color:var(--ink)}
body[data-theme="dark"] .topbar,body[data-theme="dark"] .mobile-nav,body[data-theme="dark"] .mobile-more,body[data-theme="dark"] .modal,body[data-theme="dark"] .modalfoot{background:#192232;color:var(--ink);border-color:var(--line)}
body[data-theme="dark"] .field input,body[data-theme="dark"] .field select,body[data-theme="dark"] .field textarea,body[data-theme="dark"] .toolbar input,body[data-theme="dark"] .toolbar select{background:#111a29;color:var(--ink);border-color:var(--line)}
body[data-theme="dark"] th{background:#202c3e;color:#b8c4d8}body[data-theme="dark"] .day{background:#192232;border-color:var(--line)}body[data-theme="dark"] .shiftbox.dayshift{background:#24385f;color:#cbd9ff}body[data-theme="dark"] .shiftbox.nightshift{background:#382d59;color:#e0d5ff}body[data-theme="dark"] .rulebox{background:#202c3e;border-color:var(--line);color:#c4cede}body[data-theme="dark"] .notice{background:#40351f;color:#f5d99c}body[data-theme="dark"] .pill{background:#2b374a;color:#d2dced}body[data-theme="dark"] .pill.ok{background:#173d32;color:#9de2c5}body[data-theme="dark"] .pill.warn{background:#49391c;color:#f2d18b}body[data-theme="dark"] .pill.bad{background:#4a252d;color:#ffb8c1}body[data-theme="dark"] .mobile-nav{border-top:1px solid var(--line)}body[data-theme="dark"] .mobile-nav button.active{background:#263b64;color:#dbe5ff}body[data-theme="dark"] .modalhead,body[data-theme="dark"] .modalfoot{border-color:var(--line)}body[data-theme="dark"] button{background:#29364a;color:var(--ink)}body[data-theme="dark"] button.primary{background:#416fe5;color:#fff}body[data-theme="dark"] button.ghost{border-color:var(--line)}
"""
replace('</style>',dark_css+'</style>','dark theme css')
p.write_text(s,encoding='utf-8')
print('Applied settings, theme, form and persistence fixes.')
