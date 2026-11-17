from pathlib import Path

p = Path('smeny_pro_mobile_build/www/index.html')
s = p.read_text(encoding='utf-8')

# Load the bundled Excel writer locally so export works without an internet connection.
if '<script src="xlsx.bundle.js"></script>' not in s:
    marker = '<script>'
    if marker not in s:
        raise SystemExit('Main script tag not found')
    s = s.replace(marker, '<script src="xlsx.bundle.js"></script>\\n' + marker, 1)

# Add Excel actions beside the existing CSV actions.
if 'onclick="exportXLSX()"' not in s:
    s = s.replace('onclick="exportCSV()">⇩ CSV', 'onclick="exportCSV()">⇩ CSV</button><button class="primary" onclick="exportXLSX()">▦ Excel (.xlsx)', 1)
    s = s.replace('onclick="exportCSV()">⇩ Export CSV', 'onclick="exportCSV()">⇩ Export CSV</button><button class="primary" onclick="exportXLSX()">▦ Excel (.xlsx)', 1)

if 'function exportXLSX()' not in s:
    anchor = 'function exportCSV(){'
    if anchor not in s:
        raise SystemExit('CSV export function not found')
    fn = r"""
function exportXLSX(){
  if(!window.XLSX){toast('Excel exportní knihovna není načtena.');return}
  const prefix=yearMonth();
  const shifts=db.assignments.filter(x=>x.date.startsWith(prefix)).sort((a,b)=>a.date.localeCompare(b.date)||a.type.localeCompare(b.type)||empName(a.employeeId).localeCompare(empName(b.employeeId),'cs'));
  const wb=XLSX.utils.book_new();
  const border={style:'thin',color:{rgb:'D9E2F0'}};
  const titleStyle={font:{name:'Aptos',sz:16,bold:true,color:{rgb:'FFFFFF'}},fill:{patternType:'solid',fgColor:{rgb:'172B4D'}},alignment:{vertical:'center'}};
  const subStyle={font:{name:'Aptos',sz:10,italic:true,color:{rgb:'526078'}},alignment:{vertical:'center'}};
  const headStyle={font:{name:'Aptos',sz:10,bold:true,color:{rgb:'FFFFFF'}},fill:{patternType:'solid',fgColor:{rgb:'315B9A'}},alignment:{horizontal:'center',vertical:'center',wrapText:true},border:{bottom:{style:'medium',color:{rgb:'244675'}}}};
  const baseStyle={font:{name:'Aptos',sz:10,color:{rgb:'243247'}},alignment:{vertical:'center'},border:{bottom:border}};
  const dayStyle={...baseStyle,fill:{patternType:'solid',fgColor:{rgb:'EAF2FF'}}};
  const nightStyle={...baseStyle,fill:{patternType:'solid',fgColor:{rgb:'F0ECFF'}}};
  const rows=[
    ['SMĚNY PRO · MĚSÍČNÍ ROZPIS'],
    [monthNames[db.month]+' '+db.year+' · Vygenerováno '+new Date().toLocaleDateString('cs-CZ')],
    [],
    ['Datum','Den v týdnu','Směna','Od','Do','Zaměstnanec','Pozice','EX','Uzamčeno','Hodin']
  ];
  shifts.forEach(a=>{
    const pos=posName(a.positionId), isEx=/\\bEX\\b/i.test(pos);
    rows.push([a.date,new Date(a.date+'T12:00:00').toLocaleDateString('cs-CZ',{weekday:'long'}),a.type==='D'?'Denní':'Noční',a.start,a.end,empName(a.employeeId),pos,isEx?'ANO':'',a.locked?'Ano':'Ne',duration(a.start,a.end)]);
  });
  if(!shifts.length) rows.push(['','','','','','V tomto měsíci nejsou naplánované směny.']);
  const ws=XLSX.utils.aoa_to_sheet(rows);
  ws['!merges']=[{s:{r:0,c:0},e:{r:0,c:9}},{s:{r:1,c:0},e:{r:1,c:9}}];
  ws['!cols']=[{wch:13},{wch:17},{wch:12},{wch:9},{wch:9},{wch:25},{wch:20},{wch:9},{wch:12},{wch:10}];
  ws['!rows']=[{hpt:30},{hpt:21},{hpt:8},{hpt:28}];
  ws['!freeze']={xSplit:0,ySplit:4,topLeftCell:'A5',activePane:'bottomLeft',state:'frozen'};
  if(shifts.length) ws['!autofilter']={ref:'A4:J'+(4+shifts.length)};
  for(let c=0;c<10;c++){const cell=ws[XLSX.utils.encode_cell({r:0,c})];if(cell)cell.s=titleStyle;const sub=ws[XLSX.utils.encode_cell({r:1,c})];if(sub)sub.s=subStyle;const h=ws[XLSX.utils.encode_cell({r:3,c})];if(h)h.s=headStyle;}
  shifts.forEach((a,i)=>{const r=4+i,style=a.type==='D'?dayStyle:nightStyle;for(let c=0;c<10;c++){const cell=ws[XLSX.utils.encode_cell({r,c})];if(cell)cell.s=style;}const type=ws[XLSX.utils.encode_cell({r, c:2})];if(type)type.s={...style,font:{name:'Aptos',sz:10,bold:true,color:{rgb:a.type==='D'?'2457A6':'6547A8'}}};const hours=ws[XLSX.utils.encode_cell({r,c:9})];if(hours)hours.s={...style,numFmt:'0.0'};});
  XLSX.utils.book_append_sheet(wb,ws,'Měsíční rozpis');

  const employees=activeEmployees();
  const summary=[['SOUHRN ZAMĚSTNANCŮ'],[monthNames[db.month]+' '+db.year],[],['Zaměstnanec','Počet směn','Denní','Noční','Odpracováno hodin','Týdenní úvazek','Pozice']];
  employees.forEach(e=>{const own=shifts.filter(a=>a.employeeId===e.id);summary.push([e.name,own.length,own.filter(a=>a.type==='D').length,own.filter(a=>a.type==='N').length,own.reduce((n,a)=>n+duration(a.start,a.end),0),e.weeklyHours||40,(e.positions||[]).map(posName).join(', ')]);});
  const sws=XLSX.utils.aoa_to_sheet(summary);
  sws['!merges']=[{s:{r:0,c:0},e:{r:0,c:6}},{s:{r:1,c:0},e:{r:1,c:6}}];
  sws['!cols']=[{wch:26},{wch:13},{wch:12},{wch:12},{wch:20},{wch:18},{wch:32}];
  sws['!rows']=[{hpt:30},{hpt:21},{hpt:8},{hpt:28}];
  sws['!freeze']={xSplit:0,ySplit:4,topLeftCell:'A5',activePane:'bottomLeft',state:'frozen'};
  if(employees.length)sws['!autofilter']={ref:'A4:G'+(4+employees.length)};
  for(let c=0;c<7;c++){const t=sws[XLSX.utils.encode_cell({r:0,c})];if(t)t.s=titleStyle;const sub=sws[XLSX.utils.encode_cell({r:1,c})];if(sub)sub.s=subStyle;const h=sws[XLSX.utils.encode_cell({r:3,c})];if(h)h.s=headStyle;}
  employees.forEach((e,i)=>{for(let c=0;c<7;c++){const cell=sws[XLSX.utils.encode_cell({r:4+i,c})];if(cell)cell.s=baseStyle;}});
  XLSX.utils.book_append_sheet(wb,sws,'Souhrn zaměstnanců');
  XLSX.writeFile(wb,'smeny-'+prefix+'.xlsx',{compression:true});
  toast('Excelová tabulka je připravena ke stažení.');
}
"""
    s = s.replace(anchor, fn + '\\n' + anchor, 1)

p.write_text(s, encoding='utf-8')
print('Phase 4 Excel export patch ready.')
