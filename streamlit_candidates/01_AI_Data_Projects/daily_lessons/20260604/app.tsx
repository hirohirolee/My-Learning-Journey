import React, { useState } from 'react';
import { Sparkles, Download, Image as ImageIcon, Loader2, AlertCircle, RefreshCw } from 'lucide-react';

// 定義 API 回應的型別
interface Prediction {
  bytesBase64Encoded: string;
}

interface ApiResponse {
  predictions?: Prediction[];
  error?: {
    message: string;
  };
}

export default function App() {
  const [prompt, setPrompt] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string>('');

  // 實作指數退避 (Exponential Backoff) 的重試機制
  const fetchWithRetry = async (url: string, options: RequestInit, retries = 5): Promise<any> => {
    const delays = [1000, 2000, 4000, 8000, 16000];
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(url, options);
        if (!response.ok) {
          throw new Error(`伺服器回應錯誤 (狀態碼: ${response.status})`);
        }
        return await response.json();
      } catch (e) {
        if (i === retries - 1) throw e;
        await new Promise(resolve => setTimeout(resolve, delays[i]));
      }
    }
  };

  const generateImage = async () => {
    if (!prompt.trim()) {
      setError('請先輸入你想生成的圖片描述！');
      return;
    }

    setLoading(true);
    setError('');
    setImageUrl(null);

    try {
      const apiKey = ""; // 執行環境會自動提供 API Key，若在本地測試請填入你自己的 Key
      const url = `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${apiKey}`;
      
      const payload = {
        instances: { prompt: prompt.trim() },
        parameters: { sampleCount: 1 }
      };

      const result: ApiResponse = await fetchWithRetry(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (result.error) {
        setError(`伺服器錯誤: ${result.error.message || '發生未知錯誤'}`);
      } else if (result.predictions && result.predictions[0] && result.predictions[0].bytesBase64Encoded) {
        setImageUrl(`data:image/png;base64,${result.predictions[0].bytesBase64Encoded}`);
      } else {
        setError('無法生成圖片。這通常是因為「提示詞觸發了安全審查機制」。請修改提示詞後再試一次！');
      }
    } catch (err) {
      setError('連線或生成過程中發生錯誤，請稍後再試。');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `AI-Image-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleClear = () => {
    setPrompt('');
    setImageUrl(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex justify-center text-gray-800 font-sans">
      <div className="w-full max-w-md bg-white shadow-xl flex flex-col min-h-screen sm:min-h-[auto] sm:my-8 sm:rounded-[2.5rem] overflow-hidden relative">
        
        {/* 頂部導覽列 */}
        <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-5 shadow-md z-10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-yellow-300" />
            <h1 className="text-xl font-bold tracking-wide">AI 魔法生圖器</h1>
          </div>
          <p className="text-purple-100 text-xs mt-1 opacity-80">輸入文字，見證奇蹟 (TypeScript 版)</p>
        </header>

        {/* 內容區域 */}
        <main className="flex-1 p-5 flex flex-col gap-6 overflow-y-auto">
          
          <div className="space-y-3">
            <label htmlFor="prompt" className="block text-sm font-semibold text-gray-700">
              你想畫些什麼？
            </label>
            <div className="relative">
              <textarea
                id="prompt"
                rows={4}
                className="w-full bg-gray-50 border border-gray-200 rounded-2xl p-4 text-base focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all resize-none shadow-inner"
                placeholder="例如：一隻可愛的貓咪在攀爬台北101大樓，卡通風格..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={loading}
              />
              {prompt && !loading && (
                <button 
                  onClick={() => setPrompt('')}
                  className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 bg-gray-100 rounded-full p-1"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}
            </div>
            
            <button
              onClick={generateImage}
              disabled={loading || !prompt.trim()}
              className={`w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${
                loading || !prompt.trim()
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-200'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>魔法施展中...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-6 h-6" />
                  <span>立即生成圖片</span>
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-2xl flex items-start gap-3 text-sm animate-in fade-in zoom-in duration-300">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <p className="leading-relaxed">{error}</p>
            </div>
          )}

          <div className="mt-2 flex-1 flex flex-col">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">生成結果</h2>
            <div className={`flex-1 min-h-[300px] rounded-3xl border-2 border-dashed flex flex-col items-center justify-center overflow-hidden relative transition-colors ${
              imageUrl ? 'border-transparent bg-gray-100 shadow-inner' : 'border-gray-200 bg-gray-50'
            }`}>
              
              {loading && !imageUrl && (
                <div className="flex flex-col items-center text-indigo-500 animate-pulse">
                  <ImageIcon className="w-12 h-12 mb-3 opacity-80" />
                  <p className="text-sm font-medium">正在為您繪製...</p>
                </div>
              )}

              {!loading && !imageUrl && (
                <div className="flex flex-col items-center text-gray-400">
                  <ImageIcon className="w-12 h-12 mb-3 opacity-30" />
                  <p className="text-sm font-medium">圖片將顯示於此</p>
                </div>
              )}

              {imageUrl && (
                <img 
                  src={imageUrl} 
                  alt="AI Generated" 
                  className="w-full h-full object-cover animate-in fade-in duration-500"
                />
              )}
            </div>

            {imageUrl && (
              <div className="grid grid-cols-2 gap-3 mt-4 animate-in slide-in-from-bottom-4 duration-300">
                <button
                  onClick={handleDownload}
                  className="py-3 px-4 bg-gray-900 text-white rounded-2xl font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 active:scale-[0.98] transition-transform"
                >
                  <Download className="w-5 h-5" />
                  <span>儲存圖片</span>
                </button>
                <button
                  onClick={handleClear}
                  className="py-3 px-4 bg-gray-100 text-gray-700 rounded-2xl font-semibold flex items-center justify-center gap-2 hover:bg-gray-200 active:scale-[0.98] transition-transform"
                >
                  <span>再畫一張</span>
                </button>
              </div>
            )}
          </div>
          
        </main>
      </div>
    </div>
  );
}
