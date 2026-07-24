"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface Point {
  x: number;
  y: number;
}

export default function LinearRegressionPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [equation, setEquation] = useState<string>("y = 0x + 0");
  const [r2, setR2] = useState<number>(0);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw background grid
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

    // Draw axis lines
    ctx.strokeStyle = "#475569"; // slate-600
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, height - 30);
    ctx.lineTo(width, height - 30);
    ctx.moveTo(40, 0);
    ctx.lineTo(40, height);
    ctx.stroke();

    // Draw points
    ctx.fillStyle = "#60a5fa"; // blue-400
    ctx.shadowBlur = 4;
    ctx.shadowColor = "#60a5fa";
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.shadowBlur = 0; // reset shadow

    // Calculate and draw regression line
    if (points.length >= 2) {
      // Convert standard canvas coordinates to math-like coordinates
      // Let x_val = p.x - 40, y_val = (height - 30) - p.y
      const n = points.length;
      let sumX = 0;
      let sumY = 0;
      let sumXY = 0;
      let sumX2 = 0;
      let sumY2 = 0;

      const mathPoints = points.map((p) => ({
        x: p.x - 40,
        y: height - 30 - p.y,
      }));

      mathPoints.forEach((p) => {
        sumX += p.x;
        sumY += p.y;
        sumXY += p.x * p.y;
        sumX2 += p.x * p.x;
        sumY2 += p.y * p.y;
      });

      const denominator = n * sumX2 - sumX * sumX;
      if (denominator !== 0) {
        const m = (n * sumXY - sumX * sumY) / denominator;
        const b = (sumY - m * sumX) / n;

        // R-squared calculation
        const avgY = sumY / n;
        let sst = 0; // Total sum of squares
        let ssr = 0; // Residual sum of squares
        mathPoints.forEach((p) => {
          const predY = m * p.x + b;
          sst += Math.pow(p.y - avgY, 2);
          ssr += Math.pow(p.y - predY, 2);
        });

        const calculatedR2 = sst === 0 ? 1 : 1 - ssr / sst;
        setR2(calculatedR2);
        setEquation(`y = ${m.toFixed(2)}x + ${b.toFixed(0)}`);

        // Draw the regression line
        // We find points on the line at math_x = 0 and math_x = width - 40
        const x1 = 40;
        const y1 = height - 30 - (m * 0 + b);

        const x2 = width;
        const y2 = height - 30 - (m * (width - 40) + b);

        ctx.strokeStyle = "#10b981"; // emerald-500
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
    } else {
      setEquation("y = 0x + 0");
      setR2(0);
    }
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

    // Check boundary
    if (x > 40 && y < canvas.height - 30) {
      setPoints([...points, { x, y }]);
    }
  };

  const handleReset = () => {
    setPoints([]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            📊 線性迴歸互動式沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            在網格中點擊任意位置放置資料點，系統將自動擬合最佳趨勢線。
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
        >
          <Trash2 size={14} /> 清空點
        </button>
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
              <HelpCircle size={16} className="text-blue-400" /> 請點擊畫布放置至少 2 個數據點
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 text-center">
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">迴歸方程式</span>
          <span className="text-emerald-400 font-mono font-bold text-base block mt-1">
            {equation}
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">決定係數 R² (擬合度)</span>
          <span className="text-blue-400 font-mono font-bold text-base block mt-1">
            {r2.toFixed(4)}
          </span>
        </div>
      </div>
    </div>
  );
}
