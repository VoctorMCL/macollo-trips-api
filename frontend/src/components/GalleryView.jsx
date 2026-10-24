import React, { useState, useEffect, useRef } from "react";

export default function GalleryView({ showLoading, hideLoading, onUnauthorized }) {
  const [stats, setStats] = useState({
    total_images: 0,
    by_stage: { huevo: 0, larva: 0, pupa: 0, adulto: 0, dano_gulupa: 0 }
  });
  const [items, setItems] = useState([]);
  const [selectedStage, setSelectedStage] = useState("larva");
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

  useEffect(() => {
    fetchStats();
    fetchItems();
  }, []);

  const handleUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("stage", selectedStage);

    showLoading(`Indexando foto en BioCLIP 2.5 (Estadio: ${selectedStage})...`);
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
    showLoading("Reescaneando directorio local y recalculando vectores BioCLIP...");
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

  return (
    <section className="tab-content gallery-section" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>Galería de referencia</h2>
        <p>Estas fotos se indexan en el servidor para enriquecer la comparación empírica de la API.</p>
      </div>

      <div className="env-bar">
        <div className="env-title">
          <span>Memoria de campo (few-shot)</span>
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
        <div className="stat-pill">
          <div className="num">{stats.by_stage?.huevo || 0}</div>
          <div className="lbl">Huevos</div>
        </div>
        <div className="stat-pill">
          <div className="num">{stats.by_stage?.larva || 0}</div>
          <div className="lbl">Larvas / Ninfas</div>
        </div>
        <div className="stat-pill">
          <div className="num">{stats.by_stage?.pupa || 0}</div>
          <div className="lbl">Pupas</div>
        </div>
        <div className="stat-pill">
          <div className="num">{stats.by_stage?.adulto || 0}</div>
          <div className="lbl">Adultos</div>
        </div>
        <div className="stat-pill">
          <div className="num">{stats.by_stage?.dano_gulupa || 0}</div>
          <div className="lbl">Daño / Roña</div>
        </div>
      </div>

      <div className="info-card">
        <div className="card-label">Agregar una foto</div>
        <p className="card-desc" style={{ marginBottom: 14 }}>
          Sube fotos reales de trips o daños tomadas en el invernadero. El modelo extrae su vector de características y lo usa para comparar nuevas fotos.
        </p>

        <div className="stage-select-row">
          <label htmlFor="galleryStageSelect">Fase:</label>
          <select
            id="galleryStageSelect"
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
          >
            <option value="huevo">Huevo</option>
            <option value="larva">Larva (Ninfa)</option>
            <option value="pupa">Pupa</option>
            <option value="adulto">Adulto</option>
            <option value="dano_gulupa">Daño / Roña</option>
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
          <p>Formatos JPG, PNG o WebP</p>
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
                  <b>[{item.stage}]</b> {item.filename}
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
