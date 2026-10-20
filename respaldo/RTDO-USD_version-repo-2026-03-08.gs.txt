/**
 * ============================================================
 * GIASSISTANT - CÓDIGO MAESTRO CONSOLIDADO (2026)
 * ============================================================
 * Estructura: 61 columnas (ID -> EMAIL) + 2 de control (P y N).
 */

// --- CONFIGURACIÓN GLOBAL ---
const SERVICIOS_MASTER = [
  "Seleccion IT", 
  "Seleccion Generalista", 
  "Employee Experience",
  "Capacitacion In Company", 
  "Workshop o Curso Online", 
  "Otros Ing", 
  "Outsourcing",
  "PR-HIST"
];

const HOJA_RTDO_FINAL = "RTDO";
const CANT_COL_ORIGEN = 61; // Exactamente 61 columnas según tu lista actualizada (ID hasta EMAIL)

// --- 1. MENÚ SUPERIOR ---
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 GiAssistant')
      .addItem('🔄 Actualizar USD Blue (Columna AT)', 'updateServiceRates')
      .addSeparator()
      .addItem('📥 Reconstruir RTDO', 'initialSyncAll')
      .addItem('🛠️ Reparar Activadores', 'setupTrigger')
      .addToUi();
}

// --- 2. ACTUALIZACIÓN DE USD BLUE ---
function updateServiceRates() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const apiURL = "https://api.bluelytics.com.ar/v2/evolution.json";
  try {
    const res = JSON.parse(UrlFetchApp.fetch(apiURL).getContentText());
    const blueMap = {};
    res.forEach(r => { if (r.source === "Blue") blueMap[r.date] = r.value_sell; });
    let total = 0;
    SERVICIOS_MASTER.forEach(nombre => {
      const sheet = ss.getSheetByName(nombre);
      if (!sheet) return;
      const data = sheet.getDataRange().getValues();
      const colCOTIZ = 45; // Columna "COTIZ" (Index 45, Columna 46)
      
      for (let i = 1; i < data.length; i++) {
        // Si el ID está vacío o si ya tiene cotización, pasar
        if (data[i][0] === "" || (data[i][colCOTIZ] !== "" && data[i][colCOTIZ] !== null)) continue;
        
        let valor = null;
        let d = (data[i][8] instanceof Date) ? data[i][8] : data[i][7]; // 8: INICIO, 7: VENTA/PRESUP
        
        if (!(d instanceof Date) || isNaN(d) || d.getFullYear() < 2026) continue;
        
        let iso = Utilities.formatDate(d, "GMT", "yyyy-MM-dd");
        const resDate = resolveDateFallback(iso, blueMap);
        if (resDate) valor = blueMap[resDate];
        
        if (valor !== null) {
          sheet.getRange(i + 1, colCOTIZ + 1).setValue(valor).setNumberFormat("#,##0");
          total++;
        }
      }
    });
    SpreadsheetApp.getUi().alert("✅ Cotizaciones actualizadas: " + total);
  } catch(e) { SpreadsheetApp.getUi().alert("Error USD: " + e.message); }
}

function resolveDateFallback(iso, map) {
  let d = new Date(iso + "T12:00:00");
  let today = new Date();
  if (d > today) d = today;
  for (let i = 0; i <= 15; i++) {
    let c = new Date(d); c.setDate(d.getDate() - i);
    if (c.getDay() === 0 || c.getDay() === 6) continue;
    let k = Utilities.formatDate(c, "GMT", "yyyy-MM-dd");
    if (map[k]) return k;
  }
  return null;
}

// --- 3. SINCRONIZACIÓN AUTOMÁTICA (RTDO) ---

function onEditTrigger(e) {
  if (!e || !e.source) return;
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(15000)) return; 
  try {
    const ss = e.source;
    const sheet = ss.getActiveSheet();
    const name = sheet.getName().trim();
    const pIdx = SERVICIOS_MASTER.map(s => s.toLowerCase()).indexOf(name.toLowerCase());
    if (pIdx === -1) return;

    const range = e.range;
    if (range.getRow() === 1) return; // Ignorar cabecera

    const destSheet = ss.getSheetByName(HOJA_RTDO_FINAL) || ss.insertSheet(HOJA_RTDO_FINAL);
    const currentRow = range.getRow();
    const id = sheet.getRange(currentRow, 1).getValue().toString().trim();
    
    // Si se borró el ID, purgamos huérfanos
    if (!id) {
      purgeSheetOrphans(ss, pIdx, sheet);
      return;
    }

    // Obtener los datos de la fila con el nuevo ancho de 61 columnas
    const rowData = sheet.getRange(currentRow, 1, 1, CANT_COL_ORIGEN).getValues()[0];
    const idNum = parseInt(id.match(/\d+/)) || 0;
    const finalRow = [...rowData, pIdx, idNum];

    if (upsertRowInRTDO(destSheet, id, finalRow)) {
      sortNaturalRTDO(destSheet);
    }
  } finally { lock.releaseLock(); }
}

