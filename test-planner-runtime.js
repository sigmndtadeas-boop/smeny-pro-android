const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('smeny_pro_mobile_build/www/index.html', 'utf8');
const start = html.indexOf('function plannerMinutes(t)');
const end = html.indexOf('\n\nasync function exportXLSX()', start);
if (start < 0 || end < 0) throw new Error('Cannot isolate planner functions');
const plannerCode = html.slice(start, end);

function runCase(label, employeeCount, partialAllowed, expectedAssignments, expectedSave) {
  let nextId = 0, saveCount = 0, modalTitle = '';
  const employees = Array.from({length: employeeCount}, (_, i) => ({
    id: 'e' + i, name: 'Employee ' + i, active: true,
    positions: ['legacy-general'], weeklyHours: 40, maxConsecutive: 5
  }));
  const db = {
    year: 2026, month: 0, employees,
    // Legacy positions intentionally have no shiftType.
    positions: [{id:'legacy-general',name:'General role',lead:false}],
    absences: [], assignments: [],
    rules: {
      dayCount:0, nightCount:0, weekdayEx:0, weekendEx:0,
      dayStart:'06:00', dayEnd:'18:00', nightStart:'18:00', nightEnd:'06:00',
      maxConsecutive:5, minRest:11, maxHours:200, includeLead:false,
      avoidNightToDay:true, excludePairs:[], coverageRules:[],
      staffingByDay:{1:{D:1,N:1}}, plannerStrategy:'balanced',
      plannerAllowPartial:partialAllowed
    }
  };
  const context = {
    db, window:{},
    document:{getElementById:()=>null,querySelectorAll:()=>[]},
    $:()=>null, $$:()=>[], saveRules:()=>{}, saveAdvancedPlanner:()=>{},
    confirm:()=>true, toast:()=>{}, render:()=>{},
    save:()=>{saveCount++;return true},
    showModal:(title)=>{modalTitle=title}, closeModal:()=>{},
    dateRange:()=>[new Date(2026,0,5)], iso:()=> '2026-01-05',
    fmt:()=> '5. 1. 2026',
    duration:(a,b)=>{
      const [ah,am]=a.split(':').map(Number),[bh,bm]=b.split(':').map(Number);
      let n=bh*60+bm-ah*60-am;if(n<=0)n+=1440;return n/60;
    },
    uid:()=> 'new'+(++nextId), esc:s=>String(s), monthNames:['leden'],
    structuredClone, console, Date, Map, Number, String, Object, Array, Math
  };
  vm.createContext(context);
  vm.runInContext(plannerCode + '\ngenerateSchedule();', context);

  const actual = context.db.assignments.length;
  if (actual !== expectedAssignments || (saveCount > 0) !== expectedSave) {
    throw new Error(label + ': assignments=' + actual + ', saves=' + saveCount + ', modal=' + modalTitle);
  }
  if (!modalTitle) throw new Error(label + ': no result dialog was shown');
  if (label.startsWith('legacy')) {
    const types = context.db.assignments.map(a=>a.type).sort().join(',');
    if (types !== 'D,N') throw new Error('Legacy position did not cover both shift types: ' + types);
  }
  console.log('PASS ' + label + ' — ' + actual + ' assignments; save=' + (saveCount>0));
}

runCase('legacy generic position supports day and night', 2, true, 2, true);
runCase('partial staffing is saved as an editable draft', 1, true, 1, true);
runCase('strict mode leaves the original schedule untouched', 1, false, 0, false);
console.log('All planner behavior tests passed.');
