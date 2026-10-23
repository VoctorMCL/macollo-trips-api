/**
 * Gestor de Galería de Referencia (Few-Shot) para la interfaz web.
 */

class GalleryUI {
    constructor() {
        this.dropZone = document.getElementById("galleryDropZone");
        this.fileInput = document.getElementById("galleryFileInput");
        this.stageSelect = document.getElementById("galleryStageSelect");
        this.reindexBtn = document.getElementById("reindexBtn");
        this.itemsList = document.getElementById("galleryItemsList");
        
        this.statTotal = document.getElementById("statTotal");
        this.statAdulto = document.getElementById("statAdulto");
        this.statN1 = document.getElementById("statN1");
        this.statN2 = document.getElementById("statN2");
        this.statPupa = document.getElementById("statPupa");
        this.statDano = document.getElementById("statDano");

        this._setupListeners();
    }

    _setupListeners() {
        if (this.dropZone && this.fileInput) {
            this.dropZone.addEventListener("click", () => this.fileInput.click());
            
            this.dropZone.addEventListener("dragover", (e) => {
                e.preventDefault();
                this.dropZone.style.borderColor = "var(--primary)";
            });

            this.dropZone.addEventListener("dragleave", () => {
                this.dropZone.style.borderColor = "rgba(56, 189, 248, 0.4)";
            });

            this.dropZone.addEventListener("drop", (e) => {
                e.preventDefault();
                this.dropZone.style.borderColor = "rgba(56, 189, 248, 0.4)";
                if (e.dataTransfer.files.length > 0) {
                    this.uploadFile(e.dataTransfer.files[0]);
                }
            });

            this.fileInput.addEventListener("change", (e) => {
                if (e.target.files.length > 0) {
                    this.uploadFile(e.target.files[0]);
                }
            });
        }

        if (this.reindexBtn) {
            this.reindexBtn.addEventListener("click", () => this.reindexGallery());
        }
    }

    async refreshStats() {
        try {
            const res = await fetch("/api/gallery");
            if (!res.ok) return;
            const data = await res.json();
            
            if (this.statTotal) this.statTotal.textContent = data.total_images;
            if (this.statAdulto) this.statAdulto.textContent = data.by_stage.adulto || 0;
            if (this.statN1) this.statN1.textContent = data.by_stage.ninfa_1 || 0;
            if (this.statN2) this.statN2.textContent = data.by_stage.ninfa_2 || 0;
            if (this.statPupa) this.statPupa.textContent = data.by_stage.pupa || 0;
            if (this.statDano) this.statDano.textContent = data.by_stage.dano_gulupa || 0;

            this.refreshItemsList();
        } catch (err) {
            console.warn("[GalleryUI] Error obteniendo estadísticas:", err);
        }
    }

    async refreshItemsList() {
        if (!this.itemsList) return;
        try {
            const res = await fetch("/api/gallery/items");
            if (!res.ok) return;
            const items = await res.json();
            
            if (items.length === 0) {
                this.itemsList.innerHTML = `
                    <div style="text-align:center; padding: 16px; color: var(--text-muted);">
                        No hay fotos de referencia indexadas todavía.<br>
                        Puedes copiar fotos a <code>data/reference_gallery/</code> o subirlas arriba.
                    </div>`;
                return;
            }

            this.itemsList.innerHTML = items.map(it => `
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <span><b>[${it.stage}]</b> ${it.filename}</span>
                    <span style="color:var(--text-muted); font-size: 0.75rem;">${(it.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
            `).join("");
        } catch (err) {
            console.warn("[GalleryUI] Error listando items:", err);
        }
    }

    async uploadFile(file) {
        const stage = this.stageSelect ? this.stageSelect.value : "adulto";
        const formData = new FormData();
        formData.append("file", file);
        formData.append("stage", stage);

        showLoading(`Indexando foto en BioCLIP 2.5 (Estadio: ${stage})...`);
        try {
            const res = await fetch("/api/gallery/upload", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const err = await res.text();
                throw new Error(err);
            }

            const data = await res.json();
            alert(`✅ ${data.message} Total indexadas: ${data.total_indexed_images}`);
            this.refreshStats();
        } catch (err) {
            alert("❌ Error subiendo foto a la galería: " + err.message);
        } finally {
            hideLoading();
            if (this.fileInput) this.fileInput.value = "";
        }
    }

    async reindexGallery() {
        showLoading("Reescaneando directorio local y recalculando vectores BioCLIP...");
        try {
            const res = await fetch("/api/gallery/reindex", { method: "POST" });
            if (!res.ok) throw new Error("Error en reindexación");
            const data = await res.json();
            alert(`✅ ${data.message} ${data.indexed_images} imágenes indexadas.`);
            this.refreshStats();
        } catch (err) {
            alert("❌ Error reindexando galería: " + err.message);
        } finally {
            hideLoading();
        }
    }
}
