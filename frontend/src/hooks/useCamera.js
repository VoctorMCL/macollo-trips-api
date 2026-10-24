import { useState, useRef, useEffect, useCallback } from "react";

export function useCamera() {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState("environment");
  const [zoomFactor, setZoomFactor] = useState(1.0);
  const [previewSrc, setPreviewSrc] = useState(null);
  const [activeBlob, setActiveBlob] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);

  const stopCamera = useCallback(() => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setStream(null);
    setCameraActive(false);
  }, []);

  const startCamera = useCallback(
    async (mode = facingMode) => {
      stopCamera();
      setPreviewSrc(null);
      setActiveBlob(null);

      const constraints = {
        audio: false,
        video: {
          facingMode: { ideal: mode },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          await videoRef.current.play();
        }
        setStream(mediaStream);
        setCameraActive(true);
        return true;
      } catch (err) {
        console.warn("[Camera Hook] No se pudo acceder a la cámara:", err);
        setCameraActive(false);
        return false;
      }
    },
    [facingMode, stopCamera]
  );

  const switchCamera = useCallback(() => {
    const nextMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(nextMode);
    startCamera(nextMode);
  }, [facingMode, startCamera]);

  const captureFrame = useCallback(() => {
    return new Promise((resolve, reject) => {
      const video = videoRef.current;
      if (!video || !video.videoWidth || !video.videoHeight) {
        return reject(new Error("La cámara aún no tiene dimensiones válidas."));
      }

      const vw = video.videoWidth;
      const vh = video.videoHeight;

      // Recorte central proporcional al factor de zoom
      const cropWidth = vw / zoomFactor;
      const cropHeight = vh / zoomFactor;
      const startX = (vw - cropWidth) / 2;
      const startY = (vh - cropHeight) / 2;

      const canvas = document.createElement("canvas");
      canvas.width = Math.min(cropWidth, 1080);
      canvas.height = Math.min(cropHeight, 1080);

      const ctx = canvas.getContext("2d");
      ctx.drawImage(
        video,
        startX,
        startY,
        cropWidth,
        cropHeight,
        0,
        0,
        canvas.width,
        canvas.height
      );

      canvas.toBlob(
        (blob) => {
          if (!blob) return reject(new Error("Error generando imagen desde canvas"));
          setActiveBlob(blob);
          const url = URL.createObjectURL(blob);
          setPreviewSrc(url);
          resolve(blob);
        },
        "image/jpeg",
        0.92
      );
    });
  }, [zoomFactor]);

  const loadFromFile = useCallback(
    (file) => {
      return new Promise((resolve) => {
        stopCamera();
        setActiveBlob(file);
        const url = URL.createObjectURL(file);
        setPreviewSrc(url);
        resolve(file);
      });
    },
    [stopCamera]
  );

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  return {
    videoRef,
    cameraActive,
    previewSrc,
    activeBlob,
    zoomFactor,
    setZoomFactor,
    startCamera,
    stopCamera,
    switchCamera,
    captureFrame,
    loadFromFile
  };
}
