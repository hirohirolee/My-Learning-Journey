"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface ClassPoint {
  x: number;
  y: number;
  label: number; // 0 or 1
}

export default function NaiveBayesPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<ClassPoint[]>([
    { x: 120, y: 100, label: 0 },
    { x: 150, y: 160, label: 0 },
    { x: 100, y: 220, label: 0 },
    { x: 380, y: 100, label: 1 },
    { x: 350, y: 180, label: 1 },
    { x: 400, y: 250, label: 1 }
  ]);
  const [currentLabel, setCurrentLabel] = useState<number>(1);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    if (points.length >= 2) {
      const c0 = points.filter((p) => p.label === 0);
      const c1 = points.filter((p) => p.label === 1);

      const getStats = (arr: ClassPoint[]) => {
        if (arr.length === 0) return { meanX: 0, meanY: 0, varX: 1, varY: 1 };
        const sumX = arr.reduce((acc, p) => acc + p.x, 0);
        const sumY = arr.reduce((acc, p) => acc + p.y, 0);
        const mx = sumX / arr.length;
        const my = sumY / arr.length;
        let vx = arr.reduce((acc, p) => acc + Math.pow(p.x - mx, 2), 0) / arr.length;
        let vy = arr.reduce((acc, p) => acc + Math.pow(p.y - my, 2), 0) / arr.length;
        vx = Math.max(100, vx); // prevent variance too close to 0
        vy = Math.max(100, vy);
        return { meanX: mx, meanY: my, varX: vx, varY: vy };
      };

      const stats0 = getStats(c0);
      const stats1 = getStats(c1);

      const p0_prior = c0.length / points.length;
      const p1_prior = 1 - p0_prior;

      const getGaussianPdf = (val: number, mean: number, variance: number) => {
        return (
          (1 / Math.sqrt(2 * Math.PI * variance)) *
          Math.exp(-Math.pow(val - mean, 2) / (2 * variance))
        );
      };

      // Shading background probability field
      const step = 5;
      for (let x = 0; x < width; x += step) {
        for (let y = 0; y < height; y += step) {
          let score0 = p0_prior;
          let score1 = p1_prior;

          if (c0.length > 0) {
            score0 *=
              getGaussianPdf(x, stats0.meanX, stats0.varX) *
              getGaussianPdf(y, stats0.meanY, stats0.varY);
          } else {
            score0 = 0;
          }

          if (c1.length > 0) {
            score1 *=
              getGaussianPdf(x, stats1.meanX, stats1.varX) *
              getGaussianPdf(y, stats1.meanY, stats1.varY);
          } else {
            score1 = 0;
          }

          const total = score0 + score1;
          const prob1 = total > 0 ? score1 / total : 0.5;

          ctx.fillStyle = `rgba(${Math.floor(168 * prob1 + 249 * (1 - prob1))}, ${Math.floor(
            85 * prob1 + 115 * (1 - prob1)
          )}, ${Math.floor(247 * prob1 + 22 * (1 - prob1))}, 0.10)`;
          ctx.fillRect(x, y, step, step);
        }
      }
    }

    // Grid lines
    ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
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

    // Draw points
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      if (p.label === 1) {
        ctx.fillStyle = "#a855f7";
        ctx.shadowColor = "#a855f7";
      } else {
        ctx.fillStyle = "#f97316";
        ctx.shadowColor = "#f97316";
      }
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    });
  };

  useEffect(() => {
    drawCanvas();
  }, [points]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    setPoints([...points, { x, y, label: currentLabel }]);
  };

  const handleReset = () => {
    setPoints([]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            ✉️ 單純貝氏高斯機率場沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            放置資料點。系統將利用獨立的高斯常態分佈，擬合出非線性的貝氏機率密度劃分圖。
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
        >
          <Trash2 size={14} /> 清空點
        </button>
      </div>

      <div className="flex items-center justify-center gap-6 mb-4">
        <label className="text-xs font-semibold text-slate-300">選擇類別：</label>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setCurrentLabel(0)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 border ${
              currentLabel === 0
                ? "bg-orange-500/20 text-orange-400 border-orange-500"
                : "bg-slate-850 text-slate-400 border-transparent hover:bg-slate-800"
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span> 類別 0 (橘色)
          </button>
          <button
            onClick={() => setCurrentLabel(1)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 border ${
              currentLabel === 1
                ? "bg-purple-500/20 text-purple-400 border-purple-500"
                : "bg-slate-850 text-slate-400 border-transparent hover:bg-slate-800"
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> 類別 1 (紫色)
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
        {points.length < 2 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-slate-950/60 backdrop-blur-[1px]">
            <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
              <HelpCircle size={16} className="text-blue-400" /> 請在畫布兩側點擊，放置兩種不同顏色類別的點
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 text-center">
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">模型特徵分佈</span>
          <span className="text-emerald-400 font-mono font-bold text-sm block mt-1">
            高斯獨立機率 (Gaussian)
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">條件獨立性假設</span>
          <span className="text-blue-400 font-mono font-bold text-sm block mt-1">
            P(X,Y|C) = P(X|C)P(Y|C)
          </span>
        </div>
      </div>
    </div>
  );
}
