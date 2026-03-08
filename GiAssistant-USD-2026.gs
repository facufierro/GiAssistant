/**
 * ==========================================
 * GIASSISTANT - USD AUTOMÁTICO (EDICIÓN 2026)
 * ==========================================
 */

// 1. CONFIGURACIÓN DE HOJAS Y COLUMNAS
const CONFIG_SHEETS = [
  { id: "16GpI2yKovf5sqyeBD42CAMP1W4C2-Ap_tpuoBPBv34s", name: "Ventas", dateCol: "FECHA DE INGRESO", rateCol: "COTIZACIÓN OFICIAL", type: "Oficial" },
  { id: "16GpI2yKovf5sqyeBD42CAMP1W4C2-Ap_tpuoBPBv34s", name: "Ventas", dateCol: "FECHA DE INGRESO", rateCol: "COTIZACIÓN BLUE", type: "Blue" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Selección IT", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Selección", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Employee Experience", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Cap. In Company", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Workshop", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", name: "Otros Ing", dateCol: "FECHA DE INICIO", rateCol: "COTIZ", type: "Blue", currencyCol: "MONEDA" },
  { id: "1amlJG3ggXYm7tuyAxxsQIN9pg47u9y1tk4cW2gaSr5o", name: "Hoja 1", dateCol: "Fecha de inicio", rateCol: "Cotiz USD", type: "Blue" }
];

// 2. CREACIÓN DEL MENÚ EN LA PLANILLA
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 GiAssistant')
      .addItem('🔄 Actualizar Todo (2026+)', 'mainUpdateAction')
      .addSeparator()
      .addItem('💰 Completar Ventas (Columna G - 2026+)', 'updateMissingSalesRates')
      .addToUi();
}

/**
 * 3. FUNCIÓN DE ACTUALIZACIÓN DUAL (PARA HOJA VENTAS)
 * Utiliza estrictamente la Columna G (FECHA DE VENTA)
 */
function updateMissingSalesRates() {
  const SHEET_ID = "16GpI2yKovf5sqyeBD42CAMP1W4C2-Ap_tpuoBPBv34s";
  const SHEET_NAME = "Ventas";
  
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = ss.getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  // Identificar índices de columnas
  const ventaIdx = headers.indexOf("FECHA DE VENTA");    // Columna G
  const offIdx = headers.indexOf("COTIZACIÓN OFICIAL");  // Columna R
  const blueIdx = headers.indexOf("COTIZACIÓN BLUE");    // Columna S

  if (ventaIdx === -1) return SpreadsheetApp.getUi().alert("Error: No se encontró la columna 'FECHA DE VENTA' (Check Col G)");

  const ratesData = fetchRates();
  const officialMap = mapRates(ratesData, "Oficial");
  const blueMap = mapRates(ratesData, "Blue");

  let updatedCount = 0;

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    let dateVal = row[ventaIdx];

    // Verificar que sea una fecha válida del 2026 en adelante
    if (!dateVal || isNaN(Date.parse(dateVal))) continue;
    let d = new Date(dateVal);
    if (d.getFullYear() < 2026) continue;

    const currentOfficial = row[offIdx];
    const currentBlue = row[blueIdx];

    // Solo si falta alguna de las dos cotizaciones
    if (currentOfficial === "" || currentBlue === "") {
      const isoDate = Utilities.formatDate(d, "GMT", "yyyy-MM-dd");
      const resolvedDateStr = resolveDate(isoDate, officialMap);

      if (resolvedDateStr) {
        // Actualizar Oficial si está vacío
        if (currentOfficial === "") {
          sheet.getRange(i + 1, offIdx + 1).setValue(officialMap[resolvedDateStr]);
        }
        // Actualizar Blue si está vacío
        if (currentBlue === "") {
          sheet.getRange(i + 1, blueIdx + 1).setValue(blueMap[resolvedDateStr]);
        }
        updatedCount++;
      }
    }
  }
  SpreadsheetApp.getUi().alert("✅ Ventas Finalizado.\nRegistros de 2026 actualizados: " + updatedCount);
}

/**
 * 4. FUNCIÓN PARA EL RESTO DE LAS HOJAS
 */
function mainUpdateAction() {
  const ratesData = fetchRates();
  let summary = "Resumen Actualización 2026+:\n";

  CONFIG_SHEETS.forEach(conf => {
    try {
      const ss = SpreadsheetApp.openById(conf.id);
      const sheet = ss.getSheetByName(conf.name);
      if (!sheet) return;

      const data = sheet.getDataRange().getValues();
      const headers = data[0];
      const dateIdx = headers.indexOf(conf.dateCol);
      const rateIdx = headers.indexOf(conf.rateCol);
      const currIdx = conf.currencyCol ? headers.indexOf(conf.currencyCol) : -1;

      if (dateIdx === -1 || rateIdx === -1) return;

      const rateMap = mapRates(ratesData, conf.type);
      let count = 0;

      for (let i = 1; i < data.length; i++) {
        const row = data[i];
        let dateVal = row[dateIdx];

        if (!dateVal || isNaN(Date.parse(dateVal))) continue;
        let d = new Date(dateVal);
        if (d.getFullYear() < 2026) continue;
        if (row[rateIdx] !== "") continue; 

        // Caso moneda USD
        if (currIdx !== -1 && row[currIdx].toString().toUpperCase() === "USD") {
          sheet.getRange(i + 1, rateIdx + 1).setValue(1);
          count++;
          continue;
        }

        const isoDate = Utilities.formatDate(d, "GMT", "yyyy-MM-dd");
        const resolvedDateStr = resolveDate(isoDate, rateMap);

        if (resolvedDateStr) {
          sheet.getRange(i + 1, rateIdx + 1).setValue(rateMap[resolvedDateStr]);
          count++;
        }
      }
      summary += `- ${conf.name} (${conf.rateCol}): ${count} filas.\n`;
    } catch (e) {
      summary += `- Error en ${conf.name}: ${e.message}\n`;
    }
  });

  SpreadsheetApp.getUi().alert(summary);
}

// --- UTILIDADES INTERNAS ---

function fetchRates() {
  const url = "https://api.bluelytics.com.ar/v2/evolution.json";
  return JSON.parse(UrlFetchApp.fetch(url).getContentText());
}

function mapRates(data, source) {
  const map = {};
  data.forEach(r => { if (r.source === source) map[r.date] = r.value_sell; });
  return map;
}

function resolveDate(targetDateStr, rateMap) {
  if (!targetDateStr) return null;
  let d = new Date(targetDateStr + "T12:00:00");
  let today = new Date();
  today.setHours(12, 0, 0, 0);

  // Si es una fecha futura, usamos la cotización de hoy (estimación)
  if (d > today) d = today;
  
  // Retroceder hasta 15 días para encontrar una cotización (fines de semana/feriados)
  for (let i = 0; i <= 15; i++) {
    let check = new Date(d);
    check.setDate(d.getDate() - i);
    
    // Ignorar Sábados (6) y Domingos (0)
    if (check.getDay() === 0 || check.getDay() === 6) continue;
    
    let key = Utilities.formatDate(check, "GMT", "yyyy-MM-dd");
    if (rateMap[key]) return key;
  }
  return null;
}
