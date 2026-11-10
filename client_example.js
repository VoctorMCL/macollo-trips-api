/**
 * Ejemplo de integración de la API de Visión Fitosanitaria con BioCLIP 2.5
 * para tu plataforma web existente (SIATA / Open-Meteo / Google Sheets / Gulupa).
 *
 * Perfiles disponibles: "trips", "moscas" y "aranas_rojas".
 * Puedes copiar y adaptar estas funciones directamente en tu página actual.
 */

// 1. Configura la URL donde corre tu servidor de la API (local o en la nube)
const FITOSANITARIA_API_BASE_URL = "http://localhost:8000"; // Ej. local: "http://192.168.1.50:8000"
const FITOSANITARIA_API_KEY = "mk_tu_clave_generada_en_el_panel"; // Genera la clave en "API y accesos"

/**
 * Envía una foto tomada por la cámara a la API de BioCLIP 2.5.
 *
 * @param {File|Blob} imageFile - Archivo de imagen o blob capturado de la cámara.
 * @param {"trips"|"moscas"|"aranas_rojas"} profile - Perfil fitosanitario a evaluar.
 * @param {number|null} temperatureC - Temperatura ambiente actual (SIATA, Open-Meteo o sensor).
 * @returns {Promise<Object>} Respuesta completa de /api/predict.
 */
async function analizarMuestraFitosanitaria(imageFile, profile = "trips", temperatureC = null) {
    const formData = new FormData();
    formData.append("file", imageFile, "muestra_gulupa.jpg");
    formData.append("profile", profile);
    formData.append("crop", "gulupa");

    // Si tu página ya tiene la temperatura de SIATA u Open-Meteo, la enviamos;
    // si no, la API usará 20 °C por defecto.
    if (temperatureC !== null && !isNaN(temperatureC)) {
        formData.append("temperature_c", temperatureC.toString());
    }

    try {
        console.log(
            `[BioCLIP] Enviando muestra (${profile}) a ${FITOSANITARIA_API_BASE_URL}/api/predict...`
        );
        const response = await fetch(`${FITOSANITARIA_API_BASE_URL}/api/predict`, {
            method: "POST",
            headers: {
                // La API exige autenticación. La clave se genera en el panel web.
                "X-API-Key": FITOSANITARIA_API_KEY,
            },
            body: formData,
            // NOTA: No definir manualmente 'Content-Type'; el navegador asigna
            // automáticamente multipart/form-data con su boundary.
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error en API BioCLIP (${response.status}): ${errorText}`);
        }

        const data = await response.json();
        console.log(`[BioCLIP] Respuesta recibida (${profile}):`, data);
        return data;
    } catch (error) {
        console.error("[BioCLIP] Error al comunicar con la API:", error);
        throw error;
    }
}

/**
 * Estructura la respuesta de la API para enviarla a tu Google Sheet o base de datos.
 *
 * @param {Object} apiResult - Objeto devuelto por analizarMuestraFitosanitaria.
 * @param {string} loteInvernadero - Identificador del lote o módulo.
 * @param {number} tempAmbiente - Temperatura de SIATA / Open-Meteo.
 */
function formatearParaGoogleSheets(apiResult, loteInvernadero = "Lote 1", tempAmbiente = 20.0) {
    const det = apiResult.detection ?? {};
    const confianza = det.confidence ?? apiResult.thrips_confidence ?? 0;

    return {
        fechaHora: new Date().toISOString(),
        lote: loteInvernadero,
        cultivo: apiResult.crop ?? "Gulupa (Passiflora edulis)",
        perfil: apiResult.profile ?? det.profile ?? "trips",
        temperaturaC: tempAmbiente,
        objetivoPositivo: det.is_positive ? "SÍ" : "NO",
        categoria: det.category ?? "N/A",
        objetivoDetectado: det.target_name ?? apiResult.detected_target ?? "N/A",
        nombreCientifico: det.scientific_name ?? "",
        confianzaDeteccion: `${(confianza * 100).toFixed(1)}%`,
        resultadoIncierto: det.is_uncertain ? "SÍ" : "NO",
        estadioBiologico: apiResult.detected_stage ?? "N/A",
        confianzaEstadio: `${((apiResult.stage_confidence ?? 0) * 100).toFixed(1)}%`,
        urgenciaFitosanitaria: apiResult.cycle_info ? apiResult.cycle_info.urgency_level : "N/A",
        diasParaAdulto: apiResult.cycle_info ? apiResult.cycle_info.days_to_adult : "N/A",
        accionRecomendadaMIP: apiResult.recommendations
            ? apiResult.recommendations.biological_control[0]
            : "Monitoreo preventivo",
    };
}

// ---------------------------------------------------------------------------
// Ejemplo de uso rápido con un input de archivo HTML:
// <select id="perfil">
//   <option value="trips">Trips</option>
//   <option value="moscas">Moscas de la Fruta</option>
//   <option value="aranas_rojas">Arañas Rojas</option>
// </select>
// <input type="file" id="cameraInput" accept="image/*" capture="environment">
// ---------------------------------------------------------------------------
/*
document.getElementById("cameraInput").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const perfil = document.getElementById("perfil")?.value ?? "trips";

    // Supongamos que ya tienes la temperatura leída de tu API de SIATA o Open-Meteo:
    const tempActualSiata = 21.5;

    try {
        const diagnostico = await analizarMuestraFitosanitaria(file, perfil, tempActualSiata);
        const det = diagnostico.detection ?? {};

        if (det.is_positive) {
            alert(
                `⚠️ ${det.target_name} confirmado: ${diagnostico.detected_stage} ` +
                `(${(det.confidence * 100).toFixed(0)}% de confianza). ` +
                `Urgencia: ${diagnostico.cycle_info?.urgency_level ?? "N/A"}`
            );
        } else {
            alert(`✅ Sin detección positiva. Clasificación: ${diagnostico.detected_target}`);
        }

        // Si usas Google Sheets para guardar la bitácora:
        const filaRegistro = formatearParaGoogleSheets(diagnostico, "Invernadero A", tempActualSiata);
        // await enviarAGoogleSheets(filaRegistro);

    } catch (err) {
        alert("Error al procesar la foto: " + err.message);
    }
});
*/
