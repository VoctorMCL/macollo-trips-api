/**
 * Lógica principal del panel: autenticación, diagnóstico y renderizado.
 */

function showLoading(text = "Analizando muestra...") {
    const overlay = document.getElementById("spinnerOverlay");
    const label = document.getElementById("spinnerText");
    if (label) label.textContent = text;
    if (overlay) overlay.style.display = "flex";
}

function hideLoading() {
    const overlay = document.getElementById("spinnerOverlay");
    if (overlay) overlay.style.display = "none";
}

function handleUnauthorized(response) {
    if (response.status === 401) {
        window.location.reload();
        return true;
    }
    return false;
}

document.addEventListener("DOMContentLoaded", () => {
    const loginScreen = document.getElementById("loginScreen");
    const appShell = document.getElementById("appShell");
    const loginForm = document.getElementById("loginForm");
    const loginError = document.getElementById("loginError");
    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const userChip = document.getElementById("userChip");

    let appInitialized = false;

    function showLogin() {
        if (appShell) appShell.hidden = true;
        if (loginScreen) loginScreen.style.display = "flex";
    }

    function enterApp(username) {
        if (loginScreen) loginScreen.style.display = "none";
        if (appShell) appShell.hidden = false;
        if (userChip) userChip.textContent = username || "admin";
        if (!appInitialized) {
            appInitialized = true;
            initApp();
        }
    }

    async function checkAuth() {
        try {
            const res = await fetch("/api/auth/me");
            if (res.ok) {
                const data = await res.json();
                enterApp(data.username);
            } else {
                showLogin();
            }
        } catch (err) {
            showLogin();
        }
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (loginError) loginError.textContent = "";
            if (loginBtn) {
                loginBtn.disabled = true;
                loginBtn.textContent = "Entrando...";
            }

            const username = document.getElementById("loginUser").value.trim();
            const password = document.getElementById("loginPass").value;

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!res.ok) {
                    let message = "Usuario o contraseña incorrectos.";
                    try {
                        const data = await res.json();
                        if (data.detail) message = data.detail;
                    } catch (e) {}
                    throw new Error(message);
                }

                const data = await res.json();
                document.getElementById("loginPass").value = "";
                enterApp(data.username);
            } catch (err) {
                if (loginError) loginError.textContent = err.message;
            } finally {
                if (loginBtn) {
                    loginBtn.disabled = false;
                    loginBtn.textContent = "Entrar";
                }
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            try {
                await fetch("/api/auth/logout", { method: "POST" });
            } finally {
                window.location.reload();
            }
        });
    }

    checkAuth();

    function initApp() {
        const videoEl = document.getElementById("cameraVideo");
        const previewEl = document.getElementById("imagePreview");
        const zoomRange = document.getElementById("zoomRange");
        const zoomVal = document.getElementById("zoomValue");

        const camera = new CameraController(videoEl, previewEl, zoomRange, zoomVal);
        const galleryUI = new GalleryUI();
        const apiKeysUI = new ApiKeysUI();

        camera.startCamera();

        // Tabs
        const tabs = document.querySelectorAll(".tab-btn");
        const tabContents = {
            scoutView: document.getElementById("scoutView"),
            galleryView: document.getElementById("galleryView"),
            apiView: document.getElementById("apiView"),
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
                if (target === "apiView") {
                    apiKeysUI.refresh();
                }
            });
        });

        // Camera controls
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
                    ejecutarDiagnostico(file);
                }
            });
        }

        if (captureBtn) {
            captureBtn.addEventListener("click", async () => {
                try {
                    if (previewEl.style.display === "block" && !camera.currentStream) {
                        await camera.startCamera();
                        return;
                    }

                    showLoading("Capturando imagen...");
                    const blob = await camera.captureFrame();
                    hideLoading();
                    ejecutarDiagnostico(blob);
                } catch (err) {
                    hideLoading();
                    console.warn("[Capture] Error capturando frame:", err);
                    if (fileUploadInput) fileUploadInput.click();
                }
            });
        }

        // Health
        checkApiHealth();
        setInterval(checkApiHealth, 25000);

        async function checkApiHealth() {
            const pill = document.getElementById("serverStatusPill");
            const text = document.getElementById("serverStatusText");
            try {
                const res = await fetch("/api/health");
                if (!res.ok) throw new Error("Respuesta no OK");
                const data = await res.json();
                if (pill) {
                    pill.style.borderColor = "var(--primary-border)";
                    pill.style.background = "var(--primary-soft)";
                }
                if (text) text.textContent = `Servicio activo (${(data.device || "cpu").toUpperCase()})`;
            } catch (e) {
                if (pill) {
                    pill.style.borderColor = "#f2c3be";
                    pill.style.background = "var(--danger-soft)";
                }
                if (text) text.textContent = "Sin conexión";
            }
        }

        // Diagnóstico
        async function ejecutarDiagnostico(imageBlob) {
            showLoading("Clasificando la muestra...");

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

                if (handleUnauthorized(res)) return;

                if (!res.ok) {
                    const errText = await res.text();
                    throw new Error(`Error en servidor (${res.status}): ${errText}`);
                }

                const data = await res.json();
                renderizarDiagnostico(data);
            } catch (err) {
                alert("No se pudo procesar la muestra: " + err.message);
            } finally {
                hideLoading();
            }
        }

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
                title.textContent = "Trips detectado";
                subtitle.textContent = `${data.detected_target} · ${data.inference_time_ms} ms`;

                stageName.textContent = data.detected_stage;
                stageDesc.textContent = `Certeza de la fase: ${(data.stage_confidence * 100).toFixed(1)}%`;

                if (data.cycle_info) {
                    urgencyBadge.textContent = `Nivel: ${data.cycle_info.urgency_level}`;
                    urgencyBadge.className = `urgency-badge ${data.cycle_info.urgency_level}`;
                    daysToAdult.textContent = data.cycle_info.days_to_adult;
                    urgencyRationale.textContent = `${data.cycle_info.urgency_rationale} (Temperatura considerada: ${data.cycle_info.temperature_c} °C)`;
                }

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
                title.textContent = "No corresponde a trips";
                subtitle.textContent = `Identificado como: ${data.detected_target} · ${data.inference_time_ms} ms`;

                stageName.textContent = "Sin infestación de trips";
                stageDesc.textContent = "La muestra no presenta morfología característica de Thripidae.";

                urgencyBadge.textContent = "Nivel: monitoreo";
                urgencyBadge.className = "urgency-badge MODERADO";
                daysToAdult.textContent = "Cultivo sin alerta";
                urgencyRationale.textContent = "Continúa con el monitoreo preventivo habitual.";

                if (recsSection) recsSection.style.display = "none";
            }

            if (data.exemplar_matches && data.exemplar_matches.length > 0) {
                exemplarBox.style.display = "block";
                exemplarDesc.innerHTML = data.exemplar_matches.map(m => `
                    <div style="margin-top:6px;">
                        <b>${m.filename}</b> [Fase: ${m.stage}] &rarr; Similitud: <b>${(m.similarity * 100).toFixed(1)}%</b>
                    </div>
                `).join("");
            } else {
                exemplarBox.style.display = "none";
            }

            card.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }
});
