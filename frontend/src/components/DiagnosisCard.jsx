import React from "react";

export default function DiagnosisCard({ data }) {
  if (!data) return null;

  const isThrips = data.is_thrips;
  const thripsConfPct = (data.thrips_confidence * 100).toFixed(1);
  const stageConfPct = (data.stage_confidence * 100).toFixed(1);

  return (
    <div className="diagnosis-container" style={{ display: "block" }}>
      <div className={`alert-banner ${isThrips ? "thrips-detected" : "clean-leaf"}`}>
        <div className="alert-header">
          <h2>{isThrips ? "Trips detectado" : "No corresponde a trips"}</h2>
          <p>
            {isThrips
              ? `${data.detected_target} · ${data.inference_time_ms} ms`
              : `Identificado como: ${data.detected_target} · ${data.inference_time_ms} ms`}
          </p>
        </div>
        <div className="confidence-chip">
          <div className="card-label">Certeza</div>
          <div className="confidence-val">{thripsConfPct}%</div>
        </div>
      </div>

      <div className="results-grid">
        <div className="info-card">
          <div className="card-label">Fase identificada</div>
          <div className="card-val-lg">
            {isThrips ? data.detected_stage : "Sin infestación de trips"}
          </div>
          <div className="card-desc">
            {isThrips
              ? `Certeza de la fase: ${stageConfPct}%`
              : "La muestra no presenta morfología característica de Thripidae."}
          </div>
        </div>

        <div className="info-card">
          <div className="card-label">Ciclo y urgencia</div>
          {isThrips && data.cycle_info ? (
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
                Continúa con el monitoreo preventivo habitual en espalderas y botones.
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
                <b>{match.filename}</b> [Fase: {match.stage}] &rarr; Similitud:{" "}
                <b>{(match.similarity * 100).toFixed(1)}%</b>
              </div>
            ))}
          </div>
        </div>
      )}

      {isThrips && data.recommendations && (
        <div className="recs-card">
          <div className="recs-header">
            <h3>Plan de acción (MIP Gulupa)</h3>
          </div>

          <div className="rec-group">
            <div className="rec-group-title">1. Control biológico</div>
            <ul className="rec-list">
              {data.recommendations.biological_control.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rec-group">
            <div className="rec-group-title">2. Control etológico</div>
            <ul className="rec-list">
              {data.recommendations.ethological_control.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rec-group">
            <div className="rec-group-title">3. Control cultural</div>
            <ul className="rec-list">
              {data.recommendations.cultural_control.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rec-group">
            <div className="rec-group-title">4. Control biorracional y químico</div>
            <ul className="rec-list">
              {data.recommendations.chemical_biorational_control.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="export-warning-box">
            <div>{data.recommendations.export_impact_alert}</div>
          </div>
        </div>
      )}
    </div>
  );
}
