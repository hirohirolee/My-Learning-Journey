document.addEventListener('DOMContentLoaded', () => {
    const btnUpdate = document.getElementById('btn-update');
    const updateStatus = document.getElementById('update-status');
    const btnGenerate = document.getElementById('btn-generate');
    const loading = document.getElementById('loading');
    const ballsContainer = document.getElementById('balls-container');
    const errorMsg = document.getElementById('result-error');
    
    // 更新資料庫
    btnUpdate.addEventListener('click', async () => {
        btnUpdate.disabled = true;
        updateStatus.textContent = '正在嘗試連接伺服器抓取最新開獎資料...';
        updateStatus.style.color = 'var(--text-muted)';
        
        try {
            const response = await fetch('/api/update', { method: 'POST' });
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                updateStatus.textContent = '✅ ' + data.message;
                updateStatus.style.color = '#4ade80';
            } else {
                throw new Error(data.message || '更新失敗');
            }
        } catch (error) {
            updateStatus.textContent = '❌ 錯誤: ' + error.message;
            updateStatus.style.color = '#f87171';
        } finally {
            btnUpdate.disabled = false;
        }
    });
    
    // 產生推薦號碼
    btnGenerate.addEventListener('click', async () => {
        // 取得選擇的模式
        const selectedMode = document.querySelector('input[name="mode"]:checked').value;
        
        // UI 狀態切換
        btnGenerate.disabled = true;
        ballsContainer.innerHTML = '';
        ballsContainer.classList.add('hidden');
        errorMsg.classList.add('hidden');
        loading.classList.remove('hidden');
        
        try {
            // 模擬一點運算延遲，增加儀式感與 WOW 效應
            await new Promise(resolve => setTimeout(resolve, 800));
            
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mode: selectedMode })
            });
            
            const data = await response.json();
            loading.classList.add('hidden');
            
            if (response.ok && data.status === 'success') {
                displayBalls(data.numbers);
            } else {
                throw new Error(data.message || '產生號碼失敗');
            }
        } catch (error) {
            loading.classList.add('hidden');
            errorMsg.textContent = '❌ ' + error.message;
            errorMsg.classList.remove('hidden');
        } finally {
            btnGenerate.disabled = false;
        }
    });
    
    // 動態顯示號碼球 (逐一浮現動畫)
    function displayBalls(numbers) {
        ballsContainer.classList.remove('hidden');
        
        numbers.forEach((num, index) => {
            const ball = document.createElement('div');
            ball.className = 'ball';
            // 將數字補零
            ball.textContent = num.toString().padStart(2, '0');
            // 設定動畫延遲，產生逐一彈出的效果
            ball.style.animationDelay = `${index * 0.15}s`;
            ballsContainer.appendChild(ball);
        });
    }
});
