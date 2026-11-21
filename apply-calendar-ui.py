from pathlib import Path

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

# Mark weekends in the existing day-cell renderer without changing schedule data.
old = 'let ds=iso(d),as=assignmentsFor(ds),isOther=d.getMonth()!==m;return `<div class="day ${isOther?\'other\':\'\'} ${ds===iso(today)?\'today\':\'\'}"'
new = 'let ds=iso(d),as=assignmentsFor(ds),isOther=d.getMonth()!==m,isWeekend=d.getDay()===0||d.getDay()===6;return `<div class="day ${isOther?\'other\':\'\'} ${isWeekend?\'weekend\':\'\'} ${ds===iso(today)?\'today\':\'\'}"'
if old in s:
    s = s.replace(old, new, 1)
elif 'isWeekend=d.getDay()===0||d.getDay()===6' not in s:
    raise SystemExit("Calendar day renderer anchor not found; refusing to patch.")

css = r"""
/* Směny PRO – compact mobile calendar refresh */
@media (max-width:700px) {
  .content:has(.calwrap) { padding-left:10px; padding-right:10px; }
  .calwrap { overflow:visible !important; width:100%; }
  .calendar {
    width:100%; min-width:0 !important;
    grid-template-columns:repeat(7,minmax(0,1fr)) !important;
    gap:3px !important;
  }
  .dow { min-width:0; padding:5px 0; text-align:center; font-size:10px; }
  .day {
    min-width:0; min-height:76px !important; height:auto;
    padding:5px 3px !important; border-radius:9px;
    overflow:hidden; display:flex; flex-direction:column; gap:2px;
  }
  .daynum { font-size:12px; line-height:1.2; margin:0 0 2px; }
  .day.weekend { background:rgba(110,130,165,.10); }
  .day.other { opacity:.30; }
  .day.today { border-width:2px; }
  .shiftbox {
    min-width:0; margin:1px 0 !important; padding:3px 2px !important;
    border-radius:5px; font-size:9px !important; line-height:1.15;
    text-align:center; overflow:hidden; white-space:nowrap;
  }
  .shiftbox .who { display:none !important; }
  .day > .small { font-size:8px !important; line-height:1.1; margin-top:auto; }
  .monthnav { gap:5px; }
  .monthnav strong { font-size:14px !important; }
  .card:has(.calwrap) { padding:9px !important; }
}
@media (max-width:380px) {
  .day { min-height:68px !important; padding:4px 2px !important; }
  .dow { font-size:9px; }
  .daynum { font-size:11px; }
  .shiftbox { font-size:8px !important; }
}
"""
if 'Směny PRO – compact mobile calendar refresh' not in s:
    if '</head>' not in s:
        raise SystemExit("HTML head closing tag not found.")
    s = s.replace('</head>', '<style id="calendar-mobile-refresh">\n' + css + '\n</style>\n</head>', 1)

p.write_text(s, encoding="utf-8")
print("Compact calendar styles applied.")
