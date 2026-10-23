/**
 * Ejemplo de Integración de la API de Trips con BioCLIP 2.5
 * para tu Plataforma Web Existente (SIATA / Open-Meteo / Google Sheets / Gulupa).
 *
 * Puedes copiar y adaptar esta función directamente en el código de tu página actual.
 */

// 1. Configura la URL donde corre tu servidor de la API (en tu servidor local o en la nube)
const TRIPS_API_BASE_URL = "http://localhost:8000"; // Reemplaza por la IP local ej: "http://192.168.1.50:8000"
const TRIPS_API_KEY = "mk_tu_clave_generada_en_el_panel"; // Genera la clave en la sección "API y accesos"

/**
 * Envía una foto tomada por la cámara a la API de BioCLIP 2.5
 * @param {File|Blob} imageFile - Archivo de imagen o blob capturado de la cámara
 * @param {number|null} temperatureC - Temperatura ambiente actual (ej. de tu API de Open-Meteo o SIATA)
 * @returns {Promise<Object>} Resultado fitosanitario de Trips en Gulupa
 */
async function analizarMuestraTripsGulupa(imageFile, temperatureC = null) {
    const formData = new FormData();
    formData.append("file", imageFile, "muestra_gulupa.jpg");
    
    // Si tu página ya tiene la temperatura de SIATA u Open-Meteo, la enviamos; si no, la API usará 20°C por defecto
    if (temperatureC !== null && !isNaN(temperatureC)) {
        formData.append("temperature_c", temperatureC.toString());
    }
    formData.append("crop", "gulupa");

    try {
        console.log(`[BioCLIP-Trips] Enviando muestra para análisis a ${TRIPS_API_BASE_URL}/api/predict...`);
        const response = await fetch(`${TRIPS_API_BASE_URL}/api/predict`, {
            method: "POST",
            headers: {
                // La API exige autenticación. La clave se genera en el panel web.
                "X-API-Key": TRIPS_API_KEY
            },
            body: formData,
            // NOTA: No definir manualmente 'Content-Type', el navegador asigna automáticamente multipart/form-data con boundary
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error en API BioCLIP (${response.status}): ${errorText}`);
        }

        const data = await response.json();
        console.log("[BioCLIP-Trips] Respuesta recibida:", data);
        return data;
    } catch (error) {
        console.error("[BioCLIP-Trips] Error al comunicar con la API:", error);
        throw error;
    }
}

/**
 * Ejemplo: Función para estructurar los datos y enviarlos a tu Google Sheet existente
 * @param {Object} apiResult - Objeto devuelto por analizarMuestraTripsGulupa
 * @param {string} loteInvernadero - Identificador del lote o módulo
 * @param {number} tempAmbiente - Temperatura de SIATA / Open-Meteo
 */
function formatearParaGoogleSheets(apiResult, loteInvernadero = "Lote 1", tempAmbiente = 20.0) {
    return {
        fechaHora: new Date().toISOString(),
        lote: loteInvernadero,
        cultivo: "Gulupa (Passiflora edulis)",
        temperaturaC: tempAmbiente,
        esTrips: apiResult.is_thrips ? "SÍ" : "NO",
        confianzaDeteccion: `${(apiResult.thrips_confidence * 100).toFixed(1)}%`,
        estadioBiologico: apiResult.detected_stage,
        confianzaEstadio: `${(apiResult.stage_confidence * 100).toFixed(1)}%`,
        urgenciaFitosanitaria: apiResult.cycle_info ? apiResult.cycle_info.urgency_level : "N/A",
        diasParaAdulto: apiResult.cycle_info ? apiResult.cycle_info.days_to_adult : "N/A",
        accionRecomendadaMIP: apiResult.recommendations 
            ? apiResult.recommendations.biological_control[0] 
            : "Monitoreo preventivo"
    };
}

// ---------------------------------------------------------------------------
// Ejemplo de uso rápido con un input de archivo HTML:
// <input type="file" id="cameraInput" accept="image/*" capture="environment">
// ---------------------------------------------------------------------------
/*
document.getElementById("cameraInput").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Supongamos que ya tienes la temperatura leída de tu API de SIATA o Open-Meteo:
    const tempActualSiata = 21.5; 

    try {
        const diagnostico = await analizarMuestraTripsGulupa(file, tempActualSiata);
        
        if (diagnostico.is_thrips) {
            alert(`⚠️ ALERTA TRIPS CONFIRMADO: ${diagnostico.detected_stage} (${(diagnostico.thrips_confidence * 100).toFixed(0)}% de confianza). Urgencia: ${diagnostico.cycle_info.urgency_level}`);
        } else {
            alert(`✅ No se detectó Trips. Clasificación: ${diagnostico.detected_target}`);
        }

        // Si usas Google Sheets para guardar la bitácora:
        const filaRegistro = formatearParaGoogleSheets(diagnostico, "Invernadero A", tempActualSiata);
        // await enviarAGoogleSheets(filaRegistro);

    } catch (err) {
        alert("Error al procesar la foto: " + err.message);
    }
});
*/