function onChangeTrigger(e) {
  if (!e || (e.changeType !== 'REMOVE_ROW' && e.changeType !== 'OTHER')) return;
  const ss = e.source;
  const sheet = ss.getActiveSheet();
  const name = sheet.getName().trim();
  const pIdx = SERVICIOS_MASTER.map(s => s.toLowerCase()).indexOf(name.toLowerCase());
  if (pIdx !== -1) purgeSheetOrphans(ss, pIdx, sheet);
}

function upsertRowInRTDO(destSheet, id, fullRow) {
  const data = destSheet.getDataRange().getValues();
  const idLower = id.toLowerCase();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] && data[i][0].toString().trim().toLowerCase() === idLower) {
      destSheet.getRange(i + 1, 1, 1, fullRow.length).setValues([fullRow]);
      return true;
    }
  }
  // Si no está, lo insertamos
  destSheet.appendRow(fullRow);
  return true;
}

function purgeSheetOrphans(ss, pIdx, sourceSheet) {
  const destSheet = ss.getSheetByName(HOJA_RTDO_FINAL);
  if (!destSheet) return;
  const data = destSheet.getDataRange().getValues();
  const sourceIds = new Set(sourceSheet.getDataRange().getValues().map(r => r[0] ? r[0].toString().trim().toLowerCase() : "").filter(id => id !== ""));
  
  for (let i = data.length - 1; i >= 1; i--) {
    // La columna de prioridad (P) es ahora la 62 (Index 61)
    if (data[i][CANT_COL_ORIGEN] === pIdx) { 
      const id = data[i][0] ? data[i][0].toString().trim().toLowerCase() : "";
      if (!id || !sourceIds.has(id)) destSheet.deleteRow(i + 1);
    }
  }
}

function sortNaturalRTDO(sheet) {
  const lr = sheet.getLastRow();
  const lc = sheet.getLastColumn();
  // El SORT debe basarse en P (Col 62) y N (Col 63)
  if (lr > 1 && lc >= CANT_COL_ORIGEN + 2) {
    sheet.getRange(2, 1, lr - 1, lc).sort([
      {column: CANT_COL_ORIGEN + 1, ascending: true}, // P
      {column: CANT_COL_ORIGEN + 2, ascending: true}  // N
    ]);
    sheet.hideColumns(CANT_COL_ORIGEN + 1, 2);
  }
}

// --- 4. CARGA MASIVA ---
function initialSyncAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dest = ss.getSheetByName(HOJA_RTDO_FINAL) || ss.insertSheet(HOJA_RTDO_FINAL);
  dest.clear();
  
  let report = "Carga Finalizada (Estructura de 61 Columnas):\n";
  let firstHeader = true;

  SERVICIOS_MASTER.forEach((name, pIdx) => {
    const s = ss.getSheetByName(name.trim());
    if (!s) {
      report += "❌ No existe: " + name + "\n";
      return;
    }

    const lastRow = s.getLastRow();
    if (lastRow < 2) return;

    // Leemos exactamente 61 columnas
    const data = s.getRange(1, 1, lastRow, CANT_COL_ORIGEN).getValues();

    if (firstHeader) {
      dest.appendRow([...data[0], "P", "N"]);
      firstHeader = false;
    }

    const isHistorical = name.trim().toUpperCase() === "PR-HIST";
    const cleanRows = data.slice(1).filter(r => {
      // Si es PR-HIST, permitimos filas que tengan al menos algún contenido aunque no tengan ID
      if (isHistorical) {
        return r.some(cell => cell !== "" && cell !== null);
      }
      // Para el resto, el ID sigue siendo obligatorio
      return r[0] !== "" && r[0] !== null;
    }).map(r => {
      const idNum = parseInt(r[0].toString().match(/\d+/)) || 0;
      return [...r, pIdx, idNum];
    });

    if (cleanRows.length > 0) {
      dest.getRange(dest.getLastRow() + 1, 1, cleanRows.length, cleanRows[0].length).setValues(cleanRows);
      report += "✅ " + name + ": " + cleanRows.length + " filas\n";
    }
  });

  SpreadsheetApp.flush();
  sortNaturalRTDO(dest);
  SpreadsheetApp.getUi().alert(report);
}

// --- 5. REPARAR ACTIVADORES ---
function setupTrigger() {
  const ts = ScriptApp.getProjectTriggers();
  ts.forEach(t => ScriptApp.deleteTrigger(t));
  const ss = SpreadsheetApp.getActive();
  ScriptApp.newTrigger('onEditTrigger').forSpreadsheet(ss).onEdit().create();
  ScriptApp.newTrigger('onChangeTrigger').forSpreadsheet(ss).onChange().create();
  SpreadsheetApp.getUi().alert("✅ Activadores reparados para estructura de 61 columnas.");
}
