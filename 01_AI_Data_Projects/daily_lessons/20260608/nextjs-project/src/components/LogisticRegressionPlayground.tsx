"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface ClassPoint {
  x: number;
  y: number;
  label: number; // 0 or 1
}

export default function LogisticRegressionPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<ClassPoint[]>([]);
  const [currentLabel, setCurrentLabel] = useState<number>(1); // 1 = Purple (Positive), 0 = Orange (Negative)
  const [iterations, setIterations] = useState<number>(0);
  const [loss, setLoss] = useState<number>(0);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Train Logistic Regression Model using Gradient Descent
    let w0 = 0;
    let w1 = 0;
    let b = 0;
    const lr = 0.1;
    const steps = 1500;
    let currentLoss = 0;

    // Normalization scales
    const scaleX = width / 2;
    const scaleY = height / 2;

    const mathPoints = points.map((p) => ({
      x: (p.x - width / 2) / scaleX,
      y: (height / 2 - p.y) / scaleY,
      label: p.label,
    }));

    if (points.length >= 2) {
      for (let step = 0; step < steps; step++) {
        let dw0 = 0;
        let dw1 = 0;
        let db = 0;
        let tempLoss = 0;

        mathPoints.forEach((p) => {
          const z = w0 * p.x + w1 * p.y + b;
          const pred = 1 / (1 + Math.exp(-z));
          const diff = pred - p.label;

          dw0 += diff * p.x;
          dw1 += diff * p.y;
          db += diff;

          // Cross entropy loss
          const epsilon = 1e-15;
          const predClip = Math.max(epsilon, Math.min(1 - epsilon, pred));
          tempLoss += -(p.label * Math.log(predClip) + (1 - p.label) * Math.log(1 - predClip));
        });

        const n = points.length;
        dw0 /= n;
        dw1 /= n;
        db /= n;
        currentLoss = tempLoss / n;

        // Gradient descent step
        w0 -= lr * dw0;
        w1 -= lr * dw1;
        b -= lr * db;
      }
      setLoss(currentLoss);
    }

    // Draw background probability colors (Sigmoid field)
    if (points.length >= 2) {
      const stepSize = 5;
      for (let x = 0; x < width; x += stepSize) {
        for (let y = 0; y < height; y += stepSize) {
          const mx = (x + stepSize / 2 - width / 2) / scaleX;
          const my = (height / 2 - (y + stepSize / 2)) / scaleY;

          const z = w0 * mx + w1 * my + b;
          const prob = 1 / (1 + Math.exp(-z));

          // Draw probability shading: Class 1 (purple) vs Class 0 (orange)
          ctx.fillStyle = `rgba(${Math.floor(168 * prob + 249 * (1 - prob))}, ${Math.floor(
            85 * prob + 115 * (1 - prob))}, ${Math.floor(247 * prob + 22 * (1 - prob))}, 0.12)`;
          ctx.fillRect(x, y, stepSize, stepSize);
        }
      }
    }

    // Draw background grid lines
    ctx.strokeStyle = "rgba(30, 41, 59, 0.4)"; // slate-800 with low opacity
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

    // Draw decision boundary line: w0*x + w1*y + b = 0
    // => y = -(w0*x + b) / w1
    if (points.length >= 2 && Math.abs(w1) > 0.001) {
      ctx.strokeStyle = "#10b981"; // emerald-500
      ctx.lineWidth = 2.5;
      ctx.shadowBlur = 4;
      ctx.shadowColor = "#10b981";
      ctx.beginPath();

      const mathX1 = -1;
      const mathY1 = -(w0 * mathX1 + b) / w1;
      const x1 = mathX1 * scaleX + width / 2;
      const y1 = height / 2 - mathY1 * scaleY;

      const mathX2 = 1;
      const mathY2 = -(w0 * mathX2 + b) / w1;
      const x2 = mathX2 * scaleX + width / 2;
      const y2 = height / 2 - mathY2 * scaleY;

      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.shadowBlur = 0; // reset shadow
    }

    // Draw points
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      if (p.label === 1) {
        ctx.fillStyle = "#a855f7"; // purple-500
        ctx.shadowColor = "#a855f7";
      } else {
        ctx.fillStyle = "#f97316"; // orange-500
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
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setPoints([...points, { x, y, label: currentLabel }]);
  };

  const handleReset = () => {
    setPoints([]);
    setLoss(0);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            🛑 邏輯迴歸邊界二分沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            在網格中添加不同類型的點，觀察分類邊界和 Sigmoid 機率分布的動態更新。
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
        <label className="text-xs font-semibold text-slate-300">選擇放置類別：</label>
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
          <span className="text-slate-500 text-xs block uppercase tracking-wider">梯度下降優化疊代</span>
          <span className="text-emerald-400 font-mono font-bold text-base block mt-1">
            {points.length >= 2 ? "1,500 Steps (GD)" : "等待數據點"}
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">交叉熵損失值 (Loss)</span>
          <span className="text-blue-400 font-mono font-bold text-base block mt-1">
            {points.length >= 2 ? loss.toFixed(5) : "0.00000"}
          </span>
        </div>
      </div>
    </div>
  );
}
