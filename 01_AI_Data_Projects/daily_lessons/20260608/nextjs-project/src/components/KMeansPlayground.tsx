"use client";

import React, { useRef, useState, useEffect } from "react";
import { Play, RotateCcw, FastForward, HelpCircle } from "lucide-react";

interface Point {
  x: number;
  y: number;
  cluster: number; // -1 means unassigned
}

interface Centroid {
  x: number;
  y: number;
  color: string;
}

export default function KMeansPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([
    // Seed points for initial good layout
    { x: 120, y: 100, cluster: -1 },
    { x: 140, y: 120, cluster: -1 },
    { x: 110, y: 150, cluster: -1 },
    { x: 160, y: 130, cluster: -1 },
    { x: 380, y: 220, cluster: -1 },
    { x: 390, y: 250, cluster: -1 },
    { x: 360, y: 230, cluster: -1 },
    { x: 410, y: 210, cluster: -1 },
    { x: 250, y: 280, cluster: -1 },
    { x: 230, y: 290, cluster: -1 },
    { x: 270, y: 270, cluster: -1 },
  ]);
  const [centroids, setCentroids] = useState<Centroid[]>([]);
  const [kValue, setKValue] = useState<number>(3);
  const [step, setStep] = useState<number>(0);
  const [converged, setConverged] = useState<boolean>(false);

  const colors = ["#ef4444", "#3b82f6", "#10b981", "#eab308", "#ec4899"]; // red, blue, green, yellow, pink

  const initializeCentroids = () => {
    if (points.length === 0) return;
    const newCentroids: Centroid[] = [];
    for (let i = 0; i < kValue; i++) {
      // Pick a random point's coordinates as the initial centroid
      const randomIdx = Math.floor(Math.random() * points.length);
      newCentroids.push({
        x: points[randomIdx].x + (Math.random() - 0.5) * 20, // add minor jitter
        y: points[randomIdx].y + (Math.random() - 0.5) * 20,
        color: colors[i],
      });
    }
    setCentroids(newCentroids);
    setPoints(points.map((p) => ({ ...p, cluster: -1 })));
    setStep(0);
    setConverged(false);
  };

  const getDistance = (p1: { x: number; y: number }, p2: { x: number; y: number }) => {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
  };

  const runKMeansStep = () => {
    if (centroids.length === 0) {
      initializeCentroids();
      return;
    }

    // Step 1: Assign points to nearest centroid
    const newPoints = points.map((p) => {
      let minDist = Infinity;
      let nearestCluster = -1;
      centroids.forEach((c, idx) => {
        const d = getDistance(p, c);
        if (d < minDist) {
          minDist = d;
          nearestCluster = idx;
        }
      });
      return { ...p, cluster: nearestCluster };
    });

    // Step 2: Recalculate centroids
    let changed = false;
    const newCentroids = centroids.map((c, idx) => {
      const clusterPoints = newPoints.filter((p) => p.cluster === idx);
      if (clusterPoints.length === 0) return c; // no change if no points

      const sumX = clusterPoints.reduce((sum, p) => sum + p.x, 0);
      const sumY = clusterPoints.reduce((sum, p) => sum + p.y, 0);
      const avgX = sumX / clusterPoints.length;
      const avgY = sumY / clusterPoints.length;

      // Check if centroid moved significantly
      if (Math.abs(c.x - avgX) > 0.5 || Math.abs(c.y - avgY) > 0.5) {
        changed = true;
      }

      return { ...c, x: avgX, y: avgY };
    });

    setPoints(newPoints);
    setCentroids(newCentroids);
    setStep(step + 1);

    if (!changed && step > 0) {
      setConverged(true);
    }
  };

  const runToConvergence = () => {
    if (centroids.length === 0) {
      initializeCentroids();
    }
    
    // We run the loop up to 50 times synchronously or until converged
    let currentPoints = [...points];
    let currentCentroids = [...centroids];
    
    if (currentCentroids.length === 0) {
      // Initialize first
      const newCentroids: Centroid[] = [];
      for (let i = 0; i < kValue; i++) {
        const randomIdx = Math.floor(Math.random() * points.length);
        newCentroids.push({
          x: points[randomIdx].x + (Math.random() - 0.5) * 20,
          y: points[randomIdx].y + (Math.random() - 0.5) * 20,
          color: colors[i],
        });
      }
      currentCentroids = newCentroids;
    }

    let iterationsCount = 0;
    let changed = true;

    while (changed && iterationsCount < 50) {
      // Assign points
      currentPoints = currentPoints.map((p) => {
        let minDist = Infinity;
        let nearestCluster = -1;
        currentCentroids.forEach((c, idx) => {
          const d = getDistance(p, c);
          if (d < minDist) {
            minDist = d;
            nearestCluster = idx;
          }
        });
        return { ...p, cluster: nearestCluster };
      });

      // Recalculate centroids
      changed = false;
      currentCentroids = currentCentroids.map((c, idx) => {
        const clusterPoints = currentPoints.filter((p) => p.cluster === idx);
        if (clusterPoints.length === 0) return c;

        const sumX = clusterPoints.reduce((sum, p) => sum + p.x, 0);
        const sumY = clusterPoints.reduce((sum, p) => sum + p.y, 0);
        const avgX = sumX / clusterPoints.length;
        const avgY = sumY / clusterPoints.length;

        if (Math.abs(c.x - avgX) > 0.5 || Math.abs(c.y - avgY) > 0.5) {
          changed = true;
        }

        return { ...c, x: avgX, y: avgY };
      });

      iterationsCount++;
    }

    setPoints(currentPoints);
    setCentroids(currentCentroids);
    setStep(step + iterationsCount);
    setConverged(true);
  };

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = "#1e293b"; // slate-800
    ctx.lineWidth = 1;
    for (let x = 40; x < width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 40; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw assignment links
    points.forEach((p) => {
      if (p.cluster !== -1 && centroids[p.cluster]) {
        const c = centroids[p.cluster];
        ctx.strokeStyle = c.color + "33"; // Hex color with 20% alpha
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(c.x, c.y);
        ctx.stroke();
      }
    });

    // Draw points
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = p.cluster !== -1 ? centroids[p.cluster].color : "#cbd5e1"; // slate-300
      ctx.shadowColor = p.cluster !== -1 ? centroids[p.cluster].color : "#cbd5e1";
      ctx.shadowBlur = p.cluster !== -1 ? 4 : 0;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Draw centroids (rendered as prominent cross/star shapes)
    centroids.forEach((c) => {
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2.5;
      ctx.fillStyle = c.color;
      ctx.shadowColor = c.color;
      ctx.shadowBlur = 10;

      // Draw diamond / star shape
      ctx.beginPath();
      ctx.moveTo(c.x, c.y - 12);
      ctx.lineTo(c.x + 8, c.y);
      ctx.lineTo(c.x, c.y + 12);
      ctx.lineTo(c.x - 8, c.y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Outer rings
      ctx.strokeStyle = c.color + "99"; // with alpha
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(c.x, c.y, 18, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
    });
  };

  useEffect(() => {
    drawCanvas();
  }, [points, centroids]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setPoints([...points, { x, y, cluster: -1 }]);
    setConverged(false);
  };

  const handleReset = () => {
    setPoints([]);
    setCentroids([]);
    setStep(0);
    setConverged(false);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            🧲 K-Means 自主分群互動式沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            點擊畫布放置資料點，選擇 K 值並點擊「單步迭代」或「一鍵收斂」觀察群心移動。
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
        >
          <RotateCcw size={14} /> 重設點
        </button>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-4 bg-slate-950 border border-slate-800/80 p-3 rounded-xl">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300">設定分群數 K: {kValue}</label>
          <input
            type="range"
            min="2"
            max="5"
            value={kValue}
            onChange={(e) => {
              setKValue(parseInt(e.target.value));
              setCentroids([]);
              setConverged(false);
              setStep(0);
            }}
            className="w-24 h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
        </div>

        <div className="flex gap-2 w-full sm:w-auto justify-end">
          <button
            onClick={initializeCentroids}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-xs font-bold transition flex items-center gap-1"
          >
            🎲 隨機中心
          </button>
          <button
            onClick={runKMeansStep}
            disabled={points.length === 0 || converged}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-lg shadow-emerald-950/20"
          >
            <Play size={12} /> 單步迭代
          </button>
          <button
            onClick={runToConvergence}
            disabled={points.length === 0 || converged}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-lg shadow-blue-950/20"
          >
            <FastForward size={12} /> 一鍵收斂
          </button>
        </div>
      </div>

      <div className="relative border border-slate-700 rounded-xl overflow-hidden bg-slate-950 flex justify-center">
        <canvas
          ref={canvasRef}
          width={500}
          height={320}
          onClick={handleCanvasClick}
          className="cursor-crosshair w-full block max-w-full bg-slate-950"
        />
        {points.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-slate-950/60 backdrop-blur-[1px]">
            <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
              <HelpCircle size={16} className="text-blue-400" /> 請先點擊放置一些資料樣本點，然後點擊「🎲 隨機中心」
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 text-center">
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">目前迭代次數</span>
          <span className="text-emerald-400 font-mono font-bold text-base block mt-1">
            第 {step} 次
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">演算法狀態</span>
          <span className={`font-mono font-bold text-base block mt-1 ${converged ? "text-blue-400" : "text-amber-500"}`}>
            {converged ? "已收斂 (Converged)" : "迭代中..."}
          </span>
        </div>
      </div>
    </div>
  );
}
