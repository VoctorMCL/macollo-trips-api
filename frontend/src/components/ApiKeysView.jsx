import React, { useState, useEffect } from "react";

export default function ApiKeysView({ onUnauthorized }) {
  const [keys, setKeys] = useState([]);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchKeys = async () => {
    try {
      const res = await fetch("/api/keys");
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setKeys(data.items || []);
      }
    } catch (err) {
      console.warn("[API Keys] Error cargando claves:", err);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);

    try {
      const res = await fetch("/api/keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim() })
      });

      if (res.status === 401) {
        onUnauthorized();
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "No se pudo crear la clave.");
      }

      const data = await res.json();
      setNewKey(data.raw_key);
      setName("");
      setCopied(false);
      await fetchKeys();
    } catch (err) {
      alert("Error creando la clave: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (keyId) => {
    if (!window.confirm("¿Revocar esta API key? La aplicación que la use perderá el acceso inmediatamente.")) {
      return;
    }

    try {
      const res = await fetch(`/api/keys/${encodeURIComponent(keyId)}`, {
        method: "DELETE"
      });

      if (res.status === 401) {
        onUnauthorized();
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "No se pudo revocar la clave.");
      }

      await fetchKeys();
    } catch (err) {
      alert("Error revocando la clave: " + err.message);
    }
  };

  const handleCopy = async () => {
    if (!newKey) return;
    try {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert("No se pudo copiar automáticamente. Por favor selecciónala y cópiala.");
    }
  };

  const formatDate = (val) => {
    if (!val) return "Nunca";
    try {
      return new Date(val).toLocaleString("es-CO", {
        dateStyle: "medium",
        timeStyle: "short"
      });
    } catch {
      return val;
    }
  };

  return (
    <section className="tab-content" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>API y accesos</h2>
        <p>Genera claves para que tus aplicaciones externas usen la API sin compartir la contraseña del panel.</p>
      </div>

      <div className="info-card">
        <div className="card-label">Nueva API key</div>
        <p className="card-desc">Cada cliente o aplicación debe usar su propia clave. Puedes revocarla cuando quieras.</p>

        <form className="inline-form" onSubmit={handleCreateKey}>
          <input
            type="text"
            placeholder="Ej. Portal Web Macollo o App Lote 3"
            maxLength={80}
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creando..." : "Crear clave"}
          </button>
        </form>

        {newKey && (
          <div className="new-key-box" style={{ display: "block", marginTop: 16 }}>
            <strong>⚠️ Guarda esta clave ahora. Por seguridad, no se volverá a mostrar:</strong>
            <div className="key-row">
              <code>{newKey}</code>
              <button type="button" className="btn-ghost" onClick={handleCopy}>
                {copied ? "Copiada" : "Copiar"}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="info-card" style={{ marginTop: 20 }}>
        <div className="card-label">Claves emitidas</div>
        <div className="items-list">
          {keys.length === 0 ? (
            <div className="card-desc">
              Todavía no hay claves generadas. Crea la primera para conectar una aplicación.
            </div>
          ) : (
            keys.map((k) => (
              <div key={k.id} className="item-row">
                <div>
                  <strong>{k.name}</strong>
                  <div className="card-desc">
                    <code>{k.key_prefix}…</code> · Creada: {formatDate(k.created_at)} · Último uso: {formatDate(k.last_used_at)}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className={`status-tag ${k.active ? "active" : "revoked"}`}>
                    {k.active ? "Activa" : "Revocada"}
                  </span>
                  {k.active && (
                    <button
                      type="button"
                      className="btn-revoke"
                      onClick={() => handleRevoke(k.id)}
                    >
                      Revocar
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="info-card" style={{ marginTop: 20 }}>
        <div className="card-label">Cómo consumir la API desde tu frontend o backend</div>
        <p className="card-desc">Envía la clave en el encabezado <code>X-API-Key</code>:</p>
        <pre className="code-block">
{`const formData = new FormData();
formData.append("file", fotoBlob, "muestra.jpg");
formData.append("temperature_c", "22.5");
formData.append("crop", "gulupa");

const res = await fetch("http://TU-SERVIDOR:8000/api/predict", {
  method: "POST",
  headers: { "X-API-Key": "mk_tu_clave_generada" },
  body: formData
});

const data = await res.json();
console.log(data);`}
        </pre>
      </div>
    </section>
  );
}
