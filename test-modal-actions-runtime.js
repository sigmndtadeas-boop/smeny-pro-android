const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('smeny_pro_mobile_build/www/index.html', 'utf8');

// Exercise the real modal function: every action must be placed in the header,
// the footer must stay empty, and the click callback must be connected.
const modalStart = html.indexOf('function showModal(');
const modalEnd = html.indexOf('function closeModal()', modalStart);
if (modalStart < 0 || modalEnd < 0) throw new Error('Cannot isolate showModal');
const els = {
  '#modalTitle': {textContent:''}, '#modalBody': {innerHTML:''},
  '#modalHeadActions': {innerHTML:''}, '#modalFoot': {innerHTML:''},
  '#modal': {classList:{add(v){this.value=v}}},
  '#modalSave': {onclick:null}
};
const modalContext = {$:s=>els[s]||null, esc:s=>String(s), console};
vm.createContext(modalContext);
vm.runInContext(html.slice(modalStart, modalEnd), modalContext);
let called = 0;
modalContext.showModal('Nová absence','<form></form>',()=>called++, '', false, 'Uložit absenci');
if (!els['#modalHeadActions'].innerHTML.includes('id="modalSave"')) throw new Error('Absence save button is not in modal header');
if (!els['#modalHeadActions'].innerHTML.includes('Uložit absenci')) throw new Error('Custom save label missing');
if (els['#modalFoot'].innerHTML !== '') throw new Error('Footer still contains actions');
if (typeof els['#modalSave'].onclick !== 'function') throw new Error('Save handler not wired');
els['#modalSave'].onclick();
if (called !== 1) throw new Error('Save callback did not execute exactly once');
modalContext.showModal('Potvrdit import','<p>preview</p>',()=>called++, '', false, 'Obnovit data ze zálohy');
if (!els['#modalHeadActions'].innerHTML.includes('Obnovit data ze zálohy')) throw new Error('Import confirmation label missing');
els['#modalSave'].onclick();
if (called !== 2) throw new Error('Import confirmation callback did not execute');
modalContext.showModal('Upravit zaměstnance','<form></form>',()=>called++, '<button>Extra</button>', true, 'Uložit');
if (!els['#modalHeadActions'].innerHTML.includes('Extra') || !els['#modalHeadActions'].innerHTML.includes('id="modalSave"')) throw new Error('Header-action mode regressed');
if (els['#modalFoot'].innerHTML !== '') throw new Error('Header-action mode populated footer');
console.log('PASS absence save action is visible in header and wired');
console.log('PASS import confirmation action is visible in header and wired');
console.log('PASS employee/position header-action mode remains compatible');

// Test that export waits for the explicit modal confirmation click.
const confirmStart = html.indexOf('function confirmExport(');
const confirmEnd = html.indexOf('\nfunction exportCSV()', confirmStart);
if (confirmStart < 0 || confirmEnd < 0) throw new Error('Cannot isolate confirmExport');
let captured = null, exportCalls = 0;
const exportContext = {
  showModal:(title,body,onSave,extra,header,label)=>{captured={title,body,onSave,label}},
  esc:s=>String(s), closeModal:()=>{}, toast:()=>{}
};
vm.createContext(exportContext);
vm.runInContext(html.slice(confirmStart, confirmEnd), exportContext);
exportContext.confirmExport('CSV',()=>{exportCalls++},'Exportovat CSV');
if (exportCalls !== 0 || !captured || captured.label !== 'Exportovat CSV') throw new Error('Export ran without confirmation or wrong label');
captured.onSave();
if (exportCalls !== 1) throw new Error('Export action did not run after confirmation');
console.log('PASS export is gated behind explicit confirmation');

// Simulate choosing a JSON backup. The live database must not change until
// the user presses the confirmation button; failed saves must roll back.
const importStart = html.indexOf('function importJSON(){');
const importEnd = html.indexOf('function resetData()', importStart);
if (importStart < 0 || importEnd < 0) throw new Error('Cannot isolate importJSON');
function runImportCase(saveResult) {
  const oldDb = {employees:[{id:'old'}],positions:[],assignments:[],absences:[],rules:{}};
  const backup = {employees:[{id:'new1'},{id:'new2'}],positions:[{id:'p'}],assignments:[{id:'a'}],absences:[],rules:{}};
  let pending = null, saved = 0, rendered = 0;
  const input = {files:[{name:'backup.json'}],click(){this.onchange()}};
  class FakeFileReader { readAsText(){this.result=JSON.stringify(backup);this.onload()} }
  const ctx = {
    document:{createElement:()=>input}, FileReader:FakeFileReader,
    structuredClone, JSON, console, esc:s=>String(s),
    db:oldDb, defaults:{employees:[],positions:[],assignments:[],absences:[],rules:{}},
    showModal:(title,body,onSave,extra,header,label)=>{pending={title,body,onSave,label}},
    normalizeSmenyDatabase:()=>{}, save:()=>{saved++;return saveResult},
    closeModal:()=>{}, render:()=>{rendered++}, toast:()=>{}
  };
  vm.createContext(ctx);
  vm.runInContext(html.slice(importStart, importEnd), ctx);
  ctx.importJSON();
  if (ctx.db !== oldDb || !pending) throw new Error('Import changed data before confirmation');
  if (pending.label !== 'Obnovit data ze zálohy') throw new Error('Wrong import confirmation label');
  pending.onSave();
  if (saveResult) {
    if (ctx.db.employees.length !== 2 || ctx.db.employees[0].id !== 'new1' || saved !== 1 || rendered !== 1) throw new Error('Confirmed import did not commit expected backup');
  } else {
    if (ctx.db !== oldDb || saved !== 1 || rendered !== 0) throw new Error('Failed import did not restore previous database');
  }
}
runImportCase(true);
runImportCase(false);
console.log('PASS import waits for confirmation and rolls back on failed save');
console.log('All modal action runtime tests passed.');
