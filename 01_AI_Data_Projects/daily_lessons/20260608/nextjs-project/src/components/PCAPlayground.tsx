"use client";

import React, { useRef, useState, useEffect } from "react";
import { Trash2, HelpCircle } from "lucide-react";

interface Point {
  x: number;
  y: number;
}

export default function PCAPlayground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([
    // Seed points with a linear correlation to make the principal component clear
    { x: 150, y: 220 },
    { x: 180, y: 200 },
    { x: 210, y: 170 },
    { x: 250, y: 150 },
    { x: 280, y: 130 },
    { x: 310, y: 110 },
    { x: 340, y: 90 },
    { x: 160, y: 230 },
    { x: 330, y: 100 },
  ]);
  const [eigenvalues, setEigenvalues] = useState<number[]>([0, 0]);
  const [pc1, setPc1] = useState<number[]>([0, 0]);

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

    if (points.length >= 3) {
      // 1. Calculate Means
      const n = points.length;
      let sumX = 0;
      let sumY = 0;
      points.forEach((p) => {
        sumX += p.x;
        sumY += p.y;
      });
      const meanX = sumX / n;
      const meanY = sumY / n;

      // 2. Calculate Covariance Matrix
      // Cov = [[varX, covXY], [covXY, varY]]
      let varX = 0;
      let varY = 0;
      let covXY = 0;
      points.forEach((p) => {
        const dx = p.x - meanX;
        const dy = p.y - meanY;
        varX += dx * dx;
        varY += dy * dy;
        covXY += dx * dy;
      });
      varX /= n;
      varY /= n;
      covXY /= n;

      // 3. Calculate Eigenvalues
      // Solve det(Cov - lambda*I) = 0
      // lambda^2 - (varX + varY)*lambda + (varX*varY - covXY^2) = 0
      const tr = varX + varY;
      const det = varX * varY - covXY * covXY;
      const desc = tr * tr - 4 * det;

      let l1 = 0;
      let l2 = 0;
      let v1 = [0, 0];
      let v2 = [0, 0];

      if (desc >= 0) {
        l1 = (tr + Math.sqrt(desc)) / 2;
        l2 = (tr - Math.sqrt(desc)) / 2;

        setEigenvalues([l1, l2]);

        // 4. Calculate Eigenvectors
        // For l1: (varX - l1)*x + covXY*y = 0
        if (Math.abs(covXY) > 1e-4) {
          const x1 = 1;
          const y1 = (l1 - varX) / covXY;
          const len = Math.sqrt(x1 * x1 + y1 * y1);
          v1 = [x1 / len, y1 / len];
        } else {
          // Uncorrelated
          if (varX > varY) {
            v1 = [1, 0];
          } else {
            v1 = [0, 1];
          }
        }
        // v2 is orthogonal to v1
        v2 = [-v1[1], v1[0]];
        setPc1(v1);
      }

      // Draw projections of points onto PC1 line
      if (l1 > 0) {
        points.forEach((p) => {
          const dx = p.x - meanX;
          const dy = p.y - meanY;
          // Dot product projection
          const dot = dx * v1[0] + dy * v1[1];
          const projX = meanX + dot * v1[0];
          const projY = meanY + dot * v1[1];

          // Draw dotted projection line
          ctx.strokeStyle = "rgba(100, 116, 139, 0.4)"; // slate-500
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 3]);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(projX, projY);
          ctx.stroke();
          ctx.setLineDash([]);
        });
      }

      // Draw Mean Center mark
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(meanX, meanY, 5, 0, Math.PI * 2);
      ctx.fill();

      // Draw Principal Component arrows
      // Length proportional to standard deviation (sqrt of eigenvalue)
      const arrowScale = 2.5;

      if (l1 > 0) {
        const p1x = meanX + v1[0] * Math.sqrt(l1) * arrowScale;
        const p1y = meanY + v1[1] * Math.sqrt(l1) * arrowScale;

        // Draw PC1 Arrow (Red)
        ctx.strokeStyle = "#ef4444"; // red-500
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(meanX, meanY);
        ctx.lineTo(p1x, p1y);
        ctx.stroke();

        // Draw arrowhead
        const angle = Math.atan2(v1[1], v1[0]);
        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.moveTo(p1x, p1y);
        ctx.lineTo(p1x - 10 * Math.cos(angle - Math.PI / 6), p1y - 10 * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(p1x - 10 * Math.cos(angle + Math.PI / 6), p1y - 10 * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
      }

      if (l2 > 0) {
        const p2x = meanX + v2[0] * Math.sqrt(l2) * arrowScale;
        const p2y = meanY + v2[1] * Math.sqrt(l2) * arrowScale;

        // Draw PC2 Arrow (Blue)
        ctx.strokeStyle = "#3b82f6"; // blue-500
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(meanX, meanY);
        ctx.lineTo(p2x, p2y);
        ctx.stroke();

        // Draw arrowhead
        const angle = Math.atan2(v2[1], v2[0]);
        ctx.fillStyle = "#3b82f6";
        ctx.beginPath();
        ctx.moveTo(p2x, p2y);
        ctx.lineTo(p2x - 8 * Math.cos(angle - Math.PI / 6), p2y - 8 * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(p2x - 8 * Math.cos(angle + Math.PI / 6), p2y - 8 * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
      }
    }

    // Draw all points
    ctx.fillStyle = "#e2e8f0"; // slate-200
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.fill();
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

    setPoints([...points, { x, y }]);
  };

  const handleReset = () => {
    setPoints([]);
    setEigenvalues([0, 0]);
    setPc1([0, 0]);
  };

  const totalVar = eigenvalues[0] + eigenvalues[1];
  const pc1Ratio = totalVar > 0 ? (eigenvalues[0] / totalVar) * 100 : 0;
  const pc2Ratio = totalVar > 0 ? (eigenvalues[1] / totalVar) * 100 : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg max-w-full">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="text-emerald-400 font-bold text-lg flex items-center gap-2">
            📉 PCA 降維與特徵向量沙盒 (Sandbox)
          </h4>
          <p className="text-slate-400 text-xs mt-1">
            點擊畫布放置資料點。系統將自動計算並繪製 <span className="text-red-500 font-bold">第一主成分 (PC1)</span> 與 <span className="text-blue-500 font-bold">第二主成分 (PC2)</span> 的方向與變異佔比。
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
        {points.length < 3 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-slate-950/60 backdrop-blur-[1px]">
            <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
              <HelpCircle size={16} className="text-blue-400" /> 請點擊放置至少 3 個具有某種線性分布的資料點
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 text-center">
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">第一主成分 (PC1) 資訊量</span>
          <span className="text-red-400 font-mono font-bold text-base block mt-1">
            {pc1Ratio.toFixed(1)}% <span className="text-xs text-slate-500">(PC1 = [{pc1[0].toFixed(2)}, {pc1[1].toFixed(2)}])</span>
          </span>
        </div>
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
          <span className="text-slate-500 text-xs block uppercase tracking-wider">第二主成分 (PC2) 資訊量</span>
          <span className="text-blue-400 font-mono font-bold text-base block mt-1">
            {pc2Ratio.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}
