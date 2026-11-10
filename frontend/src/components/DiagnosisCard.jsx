import React from "react";

const CATEGORY_LABELS = {
  pest: "Plaga",
  disease: "Enfermedad",
  damage: "Daño",
  healthy: "Tejido sano",
  other: "Otro"
};

export default function DiagnosisCard({ data }) {
  if (!data) return null;

  // Compatibilidad con respuestas 1.x y contrato genérico 2.x
  const detection = data.detection || null;
  const isPositive = detection ? detection.is_positive : data.is_thrips;
  const confidence = detection ? detection.confidence : data.thrips_confidence;
  const profileName = detection?.profile_name || "Trips";
  const targetName = detection?.target_name || data.detected_target;
  const scientificName = detection?.scientific_name;
  const category = detection?.category;
  const isUncertain = Boolean(detection?.is_uncertain);

  const confidencePct = ((confidence || 0) * 100).toFixed(1);
  const stageConfPct = ((data.stage_confidence || 0) * 100).toFixed(1);

  const stageLabel = "Fase identificada";
  const cycleLabel = "Ciclo y urgencia";
  const stageValue = isPositive
    ? data.detected_stage
    : `Sin detección de ${profileName.toLowerCase()}`;

  return (
    <div className="diagnosis-container" style={{ display: "block" }}>
      <div className={`alert-banner ${isPositive ? "thrips-detected" : "clean-leaf"}`}>
        <div className="alert-header">
          <h2>
            {isPositive ? `${targetName} detectado` : `No se detectó ${profileName.toLowerCase()}`}
          </h2>
          <p>
            {isPositive
              ? `${scientificName ? scientificName + " · " : ""}${profileName} · ${data.inference_time_ms} ms`
              : `Identificado como: ${data.detected_target} · ${data.inference_time_ms} ms`}
          </p>
          {isPositive && category && (
            <span className={`category-chip category-${category}`}>
              {CATEGORY_LABELS[category] || category}
            </span>
          )}
        </div>
        <div className="confidence-chip">
          <div className="card-label">Certeza</div>
          <div className="confidence-val">{confidencePct}%</div>
        </div>
      </div>

      {isUncertain && (
        <div className="uncertain-banner">
          ⚠️ Confianza cerca del umbral de decisión. Toma otra foto más cercana o
          refuerza la galería de referencia antes de tomar una decisión de manejo.
        </div>
      )}

      <div className="results-grid">
        <div className="info-card">
          <div className="card-label">{stageLabel}</div>
          <div className="card-val-lg">{stageValue}</div>
          <div className="card-desc">
            {isPositive
              ? `Certeza del estadio: ${stageConfPct}%`
              : detection?.target_description ||
                "La muestra no presenta la morfología o sintomatología esperada."}
          </div>
        </div>

        <div className="info-card">
          <div className="card-label">{cycleLabel}</div>
          {isPositive && data.cycle_info ? (
            <>
              <div className={`urgency-badge ${data.cycle_info.urgency_level}`}>
                Nivel: {data.cycle_info.urgency_level}
              </div>
              <div className="card-val-lg">{data.cycle_info.days_to_adult}</div>
              <div className="card-desc">
                {data.cycle_info.urgency_rationale} (Temperatura considerada:{" "}
                {data.cycle_info.temperature_c} °C)
              </div>
            </>
          ) : (
            <>
              <div className="urgency-badge MODERADO">Nivel: monitoreo</div>
              <div className="card-val-lg">Cultivo sin alerta</div>
              <div className="card-desc">
                Continúa con el monitoreo preventivo y revisa la galería de referencia.
              </div>
            </>
          )}
        </div>
      </div>

      {data.exemplar_matches && data.exemplar_matches.length > 0 && (
        <div className="info-card" style={{ marginBottom: 24 }}>
          <div className="card-label">Coincidencias con la galería local</div>
          <div className="card-desc">
            {data.exemplar_matches.map((match, idx) => (
              <div key={idx} style={{ marginTop: 6 }}>
                <b>{match.filename}</b> [{match.target || match.stage}] &rarr; Similitud:{" "}
                <b>{(match.similarity * 100).toFixed(1)}%</b>
              </div>
            ))}
          </div>
        </div>
      )}

      {isPositive && data.recommendations && (
        <div className="recs-card">
          <div className="recs-header">
            <h3>Plan de acción ({profileName})</h3>
          </div>

          {data.recommendations.biological_control && (
            <div className="rec-group">
              <div className="rec-group-title">1. Control biológico</div>
              <ul className="rec-list">
                {data.recommendations.biological_control.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {data.recommendations.ethological_control && (
            <div className="rec-group">
              <div className="rec-group-title">2. Control etológico y monitoreo</div>
              <ul className="rec-list">
                {data.recommendations.ethological_control.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {data.recommendations.cultural_control && (
            <div className="rec-group">
              <div className="rec-group-title">3. Control cultural</div>
              <ul className="rec-list">
                {data.recommendations.cultural_control.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {data.recommendations.chemical_biorational_control && (
            <div className="rec-group">
              <div className="rec-group-title">4. Control biorracional y químico</div>
              <ul className="rec-list">
                {data.recommendations.chemical_biorational_control.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {data.recommendations.export_impact_alert && (
            <div className="export-warning-box">
              <div>{data.recommendations.export_impact_alert}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
