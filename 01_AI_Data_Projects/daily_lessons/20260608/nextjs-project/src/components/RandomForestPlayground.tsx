"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface ClassPoint {
  x: number;
  y: number;
  label: number; // 0 or 1
}

export default function RandomForestPlayground() {
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
  const [status, setStatus] = useState<string>("等待數據點");

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
      const numTrees = 5;
      const trees: {
        type: "x" | "y";
        value: number;
        leftLabel: number;
        rightLabel: number;
      }[] = [];

      // Train 5 trees
      for (let t = 0; t < numTrees; t++) {
        const sample: ClassPoint[] = [];
        for (let s = 0; s < points.length; s++) {
          const rIdx = Math.floor(Math.random() * points.length);
          sample.push(points[rIdx]);
        }

        const splitType = Math.random() > 0.5 ? "x" : "y";
        const randomPt = sample[Math.floor(Math.random() * sample.length)];
        const splitValue = splitType === "x" ? randomPt.x : randomPt.y;

        const left = sample.filter((p) => (splitType === "x" ? p.x < splitValue : p.y < splitValue));
        const right = sample.filter((p) => (splitType === "x" ? p.x >= splitValue : p.y >= splitValue));

        const left0 = left.filter((p) => p.label === 0).length;
        const left1 = left.length - left0;
        const right0 = right.filter((p) => p.label === 0).length;
        const right1 = right.length - right0;

        trees.push({
          type: splitType,
          value: splitValue,
          leftLabel: left1 >= left0 ? 1 : 0,
          rightLabel: right1 >= right0 ? 1 : 0,
        });
      }

      // Render background majority vote
      const step = 8;
      for (let x = 0; x < width; x += step) {
        for (let y = 0; y < height; y += step) {
          let vote1 = 0;
          let vote0 = 0;

          trees.forEach((t) => {
            const val = t.type === "x" ? x : y;
            if (val < t.value) {
              if (t.leftLabel === 1) vote1++;
              else vote0++;
            } else {
              if (t.rightLabel === 1) vote1++;
              else vote0++;
            }
          });

          const prob1 = vote1 / numTrees;
          ctx.fillStyle = `rgba(${Math.floor(168 * prob1 + 249 * (1 - prob1))}, ${Math.floor(
            85 * prob1 + 115 * (1 - prob1)
          )}, ${Math.floor(247 * prob1 + 22 * (1 - prob1))}, 0.12)`;
          ctx.fillRect(x, y, step, step);
        }
      }

      // Draw sub-tree boundaries
      ctx.strokeStyle = "rgba(16, 185, 129, 0.35)";
      ctx.lineWidth = 1.5;
      trees.forEach((t) => {
        ctx.beginPath();
        if (t.type === "x") {
          ctx.moveTo(t.value, 0);
          ctx.lineTo(t.value, height);
        } else {
          ctx.moveTo(0, t.value);
          ctx.lineTo(width, t.value);
        }
        ctx.stroke();
      });

      setStatus("集成投票完成");
    } else {
      setStatus("等待數據點");
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
            🌲 隨機森林集成多數決沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            放置不同的點。系統會訓練 5 棵隨機子樹，並用多數決投票融合成更平滑、穩定的決策邊界。
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
          <span className="text-slate-500 text-xs block uppercase tracking-wider">森林子樹數量</span>
          <span className="text-emerald-400 font-mono font-bold text-sm block mt-1">
            5 棵決策樹
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">投票表決狀態</span>
          <span
            className={`font-mono font-bold text-sm block mt-1 ${
              points.length >= 2 ? "text-emerald-400" : "text-slate-400"
            }`}
          >
            {status}
          </span>
        </div>
      </div>
    </div>
  );
}
