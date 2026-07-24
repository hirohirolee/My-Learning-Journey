"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface KNNPoint {
  x: number;
  y: number;
  label: number; // 0 = Blue, 1 = Orange, 2 = Purple
}

export default function KNNPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<KNNPoint[]>([
    // Default points to give an immediate good visual
    { x: 120, y: 100, label: 0 },
    { x: 150, y: 130, label: 0 },
    { x: 100, y: 160, label: 0 },
    { x: 380, y: 220, label: 1 },
    { x: 350, y: 260, label: 1 },
    { x: 400, y: 240, label: 1 },
    { x: 250, y: 280, label: 2 },
    { x: 220, y: 290, label: 2 },
    { x: 280, y: 260, label: 2 },
  ]);
  const [currentLabel, setCurrentLabel] = useState<number>(0); // 0, 1, 2
  const [kValue, setKValue] = useState<number>(3);
  const [queryPoint, setQueryPoint] = useState<{ x: number; y: number }>({ x: 240, y: 180 });
  const [votes, setVotes] = useState<{ [key: number]: number }>({ 0: 0, 1: 0, 2: 0 });
  const [prediction, setPrediction] = useState<number | null>(null);

  const getDistance = (p1: { x: number; y: number }, p2: { x: number; y: number }) => {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
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

    // Colors mapping
    const colors = ["#60a5fa", "#f97316", "#a855f7"]; // blue-400, orange-500, purple-500

    // Find K nearest neighbors
    let neighbors: { point: KNNPoint; dist: number }[] = [];
    if (points.length > 0) {
      const dists = points.map((p) => ({
        point: p,
        dist: getDistance(queryPoint, p),
      }));

      // Sort ascending by distance
      dists.sort((a, b) => a.dist - b.dist);
      neighbors = dists.slice(0, Math.min(kValue, points.length));

      // Calculate votes
      const localVotes: { [key: number]: number } = { 0: 0, 1: 0, 2: 0 };
      neighbors.forEach((n) => {
        localVotes[n.point.label] = (localVotes[n.point.label] || 0) + 1;
      });
      setVotes(localVotes);

      // Find winner
      let maxVotes = -1;
      let winnerLabel = 0;
      Object.keys(localVotes).forEach((kStr) => {
        const k = parseInt(kStr);
        if (localVotes[k] > maxVotes) {
          maxVotes = localVotes[k];
          winnerLabel = k;
        }
      });
      setPrediction(winnerLabel);
    } else {
      setPrediction(null);
      setVotes({ 0: 0, 1: 0, 2: 0 });
    }

    // Draw connections and highlighting circles for the K neighbors
    neighbors.forEach((n) => {
      // Draw dotted line
      ctx.strokeStyle = "rgba(148, 163, 184, 0.6)"; // slate-400
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(queryPoint.x, queryPoint.y);
      ctx.lineTo(n.point.x, n.point.y);
      ctx.stroke();
      ctx.setLineDash([]); // reset line dash

      // Draw halo circle around neighbor
      ctx.strokeStyle = colors[n.point.label];
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(n.point.x, n.point.y, 13, 0, Math.PI * 2);
      ctx.stroke();
    });

    // Draw all training points
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = colors[p.label];
      ctx.shadowColor = colors[p.label];
      ctx.shadowBlur = 4;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Draw query point (the test point)
    ctx.beginPath();
    ctx.arc(queryPoint.x, queryPoint.y, 10, 0, Math.PI * 2);
    ctx.fillStyle = prediction !== null ? colors[prediction] : "#ffffff";
    ctx.shadowBlur = 8;
    ctx.shadowColor = prediction !== null ? colors[prediction] : "#ffffff";
    ctx.fill();
    ctx.shadowBlur = 0;

    // Draw white ring overlay around query point
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(queryPoint.x, queryPoint.y, 10, 0, Math.PI * 2);
    ctx.stroke();

    // Draw crosshair lines inside query point
    ctx.strokeStyle = "#0f172a"; // dark background color for contrast
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(queryPoint.x - 4, queryPoint.y);
    ctx.lineTo(queryPoint.x + 4, queryPoint.y);
    ctx.moveTo(queryPoint.x, queryPoint.y - 4);
    ctx.lineTo(queryPoint.x, queryPoint.y + 4);
    ctx.stroke();
  };

  useEffect(() => {
    drawCanvas();
  }, [points, queryPoint, kValue]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Standard mode: Clicking places a point of the currently selected label
    // If user holds Shift, it moves the query point
    if (e.shiftKey) {
      setQueryPoint({ x, y });
    } else {
      setPoints([...points, { x, y, label: currentLabel }]);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    // If left mouse button is pressed and shift is held, we can drag the query point
    if (e.buttons === 1 && e.shiftKey) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setQueryPoint({ x, y });
    }
  };

  const handleReset = () => {
    setPoints([]);
  };

  const labelNames = ["類別 A (藍色)", "類別 B (橘色)", "類別 C (紫色)"];
  const colors = ["text-blue-400", "text-orange-500", "text-purple-500"];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            📍 KNN 鄰近決策互動式沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            <strong>一般點擊：</strong>放置訓練樣本點。 <strong>Shift+點擊 / 拖曳：</strong>移動測試定位點（雙環靶心）。
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
        >
          <Trash2 size={14} /> 清空點
        </button>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-4 bg-slate-950 border border-slate-800/80 p-3 rounded-xl">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300 whitespace-nowrap">新增樣本類別：</label>
          <div className="flex gap-2">
            {[0, 1, 2].map((lbl) => (
              <button
                key={lbl}
                onClick={() => setCurrentLabel(lbl)}
                className={`w-7 h-7 rounded-full border transition flex items-center justify-center ${
                  currentLabel === lbl
                    ? "border-white scale-110 shadow-lg"
                    : "border-transparent opacity-60 hover:opacity-100"
                }`}
                style={{
                  backgroundColor: lbl === 0 ? "#60a5fa" : lbl === 1 ? "#f97316" : "#a855f7",
                }}
                title={labelNames[lbl]}
              />
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300 whitespace-nowrap">K 值 (鄰居數): {kValue}</label>
          <input
            type="range"
            min="1"
            max={Math.max(1, points.length)}
            value={kValue}
            onChange={(e) => setKValue(parseInt(e.target.value))}
            className="w-32 h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
        </div>
      </div>

      <div className="relative border border-slate-700 rounded-xl overflow-hidden bg-slate-950 flex justify-center">
        <canvas
          ref={canvasRef}
          width={500}
          height={320}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          className="cursor-crosshair w-full block max-w-full bg-slate-950"
        />
        {points.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-slate-950/60 backdrop-blur-[1px]">
            <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
              <HelpCircle size={16} className="text-blue-400" /> 請先點擊放置一些不同顏色的訓練點
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center items-center text-center">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">鄰居投票計數 (Votes)</span>
          <div className="flex gap-4 mt-2">
            {[0, 1, 2].map((lbl) => (
              <div key={lbl} className="flex flex-col items-center">
                <span className={`w-3.5 h-3.5 rounded-full ${lbl === 0 ? "bg-blue-400" : lbl === 1 ? "bg-orange-500" : "bg-purple-500"}`}></span>
                <span className="text-slate-300 font-mono font-bold mt-1 text-sm">{votes[lbl]} 票</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center items-center text-center">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">定位點預測類別 (Prediction)</span>
          {prediction !== null ? (
            <span className={`font-bold text-base mt-2 flex items-center gap-2 ${colors[prediction]}`}>
              <span className={`w-3.5 h-3.5 rounded-full ${prediction === 0 ? "bg-blue-400" : prediction === 1 ? "bg-orange-500" : "bg-purple-500"}`}></span>
              {labelNames[prediction]}
            </span>
          ) : (
            <span className="text-slate-500 text-sm mt-2 font-medium">無足夠鄰居點</span>
          )}
        </div>
      </div>
    </div>
  );
}
