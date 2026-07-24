"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface ClassPoint {
  x: number;
  y: number;
  label: number; // 0 (Orange) or 1 (Purple)
}

export default function DecisionTreePlayground() {
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
  const [splitRule, setSplitRule] = useState<string>("無分割");
  const [gini, setGini] = useState<number>(0.5);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    let bestSplit: {
      type: "x" | "y";
      value: number;
      gini: number;
      leftLabel: number;
      rightLabel: number;
    } | null = null;
    let bestGini = 1.0;

    const n = points.length;
    let giniInit = 0.5;

    if (n >= 2) {
      const p1_init = points.filter((p) => p.label === 1).length / n;
      const p0_init = 1 - p1_init;
      giniInit = 1 - p1_init * p1_init - p0_init * p0_init;
      bestGini = giniInit;

      const xCandidates = points.map((p) => p.x);
      const yCandidates = points.map((p) => p.y);

      const evaluateSplit = (type: "x" | "y", val: number) => {
        const left = points.filter((p) => (type === "x" ? p.x < val : p.y < val));
        const right = points.filter((p) => (type === "x" ? p.x >= val : p.y >= val));
        if (left.length === 0 || right.length === 0) return;

        const p1_L = left.filter((p) => p.label === 1).length / left.length;
        const giniL = 1 - p1_L * p1_L - Math.pow(1 - p1_L, 2);

        const p1_R = right.filter((p) => p.label === 1).length / right.length;
        const giniR = 1 - p1_R * p1_R - Math.pow(1 - p1_R, 2);

        const weightedGini = (left.length / n) * giniL + (right.length / n) * giniR;
        if (weightedGini < bestGini) {
          bestGini = weightedGini;
          const left0 = left.filter((p) => p.label === 0).length;
          const left1 = left.length - left0;
          const right0 = right.filter((p) => p.label === 0).length;
          const right1 = right.length - right0;

          bestSplit = {
            type,
            value: val,
            gini: weightedGini,
            leftLabel: left1 >= left0 ? 0 : 1,
            rightLabel: right1 >= right0 ? 0 : 1,
          };
        }
      };

      xCandidates.forEach((val) => evaluateSplit("x", val));
      yCandidates.forEach((val) => evaluateSplit("y", val));

      if (bestSplit) {
        // Shading zones
        if (bestSplit.type === "x") {
          ctx.fillStyle = bestSplit.leftLabel === 1 ? "rgba(168, 85, 247, 0.08)" : "rgba(249, 115, 22, 0.08)";
          ctx.fillRect(0, 0, bestSplit.value, height);
          ctx.fillStyle = bestSplit.rightLabel === 1 ? "rgba(168, 85, 247, 0.08)" : "rgba(249, 115, 22, 0.08)";
          ctx.fillRect(bestSplit.value, 0, width - bestSplit.value, height);
        } else {
          ctx.fillStyle = bestSplit.leftLabel === 1 ? "rgba(168, 85, 247, 0.08)" : "rgba(249, 115, 22, 0.08)";
          ctx.fillRect(0, 0, width, bestSplit.value);
          ctx.fillStyle = bestSplit.rightLabel === 1 ? "rgba(168, 85, 247, 0.08)" : "rgba(249, 115, 22, 0.08)";
          ctx.fillRect(0, bestSplit.value, width, height - bestSplit.value);
        }

        setSplitRule(
          `${bestSplit.type.toUpperCase()} ${bestSplit.type === "x" ? "垂直分割線" : "水平分割線"} @ ${bestSplit.value.toFixed(0)}`
        );
        setGini(bestSplit.gini);
      } else {
        setSplitRule("無有效分割");
        setGini(giniInit);
      }
    } else {
      setSplitRule("無分割");
      setGini(0.5);
    }

    // Draw grid
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

    // Draw split line
    if (bestSplit) {
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 2.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      if (bestSplit.type === "x") {
        ctx.moveTo(bestSplit.value, 0);
        ctx.lineTo(bestSplit.value, height);
      } else {
        ctx.moveTo(0, bestSplit.value);
        ctx.lineTo(width, bestSplit.value);
      }
      ctx.stroke();
      ctx.setLineDash([]);
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
            🌿 決策樹空間分割沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            點擊放置不同類別的點，觀察樹節點如何進行分割以極小化基尼係數。
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
          <span className="text-slate-500 text-xs block uppercase tracking-wider">最佳切割規則</span>
          <span className="text-emerald-400 font-mono font-bold text-sm block mt-1">
            {splitRule}
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">分割後基尼係數 (Gini)</span>
          <span className="text-blue-400 font-mono font-bold text-sm block mt-1">
            {gini.toFixed(4)}
          </span>
        </div>
      </div>
    </div>
  );
}
