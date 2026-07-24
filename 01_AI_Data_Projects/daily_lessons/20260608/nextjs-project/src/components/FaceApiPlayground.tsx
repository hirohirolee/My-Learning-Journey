"use client";

import React, { useRef, useState, useEffect } from "react";
import { Camera, CameraOff, Loader2 } from "lucide-react";

export default function FaceApiPlayground() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [faceapi, setFaceapi] = useState<any>(null);
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [currentEmotion, setCurrentEmotion] = useState<string>("等待偵測...");
  const [emotionScore, setEmotionScore] = useState<number>(0);
  const [expressions, setExpressions] = useState<{ [key: string]: number }>({
    neutral: 1,
    happy: 0,
    sad: 0,
    angry: 0,
    fearful: 0,
    disgusted: 0,
    surprised: 0,
  });

  // Safe client-side dynamic import of face-api
  useEffect(() => {
    import("@vladmandic/face-api").then((mod) => {
      setFaceapi(mod);
    }).catch(err => {
      console.error("Failed to load face-api module", err);
      setErrorMsg("載入 Face API 套件失敗");
    });

    // Cleanup video stream on unmount
    return () => {
      stopVideo();
    };
  }, []);

  const stopVideo = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      const tracks = stream.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const startVideo = async () => {
    if (!faceapi) return;
    try {
      setLoading(true);
      setErrorMsg("");

      // Load models
      await faceapi.nets.tinyFaceDetector.loadFromUri("/models");
      await faceapi.nets.faceLandmark68Net.loadFromUri("/models");
      await faceapi.nets.faceExpressionNet.loadFromUri("/models");

      // Request camera
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, frameRate: { ideal: 15 } },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      setCameraActive(true);
      setLoading(false);
    } catch (err: any) {
      console.error("Error starting camera or loading models:", err);
      setLoading(false);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setErrorMsg("相機權限被拒絕，請開啟權限後再試。");
      } else {
        setErrorMsg("無法啟動相機，請確認設備已正確連接。");
      }
    }
  };

  useEffect(() => {
    let checkInterval: any;

    if (cameraActive && faceapi && videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const displaySize = { width: 320, height: 240 };
      faceapi.matchDimensions(canvas, displaySize);

      const runDetection = async () => {
        if (video.paused || video.ended || !cameraActive) return;

        try {
          const detection = await faceapi
            .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 160, scoreThreshold: 0.5 }))
            .withFaceLandmarks()
            .withFaceExpressions();

          if (detection && canvasRef.current) {
            const ctx = canvas.getContext("2d");
            if (ctx) {
              ctx.clearRect(0, 0, canvas.width, canvas.height);
            }

            const resizedDetections = faceapi.resizeResults(detection, displaySize);

            // Draw bounding boxes & landmarks on canvas overlay
            faceapi.draw.drawDetections(canvas, resizedDetections);
            faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

            // Calculate dominant expression
            const exprs = detection.expressions;
            setExpressions({ ...exprs });

            let maxEmotion = "neutral";
            let maxVal = 0;
            Object.keys(exprs).forEach((key) => {
              if (exprs[key] > maxVal) {
                maxVal = exprs[key];
                maxEmotion = key;
              }
            });

            const emotionMap: { [key: string]: string } = {
              neutral: "平常心 / 專注 😐",
              happy: "開心 / 獲得靈感 😊",
              sad: "困惑 / 思考中 😟",
              angry: "有挫折感 / 生氣 😡",
              fearful: "擔憂 😨",
              disgusted: "反感 🤢",
              surprised: "驚奇 / 恍然大悟 😮",
            };

            setCurrentEmotion(emotionMap[maxEmotion] || maxEmotion);
            setEmotionScore(maxVal);

            // Dispatch custom event to notify AI Assistant
            const emotionEvent = new CustomEvent("faceapi-emotion", {
              detail: { emotion: maxEmotion, score: maxVal, expressions: exprs },
            });
            window.dispatchEvent(emotionEvent);
          }
        } catch (e) {
          console.error("Detection error:", e);
        }
      };

      // Poll predictions every 150ms to keep CPU load low
      checkInterval = setInterval(runDetection, 150);
    }

    return () => {
      if (checkInterval) clearInterval(checkInterval);
    };
  }, [cameraActive, faceapi]);

  const emotionList = [
    { key: "neutral", label: "專注 / 平常心", color: "bg-slate-400" },
    { key: "happy", label: "滿意 / 開心", color: "bg-emerald-500" },
    { key: "sad", label: "困惑 / 思考", color: "bg-blue-500" },
    { key: "surprised", label: "驚訝 / 頓悟", color: "bg-amber-500" },
    { key: "angry", label: "挫折 / 緊繃", color: "bg-rose-500" },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            🧠 AI 視覺相機室 (Face API 現場示範)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            利用卷積神經網路 (CNN) 於瀏覽器即時定位 68 個臉部標記並辨識情緒表情。
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
        {/* Video stream box */}
        <div className="md:col-span-6 flex flex-col items-center">
          <div className="relative w-[320px] h-[240px] border border-slate-700 bg-slate-950 rounded-xl overflow-hidden shadow-2xl">
            <video
              ref={videoRef}
              width={320}
              height={240}
              muted
              playsInline
              className="absolute inset-0 object-cover scale-x-[-1]"
            />
            <canvas
              ref={canvasRef}
              width={320}
              height={240}
              className="absolute inset-0 pointer-events-none scale-x-[-1]"
            />

            {!cameraActive && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-slate-950/90 text-center">
                {loading ? (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="animate-spin text-emerald-400" size={32} />
                    <p className="text-slate-300 text-sm font-medium">正在載入深度學習模型與相機...</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <CameraOff className="text-slate-500" size={40} />
                    {errorMsg ? (
                      <p className="text-rose-400 text-xs px-2 font-medium">{errorMsg}</p>
                    ) : (
                      <p className="text-slate-400 text-xs">開啟相機體驗情緒感知的「動態適應學習模式」</p>
                    )}
                    <button
                      onClick={startVideo}
                      disabled={!faceapi}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold rounded-xl flex items-center gap-1.5 transition mt-2 shadow-lg shadow-emerald-950/30"
                    >
                      <Camera size={14} /> 開啟 AI 視訊鏡頭
                    </button>
                  </div>
                )}
              </div>
            )}

            {cameraActive && (
              <button
                onClick={stopVideo}
                className="absolute bottom-3 right-3 px-2.5 py-1.5 bg-slate-950/80 backdrop-blur-sm hover:bg-slate-900 border border-slate-800 text-slate-300 text-[10px] font-bold rounded-lg transition"
              >
                關閉相機
              </button>
            )}
          </div>
        </div>

        {/* Emotion probability dashboard */}
        <div className="md:col-span-6 space-y-4">
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3.5">
            <span className="text-slate-500 text-xs block uppercase tracking-wider">偵測表情表情</span>
            <span className="text-emerald-400 font-bold text-base block mt-1">
              {cameraActive ? `${currentEmotion} (${(emotionScore * 100).toFixed(0)}%)` : "相機未開啟"}
            </span>
          </div>

          <div className="space-y-2.5">
            {emotionList.map((e) => {
              const val = expressions[e.key] || 0;
              return (
                <div key={e.key} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">{e.label}</span>
                    <span className="text-slate-500 font-mono">{(val * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-850 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${e.color} transition-all duration-150 rounded-full`}
                      style={{ width: `${val * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
