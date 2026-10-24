import React from "react";

export default function NavigationTabs({ activeTab, onSelectTab }) {
  const tabs = [
    { id: "scoutView", label: "Inspección" },
    { id: "galleryView", label: "Galería" },
    { id: "apiView", label: "API y accesos" },
    { id: "handbookView", label: "Ficha técnica" }
  ];

  return (
    <nav className="nav-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
          onClick={() => onSelectTab(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
