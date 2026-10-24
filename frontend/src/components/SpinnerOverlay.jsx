import React from "react";

export default function SpinnerOverlay({ visible, text = "Analizando muestra..." }) {
  if (!visible) return null;

  return (
    <div className="spinner-overlay" style={{ display: "flex" }}>
      <div className="spinner"></div>
      <div className="spinner-text">{text}</div>
    </div>
  );
}
