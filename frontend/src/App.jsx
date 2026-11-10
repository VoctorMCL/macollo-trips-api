import React, { useState, useEffect, useCallback } from "react";
import LoginScreen from "./components/LoginScreen";
import Header from "./components/Header";
import NavigationTabs from "./components/NavigationTabs";
import ScoutView from "./components/ScoutView";
import GalleryView from "./components/GalleryView";
import ApiKeysView from "./components/ApiKeysView";
import HandbookView from "./components/HandbookView";
import SpinnerOverlay from "./components/SpinnerOverlay";
import { useCamera } from "./hooks/useCamera";

export default function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activeTab, setActiveTab] = useState("scoutView");
  const [temperature, setTemperature] = useState("20.0");
  const [serverStatus, setServerStatus] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState("trips");

  // Loading overlay
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("Cargando...");

  const camera = useCamera();

  const showLoading = useCallback((text = "Analizando muestra...") => {
    setLoadingText(text);
    setLoading(true);
  }, []);

  const hideLoading = useCallback(() => {
    setLoading(false);
  }, []);

  // Verificar sesión existente
  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/me");
      if (res.ok) {
        const data = await res.json();
        setUser(data.username);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setAuthChecked(true);
    }
  }, []);

  // Catálogo de perfiles (trips, moscas de la fruta, arañas rojas)
  const loadProfiles = useCallback(async () => {
    try {
      const res = await fetch("/api/profiles");
      if (!res.ok) return;
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) return;
      setProfiles(data);
      setSelectedProfile((current) => {
        if (data.some((profile) => profile.key === current)) return current;
        const serverDefault = serverStatus?.default_profile;
        if (serverDefault && data.some((profile) => profile.key === serverDefault)) {
          return serverDefault;
        }
        return data[0].key;
      });
    } catch (err) {
      console.warn("[Profiles] No se pudo cargar el catálogo:", err);
    }
  }, [serverStatus?.default_profile]);

  // Health check periódico
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        setServerStatus(data);
      } else {
        setServerStatus({ status: "error" });
      }
    } catch {
      setServerStatus({ status: "offline" });
    }
  }, []);

  useEffect(() => {
    checkAuth();
    checkHealth();
    const interval = setInterval(checkHealth, 25000);
    return () => clearInterval(interval);
  }, [checkAuth, checkHealth]);

  useEffect(() => {
    if (user) loadProfiles();
  }, [user, loadProfiles]);

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      setUser(null);
      camera.stopCamera();
    }
  };

  const handleUnauthorized = () => {
    setUser(null);
    camera.stopCamera();
  };

  if (!authChecked) {
    return (
      <SpinnerOverlay visible={true} text="Verificando sesión..." />
    );
  }

  if (!user) {
    return (
      <>
        <LoginScreen
          onLoginSuccess={(username) => {
            setUser(username);
            camera.startCamera();
          }}
        />
        <SpinnerOverlay visible={loading} text={loadingText} />
      </>
    );
  }

  return (
    <div className="app-shell">
      <Header
        username={user}
        onLogout={handleLogout}
        serverStatus={serverStatus}
      />

      <NavigationTabs
        activeTab={activeTab}
        onSelectTab={(tabId) => setActiveTab(tabId)}
      />

      <main>
        {activeTab === "scoutView" && (
          <ScoutView
            camera={camera}
            temperature={temperature}
            onTemperatureChange={setTemperature}
            profiles={profiles}
            selectedProfile={selectedProfile}
            onProfileChange={setSelectedProfile}
            showLoading={showLoading}
            hideLoading={hideLoading}
            onUnauthorized={handleUnauthorized}
          />
        )}

        {activeTab === "galleryView" && (
          <GalleryView
            profiles={profiles}
            showLoading={showLoading}
            hideLoading={hideLoading}
            onUnauthorized={handleUnauthorized}
          />
        )}

        {activeTab === "apiView" && (
          <ApiKeysView onUnauthorized={handleUnauthorized} />
        )}

        {activeTab === "handbookView" && (
          <HandbookView
            profiles={profiles}
            selectedProfile={selectedProfile}
            onProfileChange={setSelectedProfile}
          />
        )}
      </main>

      <SpinnerOverlay visible={loading} text={loadingText} />
    </div>
  );
}
