/**
 * Manejo de Cámara Móvil y Herramienta de Zoom/Recorte Macro para Trips.
 */

class CameraController {
    constructor(videoElement, previewElement, zoomSlider, zoomValueLabel) {
        this.video = videoElement;
        this.preview = previewElement;
        this.zoomSlider = zoomSlider;
        this.zoomLabel = zoomValueLabel;
        
        this.currentStream = null;
        this.facingMode = "environment"; // Priorizar cámara trasera para invernadero
        this.zoomFactor = 1.0;
        this.activeBlob = null;

        this._setupZoomListener();
    }

    _setupZoomListener() {
        if (this.zoomSlider) {
            this.zoomSlider.addEventListener("input", (e) => {
                this.zoomFactor = parseFloat(e.target.value);
                if (this.zoomLabel) {
                    this.zoomLabel.textContent = `${this.zoomFactor.toFixed(1)}x`;
                }
                this.video.style.transform = `scale(${this.zoomFactor})`;
                this.preview.style.transform = `scale(${this.zoomFactor})`;
            });
        }
    }

    async startCamera() {
        this.stopCamera();
        const constraints = {
            audio: false,
            video: {
                facingMode: { ideal: this.facingMode },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };

        try {
            this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.currentStream;
            this.video.style.display = "block";
            this.preview.style.display = "none";
            document.getElementById("overlay").style.display = "flex";
            await this.video.play();
            console.log(`[Camera] Cámara iniciada con facingMode=${this.facingMode}`);
            return true;
        } catch (err) {
            console.warn("[Camera] No se pudo acceder a la cámara:", err);
            // Si el navegador bloquea getUserMedia (ej. no HTTPS o permisos), mantener fallback a input de archivo
            return false;
        }
    }

    stopCamera() {
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }
    }

    switchCamera() {
        this.facingMode = (this.facingMode === "environment") ? "user" : "environment";
        this.startCamera();
    }

    /**
     * Captura el frame actual aplicando el recorte correspondiente al zoom macro.
     * Retorna una Promesa con el Blob de la imagen optimizada.
     */
    captureFrame() {
        return new Promise((resolve, reject) => {
            if (!this.video.videoWidth || !this.video.videoHeight) {
                return reject(new Error("La cámara aún no tiene dimensiones válidas."));
            }

            const canvas = document.createElement("canvas");
            const vw = this.video.videoWidth;
            const vh = this.video.videoHeight;

            // Si hay zoom aplicado, recortamos el área central
            const cropWidth = vw / this.zoomFactor;
            const cropHeight = vh / this.zoomFactor;
            const startX = (vw - cropWidth) / 2;
            const startY = (vh - cropHeight) / 2;

            canvas.width = Math.min(cropWidth, 1080);
            canvas.height = Math.min(cropHeight, 1080);

            const ctx = canvas.getContext("2d");
            ctx.drawImage(
                this.video,
                startX, startY, cropWidth, cropHeight,
                0, 0, canvas.width, canvas.height
            );

            canvas.toBlob((blob) => {
                if (!blob) return reject(new Error("Error generando imagen desde canvas"));
                this.activeBlob = blob;
                
                // Mostrar preview visual congelado
                this.preview.src = URL.createObjectURL(blob);
                this.preview.style.display = "block";
                this.video.style.display = "none";
                document.getElementById("overlay").style.display = "none";
                
                resolve(blob);
            }, "image/jpeg", 0.92);
        });
    }

    /**
     * Muestra una imagen externa subida desde la galería del dispositivo.
     */
    loadFromFile(file) {
        return new Promise((resolve) => {
            this.stopCamera();
            this.activeBlob = file;
            this.preview.src = URL.createObjectURL(file);
            this.preview.style.display = "block";
            this.video.style.display = "none";
            document.getElementById("overlay").style.display = "none";
            resolve(file);
        });
    }
}
