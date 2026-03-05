/**
 * ============================================================
 * GIASSISTANT - CÓDIGO MAESTRO CONSOLIDADO (2026)
 * ============================================================
 * Este archivo contiene TODO: USD + Sincronización + Menú.
 * 
 * Instrucciones:
 * 1. Copiar este contenido en Extensiones > Apps Script del Google Sheet.
 * 2. Guardar y refrescar la planilla.
 * 3. Usar el menú 'GiAssistant > Reparar Activador' una vez.
 */

// --- CONFIGURACIÓN GLOBAL ---
const SERVICIOS_MASTER = [
  "Seleccion IT", 
  "Seleccion Generalista", 
  "Employee Experience",
  "Asesoria",
  "Capacitacion In Company", 
  "Workshop o Curso Online", 
  "Otros Ing", 
  "Outsourcing"
];

const HOJA_RTDO_FINAL = "RTDO";

// --- 1. MENÚ SUPERIOR ---
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 GiAssistant')
      .addItem('🔄 Actualizar USD Blue (Columna AT)', 'updateServiceRates')
      .addSeparator()
      .addItem('📥 Reconstruir RTDO', 'initialSyncAll')
      .addItem('🛠️ Reparar Activador', 'setupTrigger')
      .addToUi();
}

// --- 2. ACTUALIZACIÓN DE USD BLUE (COLUMNA AT) ---
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
      const headers = data[0];
      const idxIni = headers.indexOf("FECHA DE INICIO");
      const idxVen = headers.indexOf("FECHA DE VENTA/PRESUP");
      const idxMon = headers.indexOf("MONEDA");
      const colAT = 45; // Columna AT

      for (let i = 1; i < data.length; i++) {
        if (data[i][0] === "" || (data[i][colAT] !== "" && data[i][colAT] !== null)) continue;
        let valor = null;

        if (idxMon !== -1 && data[i][idxMon].toString().toUpperCase() === "USD") {
          valor = 1;
        } else {
          let d = (data[i][idxIni] instanceof Date && !isNaN(data[i][idxIni])) ? data[i][idxIni] : data[i][idxVen];
          if (!(d instanceof Date) || d.getFullYear() < 2026) continue;
          let iso = Utilities.formatDate(d, "GMT", "yyyy-MM-dd");
          if (d > new Date() && data[i][idxVen] instanceof Date && data[i][idxVen] <= new Date()) {
            iso = Utilities.formatDate(data[i][idxVen], "GMT", "yyyy-MM-dd");
          }
          const resDate = resolveDateFallback(iso, blueMap);
          if (resDate) valor = blueMap[resDate];
        }

        if (valor !== null) {
          const celda = sheet.getRange(i + 1, colAT + 1);
          celda.setValue(valor);
          celda.setNumberFormat("#,##0");
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
  const sheet = e.source.getActiveSheet();
  const name = sheet.getName().trim();
  const row = e.range.getRow();
  
  const prior = SERVICIOS_MASTER.map(s => s.toLowerCase()).indexOf(name.toLowerCase());
  if (prior === -1 || row === 1) return;

  const id = sheet.getRange(row, 1).getValue().toString().trim();
  if (!id) return;

  const ss = e.source;
  let destSheet = ss.getSheetByName(HOJA_RTDO_FINAL) || ss.insertSheet(HOJA_RTDO_FINAL);
  const data = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  const idNum = parseInt(id.match(/\d+/)) || 0;

  const rowToSync = [...data, prior, idNum];
  const destData = destSheet.getDataRange().getValues();
  let targetRow = -1;

  for (let i = 0; i < destData.length; i++) {
    if (destData[i][0] && destData[i][0].toString().trim().toLowerCase() === id.toLowerCase()) {
      targetRow = i + 1; break;
    }
  }

  if (targetRow !== -1) {
    destSheet.getRange(targetRow, 1, 1, rowToSync.length).setValues([rowToSync]);
  } else {
    destSheet.appendRow(rowToSync);
  }

  sortNaturalRTDO(destSheet);
}

function sortNaturalRTDO(sheet) {
  const lr = sheet.getLastRow();
  const lc = sheet.getLastColumn();
  if (lr > 1) {
    sheet.getRange(2, 1, lr - 1, lc).sort([{column: lc - 1, ascending: true}, {column: lc, ascending: true}]);
    sheet.hideColumns(lc - 1, 2);
  }
}

// --- 4. CARGA MASIVA (RECONSTRUIR RTDO) ---
function initialSyncAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dest = ss.getSheetByName(HOJA_RTDO_FINAL) || ss.insertSheet(HOJA_RTDO_FINAL);
  dest.clear();
  let first = true;
  SERVICIOS_MASTER.forEach((n, p) => {
    const s = ss.getSheetByName(n); if (!s) return;
    const d = s.getDataRange().getValues(); if (d.length < 2) return;
    if (first) { dest.appendRow([...d[0], "P", "N"]); first = false; }
    const rs = d.slice(1).filter(r => r[0]).map(r => [...r, p, parseInt(r[0].toString().match(/\d+/)) || 0]);
    if (rs.length > 0) dest.getRange(dest.getLastRow()+1, 1, rs.length, rs[0].length).setValues(rs);
  });
  sortNaturalRTDO(dest);
  SpreadsheetApp.getUi().alert("✅ Hoja RTDO reconstruida y ordenada.");
}

// --- 5. REPARAR ACTIVADOR ---
function setupTrigger() {
  const ts = ScriptApp.getProjectTriggers();
  ts.forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('onEditTrigger').forSpreadsheet(SpreadsheetApp.getActive()).onEdit().create();
  SpreadsheetApp.getUi().alert("✅ Activador reparado satisfactoriamente.");
}
