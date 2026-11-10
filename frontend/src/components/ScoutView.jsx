import React, { useEffect, useState, useRef } from "react";
import DiagnosisCard from "./DiagnosisCard";

export default function ScoutView({
  camera,
  temperature,
  onTemperatureChange,
  profiles = [],
  selectedProfile = "trips",
  onProfileChange,
  showLoading,
  hideLoading,
  onUnauthorized
}) {
  const [diagnosis, setDiagnosis] = useState(null);
  const fileInputRef = useRef(null);
  const cardRef = useRef(null);

  const activeProfile =
    profiles.find((profile) => profile.key === selectedProfile) || null;

  useEffect(() => {
    // Evita mostrar un diagnóstico de un perfil anterior al cambiar de perfil.
    setDiagnosis(null);
  }, [selectedProfile]);

  const handleCaptureAndPredict = async () => {
    try {
      // Si la cámara estaba congelada con un preview previo, reactivarla
      if (camera.previewSrc && !camera.cameraActive) {
        await camera.startCamera();
        return;
      }

      showLoading("Capturando imagen con zoom macro...");
      const blob = await camera.captureFrame();
      hideLoading();
      await executePrediction(blob);
    } catch (err) {
      hideLoading();
      console.warn("[Capture] Fallback a selector de archivos:", err);
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await camera.loadFromFile(file);
      await executePrediction(file);
    }
  };

  const executePrediction = async (imageBlob) => {
    showLoading("Clasificando muestra con BioCLIP 2.5...");

    const formData = new FormData();
    formData.append("file", imageBlob, `muestra_${selectedProfile}.jpg`);
    formData.append("temperature_c", (parseFloat(temperature) || 20.0).toString());
    formData.append("profile", selectedProfile);
    formData.append("crop", "gulupa");

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        body: formData
      });

      if (res.status === 401) {
        onUnauthorized();
        return;
      }

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Error en servidor (${res.status}): ${errText}`);
      }

      const data = await res.json();
      setDiagnosis(data);

      setTimeout(() => {
        if (cardRef.current) {
          cardRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    } catch (err) {
      alert("No se pudo procesar la muestra: " + err.message);
    } finally {
      hideLoading();
    }
  };

  return (
    <section className="tab-content" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>Inspección de campo</h2>
        <p>
          Toma una foto de la hoja, flor o fruto y la API identificará el objetivo
          seleccionado{activeProfile ? `: ${activeProfile.name.toLowerCase()}` : ""}.
        </p>
      </div>

      <div className="env-bar">
        <div className="env-title">
          <span>Perfil de detección</span>
          <span className="crop-pill">
            Cultivo: {activeProfile?.crop === "gulupa" ? "Gulupa" : activeProfile?.crop || "Gulupa"}
          </span>
        </div>
        <div className="env-controls">
          <div className="stage-select-row">
            <label htmlFor="profileSelect">Perfil</label>
            <select
              id="profileSelect"
              value={selectedProfile}
              onChange={(e) => onProfileChange && onProfileChange(e.target.value)}
            >
              {profiles.length === 0 && <option value="trips">Trips</option>}
              {profiles.map((profile) => (
                <option key={profile.key} value={profile.key}>
                  {profile.name}
                  {profile.experimental ? " (experimental)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div
            className="temp-input-wrapper"
            title="Temperatura leída de tu estación o ingresada manualmente"
          >
            <label htmlFor="tempInput">Temp.</label>
            <input
              type="number"
              id="tempInput"
              value={temperature}
              step="0.5"
              min="10"
              max="38"
              onChange={(e) => onTemperatureChange(e.target.value)}
            />
            <span>°C</span>
          </div>
        </div>
      </div>

      {activeProfile?.description && (
        <p className="card-desc" style={{ marginTop: -8, marginBottom: 16 }}>
          {activeProfile.description}
          {activeProfile.experimental
            ? " Perfil experimental: calíbralo con fotos reales de la galería."
            : ""}
        </p>
      )}

      <div className="camera-card">
        <div className="viewport-container">
          <video
            ref={camera.videoRef}
            autoPlay
            playsInline
            muted
            style={{
              display: camera.previewSrc ? "none" : "block",
              transform: `scale(${camera.zoomFactor})`
            }}
          />

          {camera.previewSrc && (
            <img
              src={camera.previewSrc}
              alt="Captura de la muestra"
              style={{
                display: "block",
                transform: `scale(${camera.zoomFactor})`
              }}
            />
          )}

          {!camera.previewSrc && (
            <div className="crosshair-overlay" style={{ display: "flex" }}>
              <div className="macro-target"></div>
              <div className="target-hint">Centra el insecto, la lesión o el fruto</div>
            </div>
          )}
        </div>

        <div className="camera-controls">
          <div className="zoom-slider-row">
            <span>Zoom macro</span>
            <input
              type="range"
              min="1"
              max="4"
              step="0.1"
              value={camera.zoomFactor}
              onChange={(e) => camera.setZoomFactor(parseFloat(e.target.value))}
            />
            <span className="mono">{camera.zoomFactor.toFixed(1)}x</span>
          </div>

          <div className="buttons-row">
            <button
              className="btn-icon"
              type="button"
              onClick={camera.switchCamera}
              title="Cambiar cámara"
            >
              ↻
            </button>

            <button
              className="btn-capture"
              type="button"
              onClick={handleCaptureAndPredict}
              title={camera.previewSrc ? "Volver a activar cámara" : "Tomar foto y analizar"}
            />

            <button
              className="btn-icon"
              type="button"
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
              title="Subir foto de galería"
            >
              +
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
          </div>
        </div>
      </div>

      <div ref={cardRef}>
        <DiagnosisCard data={diagnosis} />
      </div>
    </section>
  );
}
