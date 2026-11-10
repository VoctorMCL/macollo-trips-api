import React, { useEffect, useState } from "react";

const KIND_LABELS = {
  pest: "Plaga",
  disease: "Enfermedad",
  damage: "Daño",
  healthy: "Tejido sano",
  other: "Otro"
};

export default function HandbookView({ profiles = [], selectedProfile = "trips", onProfileChange }) {
  const [handbook, setHandbook] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`/api/handbook?profile=${encodeURIComponent(selectedProfile)}&temperature_c=20`);
        if (!res.ok) {
          throw new Error(`No se pudo cargar la ficha (${res.status})`);
        }
        const data = await res.json();
        if (active) setHandbook(data);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [selectedProfile]);

  const profile = handbook?.profile;
  const recommendations = handbook?.sample_recommendations;
  const cycle = handbook?.sample_cycle_estimate_at_temp;
  const profileOptions =
    profiles.length > 0
      ? profiles
      : [{ key: "trips", name: "Trips", experimental: false }];

  return (
    <section className="tab-content" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>Catálogo fitosanitario</h2>
        <p>
          Perfiles, objetivos y recomendaciones disponibles. El mismo motor puede
          crecer con nuevas plagas, como moscas de la fruta o arañas rojas.
        </p>
      </div>

      <div className="env-bar">
        <div className="env-title">
          <span>Perfil de detección</span>
          <span className="crop-pill">
            Cultivo: {handbook?.crop === "gulupa" ? "Gulupa" : handbook?.crop || "Gulupa"}
          </span>
        </div>
        <div className="env-controls">
          <div className="stage-select-row">
            <label htmlFor="handbookProfileSelect">Perfil</label>
            <select
              id="handbookProfileSelect"
              value={selectedProfile}
              onChange={(e) => onProfileChange && onProfileChange(e.target.value)}
            >
              {profileOptions.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.name}
                  {item.experimental ? " (experimental)" : ""}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && <div className="info-card">Cargando catálogo...</div>}
      {error && <div className="info-card">❌ {error}</div>}

      {profile && !loading && (
        <div className="recs-card">
          <div className="rec-group">
            <div className="rec-group-title">{profile.name}</div>
            <p className="card-desc">{profile.description}</p>
            {profile.experimental && (
              <p className="card-desc">
                ⚠️ Perfil experimental. Calíbralo con fotos reales en la galería antes
                de usarlo para decisiones de manejo.
              </p>
            )}
          </div>

          <div className="rec-group">
            <div className="rec-group-title">Objetivos que reconoce</div>
            <ul className="rec-list">
              {profile.targets.map((target) => (
                <li key={target.key}>
                  <b>{target.common_name}</b>
                  {target.scientific_name ? ` (${target.scientific_name})` : ""} ·{" "}
                  {KIND_LABELS[target.kind] || target.kind}
                  {target.is_positive ? " · objetivo positivo" : " · clase de rechazo"}
                  {target.description ? ` — ${target.description}` : ""}
                </li>
              ))}
            </ul>
          </div>

          <div className="rec-group">
            <div className="rec-group-title">
              Estadios biológicos
            </div>
            <ul className="rec-list">
              {profile.stages.map((stage) => (
                <li key={stage.key}>
                  <b>{stage.name}:</b> {stage.description}
                </li>
              ))}
            </ul>
          </div>

          {cycle && (
            <div className="rec-group">
              <div className="rec-group-title">Estimación térmica de ejemplo (20 °C)</div>
              <ul className="rec-list">
                <li>
                  <b>{cycle.detected_stage_name}:</b> {cycle.current_stage_duration_days}
                </li>
                <li>
                  <b>{cycle.days_to_adult}</b>
                </li>
                <li>
                  <b>Urgencia {cycle.urgency_level}:</b> {cycle.urgency_rationale}
                </li>
              </ul>
            </div>
          )}

          {recommendations && (
            <>
              <div className="rec-group">
                <div className="rec-group-title">Control biológico</div>
                <ul className="rec-list">
                  {recommendations.biological_control.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="rec-group">
                <div className="rec-group-title">Control etológico y monitoreo</div>
                <ul className="rec-list">
                  {recommendations.ethological_control.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="rec-group">
                <div className="rec-group-title">Control cultural</div>
                <ul className="rec-list">
                  {recommendations.cultural_control.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="rec-group">
                <div className="rec-group-title">Control biorracional y químico</div>
                <ul className="rec-list">
                  {recommendations.chemical_biorational_control.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="export-warning-box">
                <div>{recommendations.export_impact_alert}</div>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
