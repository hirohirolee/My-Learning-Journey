"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface ClassPoint {
  x: number;
  y: number;
  label: number; // 0 (Orange) or 1 (Purple)
}

export default function SVMPlayground() {
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
  const [margin, setMargin] = useState<number>(0);
  const [svCount, setSvCount] = useState<number>(0);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    let w0 = 0, w1 = 0, b = 0;
    const scaleX = width / 2;
    const scaleY = height / 2;
    let numSVs = 0;
    let svmMargin = 0;

    if (points.length >= 2) {
      const mathPts = points.map((p) => ({
        x: (p.x - width / 2) / scaleX,
        y: (height / 2 - p.y) / scaleY,
        label: p.label === 0 ? -1 : 1,
      }));

      const lr = 0.05;
      const C = 10;
      const epochs = 1000;

      for (let ep = 0; ep < epochs; ep++) {
        let dw0 = w0;
        let dw1 = w1;
        let db = 0;

        mathPts.forEach((p) => {
          const val = p.label * (w0 * p.x + w1 * p.y + b);
          if (val < 1) {
            dw0 -= C * p.label * p.x;
            dw1 -= C * p.label * p.y;
            db -= C * p.label;
          }
        });

        w0 -= lr * (dw0 / mathPts.length);
        w1 -= lr * (dw1 / mathPts.length);
        b -= lr * (db / mathPts.length);
      }

      mathPts.forEach((p) => {
        const val = p.label * (w0 * p.x + w1 * p.y + b);
        if (val <= 1.1) {
          numSVs++;
        }
      });

      const wNorm = Math.sqrt(w0 * w0 + w1 * w1);
      svmMargin = wNorm > 0.001 ? 2 / wNorm : 0;

      setSvCount(numSVs);
      setMargin(svmMargin);

      // Background shading
      const step = 5;
      for (let x = 0; x < width; x += step) {
        for (let y = 0; y < height; y += step) {
          const mx = (x + step / 2 - width / 2) / scaleX;
          const my = (height / 2 - (y + step / 2)) / scaleY;
          const score = w0 * mx + w1 * my + b;

          let fillVal = 0.5 + score * 0.5;
          fillVal = Math.max(0, Math.min(1, fillVal));

          ctx.fillStyle = `rgba(${Math.floor(168 * fillVal + 249 * (1 - fillVal))}, ${Math.floor(
            85 * fillVal + 115 * (1 - fillVal)
          )}, ${Math.floor(247 * fillVal + 22 * (1 - fillVal))}, 0.10)`;
          ctx.fillRect(x, y, step, step);
        }
      }

      // Draw decision line and margins
      if (Math.abs(w1) > 0.001) {
        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        let my1 = -(w0 * -1 + b) / w1;
        let my2 = -(w0 * 1 + b) / w1;
        ctx.moveTo(0, height / 2 - my1 * scaleY);
        ctx.lineTo(width, height / 2 - my2 * scaleY);
        ctx.stroke();

        // Margin +1 (Purple side)
        ctx.strokeStyle = "rgba(168, 85, 247, 0.6)";
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        my1 = -(w0 * -1 + b - 1) / w1;
        my2 = -(w0 * 1 + b - 1) / w1;
        ctx.moveTo(0, height / 2 - my1 * scaleY);
        ctx.lineTo(width, height / 2 - my2 * scaleY);
        ctx.stroke();

        // Margin -1 (Orange side)
        ctx.strokeStyle = "rgba(249, 115, 22, 0.6)";
        ctx.beginPath();
        my1 = -(w0 * -1 + b + 1) / w1;
        my2 = -(w0 * 1 + b + 1) / w1;
        ctx.moveTo(0, height / 2 - my1 * scaleY);
        ctx.lineTo(width, height / 2 - my2 * scaleY);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    } else {
      setSvCount(0);
      setMargin(0);
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

    // Draw points with support vector rings
    points.forEach((p) => {
      const mathPt = {
        x: (p.x - width / 2) / scaleX,
        y: (height / 2 - p.y) / scaleY,
        label: p.label === 0 ? -1 : 1,
      };
      const val = mathPt.label * (w0 * mathPt.x + w1 * mathPt.y + b);

      if (points.length >= 2 && val <= 1.1) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 11, 0, Math.PI * 2);
        ctx.stroke();
      }

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
            ⚔️ SVM 最大間距邊界沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            點擊放置點。系統將尋找「最大邊際」決策超平面，並圈出核心的支援向量（Support Vectors）。
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
          <span className="text-slate-500 text-xs block uppercase tracking-wider">安全間距 (Margin)</span>
          <span className="text-emerald-400 font-mono font-bold text-sm block mt-1">
            {margin.toFixed(3)}
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">支援向量個數</span>
          <span className="text-blue-400 font-mono font-bold text-sm block mt-1">
            {svCount} 個
          </span>
        </div>
      </div>
    </div>
  );
}
