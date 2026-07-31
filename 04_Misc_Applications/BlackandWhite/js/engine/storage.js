/**
 * 商業級本地/雲端序列化存檔引擎 (Storage & Save/Load Serialization Manager)
 * 負責處理玩家帳號局外養成 (Meta Progression)、關卡中斷點記憶、防篡改驗證碼與跨裝置 Base64 匯出匯入。
 */
export class StorageManager {
    constructor(prefix = 'BW_DIVINE_') {
        this.prefix = prefix;
        this.secretKey = 'ANTIGRAVITY_GOD_ENGINE_2026'; // 用於簡易驗證碼防止隨意修改損毀存檔
    }

    /**
     * 計算字串簡易 Hash 驗證碼 (Checksum)
     */
    generateChecksum(str) {
        let hash = 0;
        const combined = str + this.secretKey;
        for (let i = 0; i < combined.length; i++) {
            const char = combined.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash.toString(16);
    }

    /**
     * 儲存資料至 localStorage (自動封裝驗證碼與 Base64 編碼)
     */
    save(key, dataObject) {
        try {
            const jsonStr = JSON.stringify(dataObject);
            const checksum = this.generateChecksum(jsonStr);
            const packageObj = {
                data: jsonStr,
                hash: checksum,
                timestamp: Date.now(),
                version: '1.0.0'
            };
            const base64Str = btoa(unescape(encodeURIComponent(JSON.stringify(packageObj))));
            localStorage.setItem(this.prefix + key, base64Str);
            return true;
        } catch (e) {
            console.error(`[StorageManager] Save failed for key "${key}":`, e);
            return false;
        }
    }

    /**
     * 從 localStorage 讀取並解驗證資料
     */
    load(key, defaultData = null) {
        try {
            const base64Str = localStorage.getItem(this.prefix + key);
            if (!base64Str) return defaultData;

            const packageStr = decodeURIComponent(escape(atob(base64Str)));
            const packageObj = JSON.parse(packageStr);

            // 驗證防篡改 Checksum
            const expectedHash = this.generateChecksum(packageObj.data);
            if (packageObj.hash !== expectedHash) {
                console.warn(`[StorageManager] Save data corrupted or tampered for key "${key}". Using default.`);
                return defaultData;
            }

            return JSON.parse(packageObj.data);
        } catch (e) {
            console.error(`[StorageManager] Load failed for key "${key}":`, e);
            return defaultData;
        }
    }

    /**
     * 刪除特定存檔槽位
     */
    remove(key) {
        localStorage.removeItem(this.prefix + key);
    }

    /**
     * 匯出存檔為 Base64 字串 (供跨裝置讀取或客服處理)
     */
    exportSaveString(key) {
        return localStorage.getItem(this.prefix + key) || '';
    }

    /**
     * 匯入外部 Base64 存檔字串並驗證
     */
    importSaveString(key, base64Str) {
        try {
            const packageStr = decodeURIComponent(escape(atob(base64Str)));
            const packageObj = JSON.parse(packageStr);
            const expectedHash = this.generateChecksum(packageObj.data);
            if (packageObj.hash !== expectedHash) {
                return { success: false, reason: '存檔驗證碼錯誤或檔案已損毀！' };
            }
            localStorage.setItem(this.prefix + key, base64Str);
            return { success: true, data: JSON.parse(packageObj.data) };
        } catch (e) {
            return { success: false, reason: '無效的存檔字串格式！' };
        }
    }
}

// 匯出預設單例供全局調用
export const gameStorage = new StorageManager();
