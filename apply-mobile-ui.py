from pathlib import Path
p=Path('smeny_pro_mobile_build/www/index.html')
s=p.read_text(encoding='utf-8')
css=Path('mobile-ui.css').read_text(encoding='utf-8')
if 'Směny PRO – mobile-first layer' not in s:
    s=s.replace('</style>', css+'\\n</style>', 1)
if 'id="mobileNav"' not in s:
    marker='<div class="modalback" id="modal">'
    nav='''<nav class="mobile-nav" id="mobileNav" aria-label="Hlavní navigace">
<button data-page="dashboard" class="active"><span class="ico">▦</span><span>Přehled</span></button>
<button data-page="schedule"><span class="ico">▣</span><span>Rozpis</span></button>
<button data-page="employees"><span class="ico">♙</span><span>Lidé</span></button>
<button data-page="absences"><span class="ico">◷</span><span>Absence</span></button>
<button type="button" id="mobileMoreBtn"><span class="ico">•••</span><span>Více</span></button>
</nav>
<div class="mobile-more" id="mobileMore">
<button onclick="nav('positions');closeMobileMore()"><span>▤</span>Pozice</button>
<button onclick="nav('rules');closeMobileMore()"><span>⚙</span>Generátor</button>
<button onclick="nav('reports');closeMobileMore()"><span>▥</span>Statistiky</button>
</div>
'''
    s=s.replace(marker,nav+marker,1)
old="function nav(page){$$('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));render(page)}$$('#nav button').forEach(b=>b.onclick=()=>nav(b.dataset.page));"
new="function nav(page){$$('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));$$('#mobileNav [data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===page));render(page)}$$('#nav button').forEach(b=>b.onclick=()=>nav(b.dataset.page));$$('#mobileNav [data-page]').forEach(b=>b.onclick=()=>nav(b.dataset.page));function closeMobileMore(){$('#mobileMore')?.classList.remove('show')}$('#mobileMoreBtn')?.addEventListener('click',()=>$('#mobileMore').classList.toggle('show'));document.addEventListener('click',e=>{if(!e.target.closest('#mobileMore')&&!e.target.closest('#mobileMoreBtn'))closeMobileMore()});"
if old in s and 'function closeMobileMore()' not in s:
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
