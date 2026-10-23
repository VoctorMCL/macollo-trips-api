/**
 * Gestión de API keys desde el panel autenticado.
 */

class ApiKeysUI {
    constructor() {
        this.form = document.getElementById("apiKeyForm");
        this.nameInput = document.getElementById("apiKeyName");
        this.list = document.getElementById("apiKeysList");
        this.newKeyBox = document.getElementById("newKeyBox");
        this.newKeyValue = document.getElementById("newKeyValue");
        this.copyBtn = document.getElementById("copyKeyBtn");

        this._setupListeners();
    }

    _setupListeners() {
        if (this.form) {
            this.form.addEventListener("submit", (event) => {
                event.preventDefault();
                this.createKey();
            });
        }

        if (this.copyBtn) {
            this.copyBtn.addEventListener("click", () => this.copyKey());
        }
    }

    _escape(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    _formatDate(value) {
        if (!value) return "Nunca";
        try {
            return new Date(value).toLocaleString("es-CO", {
                dateStyle: "medium",
                timeStyle: "short"
            });
        } catch (e) {
            return value;
        }
    }

    async createKey() {
        const name = this.nameInput ? this.nameInput.value.trim() : "";
        if (!name) return;

        try {
            const res = await fetch("/api/keys", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name })
            });

            if (handleUnauthorized(res)) return;

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || "No se pudo crear la clave.");
            }

            const data = await res.json();
            if (this.newKeyValue) this.newKeyValue.textContent = data.raw_key;
            if (this.newKeyBox) this.newKeyBox.hidden = false;
            if (this.nameInput) this.nameInput.value = "";

            this.refresh();
        } catch (err) {
            alert("Error creando la API key: " + err.message);
        }
    }

    async refresh() {
        if (!this.list) return;

        try {
            const res = await fetch("/api/keys");
            if (handleUnauthorized(res)) return;

            if (!res.ok) {
                this.list.textContent = "No se pudieron cargar las claves.";
                return;
            }

            const data = await res.json();
            const items = data.items || [];

            if (items.length === 0) {
                this.list.innerHTML = `<div class="card-desc">Todavía no hay claves. Crea la primera para conectar una aplicación.</div>`;
                return;
            }

            this.list.innerHTML = items.map(item => `
                <div class="item-row">
                    <div>
                        <strong>${this._escape(item.name)}</strong>
                        <div class="card-desc">
                            <code>${this._escape(item.key_prefix)}…</code> ·
                            Creada: ${this._escape(this._formatDate(item.created_at))} ·
                            Último uso: ${this._escape(this._formatDate(item.last_used_at))}
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="status-tag ${item.active ? "active" : "revoked"}">
                            ${item.active ? "Activa" : "Revocada"}
                        </span>
                        ${item.active ? `<button type="button" class="btn-revoke" data-key-id="${this._escape(item.id)}">Revocar</button>` : ""}
                    </div>
                </div>
            `).join("");

            this.list.querySelectorAll(".btn-revoke").forEach(button => {
                button.addEventListener("click", () => this.revokeKey(button.dataset.keyId));
            });
        } catch (err) {
            this.list.textContent = "No se pudieron cargar las claves.";
        }
    }

    async revokeKey(keyId) {
        if (!keyId) return;
        if (!confirm("¿Revocar esta API key? La aplicación que la use dejará de tener acceso.")) return;

        try {
            const res = await fetch(`/api/keys/${encodeURIComponent(keyId)}`, {
                method: "DELETE"
            });

            if (handleUnauthorized(res)) return;

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || "No se pudo revocar la clave.");
            }

            this.refresh();
        } catch (err) {
            alert("Error revocando la API key: " + err.message);
        }
    }

    async copyKey() {
        if (!this.newKeyValue) return;
        const text = this.newKeyValue.textContent || "";
        if (!text) return;

        try {
            await navigator.clipboard.writeText(text);
            if (this.copyBtn) {
                const original = this.copyBtn.textContent;
                this.copyBtn.textContent = "Copiada";
                setTimeout(() => { this.copyBtn.textContent = original; }, 1600);
            }
        } catch (e) {
            alert("No se pudo copiar automáticamente. Selecciona la clave y cópiala manualmente.");
        }
    }
}
