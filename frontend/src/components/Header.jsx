import React from "react";

export default function Header({ username, onLogout, serverStatus }) {
  const isHealthy = serverStatus?.status === "healthy";
  const device = serverStatus?.device ? serverStatus.device.toUpperCase() : "CPU";
  const profileCount = Array.isArray(serverStatus?.profiles)
    ? serverStatus.profiles.length
    : 0;

  return (
    <header>
      <div className="logo-group">
        <div className="logo-badge">🌿</div>
        <div className="logo-title">
          <h1>
            Macollo Visión <span className="badge-tag">API</span>
          </h1>
          <p>
            Detección de trips, moscas de la fruta y arañas rojas
            {profileCount > 0 ? ` · ${profileCount} perfiles activos` : ""}
          </p>
        </div>
      </div>

      <div className="header-status">
        <div
          className="status-pill"
          style={{
            borderColor: isHealthy ? "var(--primary-border)" : "#f2c3be",
            background: isHealthy ? "var(--primary-soft)" : "var(--danger-soft)"
          }}
        >
          <span className="pulse-dot"></span>
          <span>
            {isHealthy ? `Servicio activo (${device})` : "Sin conexión"}
          </span>
        </div>

        <span className="user-chip">{username || "admin"}</span>

        <button className="btn-ghost" type="button" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
    </header>
  );
}
