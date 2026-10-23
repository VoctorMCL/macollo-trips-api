/**
 * Lógica principal de la Web App: Diagnóstico en Invernadero, API y Renderizado.
 */

// Utilidades globales de UI
function showLoading(text = "Analizando muestra con BioCLIP 2.5...") {
    const overlay = document.getElementById("spinnerOverlay");
    const label = document.getElementById("spinnerText");
    if (label) label.textContent = text;
    if (overlay) overlay.style.display = "flex";
}

function hideLoading() {
    const overlay = document.getElementById("spinnerOverlay");
    if (overlay) overlay.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    // 1. Inicialización de Componentes
    const videoEl = document.getElementById("cameraVideo");
    const previewEl = document.getElementById("imagePreview");
    const zoomRange = document.getElementById("zoomRange");
    const zoomVal = document.getElementById("zoomValue");
    
    const camera = new CameraController(videoEl, previewEl, zoomRange, zoomVal);
    const galleryUI = new GalleryUI();

    // Iniciar cámara por defecto si está disponible
    camera.startCamera();

    // 2. Control de Pestañas (Tabs)
    const tabs = document.querySelectorAll(".tab-btn");
    const tabContents = {
        scoutView: document.getElementById("scoutView"),
        galleryView: document.getElementById("galleryView"),
        handbookView: document.getElementById("handbookView")
    };

    tabs.forEach(btn => {
        btn.addEventListener("click", () => {
            tabs.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const target = btn.dataset.tab;
            Object.keys(tabContents).forEach(k => {
                if (tabContents[k]) {
                    tabContents[k].style.display = (k === target) ? "block" : "none";
                }
            });

            if (target === "galleryView") {
                galleryUI.refreshStats();
            }
        });
    });

    // 3. Botones de Cámara
    const captureBtn = document.getElementById("captureBtn");
    const switchCameraBtn = document.getElementById("switchCameraBtn");
    const fileUploadInput = document.getElementById("fileUploadInput");

    if (switchCameraBtn) {
        switchCameraBtn.addEventListener("click", () => camera.switchCamera());
    }

    if (fileUploadInput) {
        fileUploadInput.addEventListener("change", async (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                await camera.loadFromFile(file);
                // Analizar automáticamente al subir archivo
                ejecutarDiagnostico(file);
            }
        });
    }

    if (captureBtn) {
        captureBtn.addEventListener("click", async () => {
            try {
                // Si ya hay una foto congelada en preview, reabrir cámara
                if (previewEl.style.display === "block" && !camera.currentStream) {
                    await camera.startCamera();
                    return;
                }

                showLoading("Capturando imagen con enfoque macro...");
                const blob = await camera.captureFrame();
                hideLoading();
                ejecutarDiagnostico(blob);
            } catch (err) {
                hideLoading();
                console.warn("[Capture] Error capturando frame:", err);
                // Si la cámara no está activa, abrir selector de archivos
                if (fileUploadInput) fileUploadInput.click();
            }
        });
    }

    // 4. Verificación de Conexión con la API
    checkApiHealth();
    setInterval(checkApiHealth, 25000);

    async function checkApiHealth() {
        const pill = document.getElementById("serverStatusPill");
        const text = document.getElementById("serverStatusText");
        try {
            const res = await fetch("/api/health");
            if (res.ok) {
                const data = await res.json();
                if (pill) {
                    pill.style.borderColor = "rgba(16, 185, 129, 0.4)";
                    pill.style.background = "rgba(16, 185, 129, 0.1)";
                }
                if (text) text.textContent = `Online (${data.device.toUpperCase()})`;
            } else {
                throw new Error("Respuesta no OK");
            }
        } catch (e) {
            if (pill) {
                pill.style.borderColor = "rgba(244, 63, 94, 0.4)";
                pill.style.background = "rgba(244, 63, 94, 0.1)";
            }
            if (text) text.textContent = "Reconectando API...";
        }
    }

    // 5. Envío y Diagnóstico
    async function ejecutarDiagnostico(imageBlob) {
        showLoading("BioCLIP 2.5 procesando clasificación taxonómica y de estadios...");
        
        const tempInput = document.getElementById("tempInput");
        const tempVal = tempInput ? parseFloat(tempInput.value) || 20.0 : 20.0;

        const formData = new FormData();
        formData.append("file", imageBlob, "muestra_gulupa.jpg");
        formData.append("temperature_c", tempVal.toString());
        formData.append("crop", "gulupa");

        try {
            const res = await fetch("/api/predict", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(`Error en servidor (${res.status}): ${errText}`);
            }

            const data = await res.json();
            renderizarDiagnostico(data);
        } catch (err) {
            alert("❌ Error al procesar la muestra: " + err.message);
        } finally {
            hideLoading();
        }
    }

    // 6. Renderizado de Resultados en Pantalla
    function renderizarDiagnostico(data) {
        const card = document.getElementById("diagnosisCard");
        const banner = document.getElementById("alertBanner");
        const title = document.getElementById("resultTitle");
        const subtitle = document.getElementById("resultSubtitle");
        const confVal = document.getElementById("confidenceVal");
        
        const stageName = document.getElementById("stageName");
        const stageDesc = document.getElementById("stageDesc");
        const urgencyBadge = document.getElementById("urgencyBadge");
        const daysToAdult = document.getElementById("daysToAdult");
        const urgencyRationale = document.getElementById("urgencyRationale");
        
        const recsSection = document.getElementById("recsSection");
        const bioList = document.getElementById("bioList");
        const ethoList = document.getElementById("ethoList");
        const cultList = document.getElementById("cultList");
        const chemList = document.getElementById("chemList");
        const exportAlertText = document.getElementById("exportAlertText");

        const exemplarBox = document.getElementById("exemplarBox");
        const exemplarDesc = document.getElementById("exemplarDesc");

        if (card) card.style.display = "block";

        const confPct = (data.thrips_confidence * 100).toFixed(1);
        if (confVal) confVal.textContent = `${confPct}%`;

        if (data.is_thrips) {
            banner.className = "alert-banner thrips-detected";
            title.innerHTML = `⚠️ CONFIRMADO: TRIPS DETECTADO`;
            subtitle.textContent = `${data.detected_target} | Latencia: ${data.inference_time_ms} ms`;

            stageName.textContent = data.detected_stage;
            stageDesc.textContent = `Certeza de estadio: ${(data.stage_confidence * 100).toFixed(1)}%`;

            if (data.cycle_info) {
                urgencyBadge.textContent = `Nivel: ${data.cycle_info.urgency_level}`;
                urgencyBadge.className = `urgency-badge ${data.cycle_info.urgency_level}`;
                daysToAdult.textContent = data.cycle_info.days_to_adult;
                urgencyRationale.textContent = `${data.cycle_info.urgency_rationale} (Temp considerada: ${data.cycle_info.temperature_c}°C)`;
            }

            // Recomendaciones MIP
            if (data.recommendations && recsSection) {
                recsSection.style.display = "block";
                bioList.innerHTML = data.recommendations.biological_control.map(i => `<li>${i}</li>`).join("");
                ethoList.innerHTML = data.recommendations.ethological_control.map(i => `<li>${i}</li>`).join("");
                cultList.innerHTML = data.recommendations.cultural_control.map(i => `<li>${i}</li>`).join("");
                chemList.innerHTML = data.recommendations.chemical_biorational_control.map(i => `<li>${i}</li>`).join("");
                exportAlertText.textContent = data.recommendations.export_impact_alert;
            }
        } else {
            banner.className = "alert-banner clean-leaf";
            title.innerHTML = `✅ NO CORRESPONDE A TRIPS`;
            subtitle.textContent = `Identificado como: ${data.detected_target} | Latencia: ${data.inference_time_ms} ms`;

            stageName.textContent = "Sin infestación de Trips";
            stageDesc.textContent = `La muestra no presenta morfología característica de Thripidae.`;

            urgencyBadge.textContent = "Nivel: BAJO / MONITOREO";
            urgencyBadge.className = "urgency-badge MODERADO";
            daysToAdult.textContent = "Cultivo protegido";
            urgencyRationale.textContent = "Continúa con el monitoreo preventivo habitual en espalderas y flores.";

            if (recsSection) recsSection.style.display = "none";
        }

        // Mostrar coincidencias con galería de fotos del usuario si existen
        if (data.exemplar_matches && data.exemplar_matches.length > 0) {
            exemplarBox.style.display = "block";
            exemplarDesc.innerHTML = data.exemplar_matches.map(m => `
                <div style="margin-top:6px;">
                    <b>${m.filename}</b> [Estadio: ${m.stage}] &rarr; Similitud empírica: <b>${(m.similarity * 100).toFixed(1)}%</b>
                </div>
            `).join("");
        } else {
            exemplarBox.style.display = "none";
        }

        // Scroll suave al diagnóstico
        card.scrollIntoView({ behavior: "smooth", block: "start" });
    }
});
