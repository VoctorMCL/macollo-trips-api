import React, { useState } from "react";

export default function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.trim(),
          password
        })
      });

      if (!res.ok) {
        let msg = "Usuario o contraseña incorrectos.";
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      const data = await res.json();
      setPassword("");
      onLoginSuccess(data.username);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen" style={{ display: "flex" }}>
      <div className="login-card">
        <div className="login-brand">
          <div className="logo-badge">🌿</div>
          <div>
            <h1>Macollo Trips</h1>
            <p>Monitoreo fitosanitario de gulupa</p>
          </div>
        </div>

        <h2>Iniciar sesión</h2>
        <p className="login-hint">
          Acceso restringido al panel de administración. Las cuentas se configuran en el servidor.
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="loginUser">
            Usuario
            <input
              type="text"
              id="loginUser"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
            />
          </label>

          <label htmlFor="loginPass">
            Contraseña
            <input
              type="password"
              id="loginPass"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </label>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </button>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}
        </form>

        <p className="login-foot">¿Necesitas acceso? Contacta al administrador del servicio.</p>
      </div>
    </div>
  );
}
