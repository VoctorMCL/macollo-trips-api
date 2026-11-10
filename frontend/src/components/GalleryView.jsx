import React, { useState, useEffect, useRef } from "react";

const LEGACY_LABELS = [
  { key: "huevo", profile: "trips", target: "trips_general", stage: "huevo", display_name: "Trips · Huevo" },
  { key: "larva", profile: "trips", target: "trips_general", stage: "larva", display_name: "Trips · Larva (Ninfa)" },
  { key: "pupa", profile: "trips", target: "trips_general", stage: "pupa", display_name: "Trips · Pupa" },
  { key: "adulto", profile: "trips", target: "trips_general", stage: "adulto", display_name: "Trips · Adulto" },
  { key: "dano_gulupa", profile: "trips", target: "trips_general", stage: "dano_gulupa", display_name: "Trips · Daño / Roña" }
];

export default function GalleryView({ profiles = [], showLoading, hideLoading, onUnauthorized }) {
  const [stats, setStats] = useState({
    total_images: 0,
    by_label: {},
    by_stage: {}
  });
  const [items, setItems] = useState([]);
  const [labels, setLabels] = useState(LEGACY_LABELS);
  const [selectedProfile, setSelectedProfile] = useState("trips");
  const [selectedLabel, setSelectedLabel] = useState("larva");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const fetchStats = async () => {
    try {
      const res = await fetch("/api/gallery");
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.warn("[Gallery] Error cargando stats:", err);
    }
  };

  const fetchItems = async () => {
    try {
      const res = await fetch("/api/gallery/items");
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setItems(data);
      }
    } catch (err) {
      console.warn("[Gallery] Error cargando items:", err);
    }
  };

  const fetchLabels = async () => {
    try {
      const res = await fetch("/api/gallery/labels");
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.items) && data.items.length > 0) {
          setLabels(data.items);
        }
      }
    } catch (err) {
      console.warn("[Gallery] Error cargando etiquetas:", err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchItems();
    fetchLabels();
  }, []);

  const profileLabels = labels.filter((label) => label.profile === selectedProfile);

  useEffect(() => {
    if (profileLabels.length > 0 && !profileLabels.some((label) => label.key === selectedLabel)) {
      setSelectedLabel(profileLabels[0].key);
    }
  }, [labels, selectedProfile]);

  const handleProfileChange = (profileKey) => {
    setSelectedProfile(profileKey);
    const firstLabel = labels.find((label) => label.profile === profileKey);
    if (firstLabel) setSelectedLabel(firstLabel.key);
  };

  const handleUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("label", selectedLabel);

    showLoading(`Indexando foto en BioCLIP 2.5 (${selectedLabel})...`);
    try {
      const res = await fetch("/api/gallery/upload", {
        method: "POST",
        body: formData
      });

      if (res.status === 401) {
        onUnauthorized();
        return;
      }

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText);
      }

      const data = await res.json();
      alert(`✅ ${data.message} Total indexadas: ${data.total_indexed_images}`);
      await fetchStats();
      await fetchItems();
    } catch (err) {
      alert("❌ Error subiendo foto a la galería: " + err.message);
    } finally {
      hideLoading();
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleReindex = async () => {
    showLoading("Reescaneando directorios y recalculando vectores BioCLIP...");
    try {
      const res = await fetch("/api/gallery/reindex", { method: "POST" });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) throw new Error("Error en reindexación");
      const data = await res.json();
      alert(`✅ ${data.message} ${data.indexed_images} imágenes indexadas.`);
      await fetchStats();
      await fetchItems();
    } catch (err) {
      alert("❌ Error reindexando galería: " + err.message);
    } finally {
      hideLoading();
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const profileOptions =
    profiles.length > 0
      ? profiles
      : [{ key: "trips", name: "Trips", experimental: false }];

  return (
    <section className="tab-content gallery-section" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>Galería de referencia</h2>
        <p>
          Estas fotos se indexan en el servidor para enriquecer la comparación
          empírica de la API. Puedes tener fotos por perfil, objetivo y estadio.
        </p>
      </div>

      <div className="env-bar">
        <div className="env-title">
          <span>Memoria de campo (few-shot)</span>
          <span className="crop-pill">
            {stats.is_stale ? "Índice desactualizado" : "Índice al día"}
          </span>
        </div>
        <button
          className="btn-primary btn-small"
          type="button"
          onClick={handleReindex}
        >
          Reindexar fotos
        </button>
      </div>

      <div className="gallery-stats-grid">
        <div className="stat-pill">
          <div className="num">{stats.total_images || 0}</div>
          <div className="lbl">Total</div>
        </div>
        {profileLabels.map((label) => (
          <div className="stat-pill" key={label.key} title={label.display_name}>
            <div className="num">
              {stats.by_label?.[label.key] ?? stats.by_stage?.[label.key] ?? 0}
            </div>
            <div className="lbl">{label.stage || label.display_name}</div>
          </div>
        ))}
      </div>

      <div className="info-card">
        <div className="card-label">Agregar una foto</div>
        <p className="card-desc" style={{ marginBottom: 14 }}>
          Sube fotos reales tomadas en el invernadero. El modelo extrae su vector
          de características y lo usa para comparar nuevas fotos.
        </p>

        <div className="stage-select-row">
          <label htmlFor="galleryProfileSelect">Perfil:</label>
          <select
            id="galleryProfileSelect"
            value={selectedProfile}
            onChange={(e) => handleProfileChange(e.target.value)}
          >
            {profileOptions.map((profile) => (
              <option key={profile.key} value={profile.key}>
                {profile.name}
                {profile.experimental ? " (experimental)" : ""}
              </option>
            ))}
          </select>

          <label htmlFor="galleryLabelSelect">Carpeta:</label>
          <select
            id="galleryLabelSelect"
            value={selectedLabel}
            onChange={(e) => setSelectedLabel(e.target.value)}
          >
            {profileLabels.map((label) => (
              <option key={label.key} value={label.key}>
                {label.display_name}
              </option>
            ))}
          </select>
        </div>

        <div
          className="upload-zone"
          style={{
            borderColor: dragOver ? "var(--primary)" : "rgba(56, 189, 248, 0.4)"
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
        >
          <strong>Haz clic o arrastra una foto aquí</strong>
          <p>Formatos JPG, PNG o WebP · Máximo 15 MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleUpload(e.target.files[0]);
              }
            }}
          />
        </div>
      </div>

      <div className="info-card" style={{ marginTop: 20 }}>
        <div className="card-label">Fotos almacenadas en el servidor</div>
        <div className="items-list">
          {items.length === 0 ? (
            <div style={{ textAlign: "center", padding: 16, color: "var(--text-muted)" }}>
              No hay fotos de referencia indexadas todavía.
              <br />
              Puedes copiar fotos a <code>data/reference_gallery/</code> o subirlas arriba.
            </div>
          ) : (
            items.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "6px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)"
                }}
              >
                <span>
                  <b>[{item.display_name || item.stage}]</b> {item.filename}
                </span>
                <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                  {(item.file_size_bytes / 1024).toFixed(1)} KB
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
