# Power BI 資料模型設計

> 適用於「市場套利分析與資訊效率稽核系統」輸出的 Star Schema 設計文件

---

## 一、Star Schema 架構總覽

```
                    ┌─────────────────────┐
                    │   dim_match         │
                    │─────────────────────│
                    │ match_id (PK)       │◄──┐
                    │ home_team           │   │
                    │ away_team           │   │
                    │ sport               │   │
                    │ commence_time       │   │
                    └─────────────────────┘   │
                                              │
┌─────────────────────┐                       │
│   dim_platform      │                       │
│─────────────────────│                       │
│ platform_id (PK)    │◄──┐   ┌───────────────────────────────────┐
│ platform_key        │   │   │         fact_odds_snapshot         │
│ platform_name       │   │   │───────────────────────────────────│
│ region              │   ├───│ snapshot_id (PK)                  │
└─────────────────────┘   │   │ match_id (FK → dim_match)         │
                          ├───│ platform_id (FK → dim_platform)   │
                          │   │ date_id (FK → dim_date)           │
┌─────────────────────┐   │   │ odds_home                         │
│   dim_date          │   │   │ odds_away                         │
│─────────────────────│   │   │ odds_draw                         │
│ date_id (PK)        │◄──┘   │ implied_prob_sum                  │
│ full_date           │       │ roi                               │
│ year                │       │ latency_ms                        │
│ month               │       │ is_valid                          │
│ day                 │       │ anomaly_flag                      │
│ hour                │       │ anomaly_reason                    │
│ day_of_week         │       │ stability_score                   │
│ is_weekend          │       │ change_count                      │
└─────────────────────┘       │ has_arb_opportunity               │
                              └───────────────────────────────────┘
```

---

## 二、各表詳細說明

### 2.1 Fact Table：`fact_odds_snapshot`

每筆記錄代表**一次賠率快照**（一場賽事 × 一個博彩平台 × 一個時間點）。

| 欄位 | 型別 | 說明 | 來源欄位 |
|------|------|------|---------|
| `snapshot_id` | INT (PK) | 代理主鍵 | `id` |
| `match_id` | TEXT (FK) | 關聯 dim_match | `match_id` |
| `platform_id` | TEXT (FK) | 關聯 dim_platform | `platform` |
| `date_id` | INT (FK) | 關聯 dim_date（格式：YYYYMMDDHH） | 衍生自 `timestamp` |
| `odds_home` | FLOAT | 主場勝出賠率（歐洲式） | `odds_home` |
| `odds_away` | FLOAT | 客場勝出賠率 | `odds_away` |
| `odds_draw` | FLOAT | 平局賠率（可能為 null） | `odds_draw` |
| `implied_prob_sum` | FLOAT | 隱含機率總和 S = Σ(1/odds) | `implied_prob_sum` |
| `roi` | FLOAT | ROI = 1/S - 1 | `roi` |
| `latency_ms` | FLOAT | API 回應延遲（毫秒） | `latency_ms` |
| `is_valid` | INT | 資料有效性（1/0） | `is_valid` |
| `anomaly_flag` | INT | 異常標記（1/0） | `anomaly_flag` |
| `anomaly_reason` | TEXT | 異常判定說明 | `anomaly_reason` |
| `stability_score` | FLOAT | 數據源穩定性分數（0–1） | `stability_score` |
| `has_arb_opportunity` | INT | 是否有正 ROI 機會（1/0） | `has_arb_opportunity` |

---

### 2.2 Dimension Table：`dim_match`（賽事維度）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `match_id` | TEXT (PK) | The Odds API 賽事唯一識別碼 |
| `home_team` | TEXT | 主場隊伍 |
| `away_team` | TEXT | 客場隊伍 |
| `sport` | TEXT | 運動類型（e.g., basketball_nba） |
| `commence_time` | DATETIME | 賽事開始時間（UTC） |
| `display_name` | TEXT | 顯示名稱（衍生：home vs away） |

---

### 2.3 Dimension Table：`dim_platform`（博彩平台維度）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `platform_id` | TEXT (PK) | 平台識別碼（e.g., draftkings） |
| `platform_name` | TEXT | 顯示名稱（e.g., DraftKings） |
| `region` | TEXT | 主要市場（us / uk / eu / au） |

> **Note**：`dim_platform` 需手動維護或從 The Odds API 的 `/sports` 端點擴充。

---

### 2.4 Dimension Table：`dim_date`（時間維度）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `date_id` | INT (PK) | 格式：YYYYMMDDHH（e.g., 2025060112） |
| `full_datetime` | DATETIME | 完整時間戳 |
| `year` | INT | 年 |
| `month` | INT | 月（1–12） |
| `day` | INT | 日（1–31） |
| `hour` | INT | 小時（0–23） |
| `day_of_week` | TEXT | 星期幾（Monday–Sunday） |
| `is_weekend` | INT | 是否為週末（1/0） |

---

## 三、Power BI 匯入步驟

### 方法 A：直接連接 SQLite（推薦）

1. 下載並安裝 [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/)
2. 在 Power BI Desktop：**取得資料 → ODBC → 選擇已設定的 SQLite DSN**
3. 選擇 `odds_snapshots` 資料表，點選「轉換資料」
4. 在 Power Query 中加入計算欄：
   ```
   date_id = Int64.From(
       Text.From(Date.Year([timestamp])) &
       Text.PadStart(Text.From(Date.Month([timestamp])), 2, "0") &
       Text.PadStart(Text.From(Date.Day([timestamp])), 2, "0") &
       Text.PadStart(Text.From(Time.Hour([timestamp])), 2, "0")
   )
   ```

### 方法 B：CSV 匯入

1. 執行 `python main.py --mode analyze` 產生 CSV
2. Power BI Desktop：**取得資料 → 文字/CSV**
3. 選擇 `output/odds_snapshot_<timestamp>.csv`

---

## 四、建議 DAX 量值與視覺化

### 4.1 核心量值

```dax
-- 正 ROI 套利機會數量
Arb Opportunities Count =
    CALCULATE(
        COUNTROWS(fact_odds_snapshot),
        fact_odds_snapshot[has_arb_opportunity] = 1
    )

-- 平均 ROI（百分比）
Avg ROI % =
    AVERAGE(fact_odds_snapshot[roi]) * 100

-- 最高 ROI（百分比）
Max ROI % =
    MAX(fact_odds_snapshot[roi]) * 100

-- 異常率（異常點 / 總有效記錄）
Anomaly Rate % =
    DIVIDE(
        CALCULATE(
            COUNTROWS(fact_odds_snapshot),
            fact_odds_snapshot[anomaly_flag] = 1
        ),
        CALCULATE(
            COUNTROWS(fact_odds_snapshot),
            fact_odds_snapshot[is_valid] = 1
        )
    ) * 100

-- 平均數據源穩定性分數
Avg Stability Score =
    AVERAGE(fact_odds_snapshot[stability_score])

-- 最新快照時間（用於 KPI 卡片）
Latest Snapshot =
    MAX(dim_date[full_datetime])
```

### 4.2 建議視覺化配置

```
報告頁面 1：套利機會儀表板
├── KPI 卡片：正 ROI 機會數、最高 ROI、平均隱含機率總和
├── 折線圖：ROI 時間序列（X 軸：timestamp，Y 軸：roi，圖例：match_id）
│           異常點以「條件格式」標記為紅色圓點
│           → 使用 anomaly_flag = 1 作為條件
├── 矩陣表：賽事 × 平台 的賠率比較
└── 散佈圖：implied_prob_sum vs roi（顏色：運動類型）

報告頁面 2：數據品質稽核
├── 量測計：有效記錄比例（is_valid）
├── 堆疊長條圖：各平台的 anomaly_flag 比例
├── 折線圖：stability_score 時間趨勢（各平台分色）
│           穩定性 < 0.3 的區間以參考線標記
└── 資料表：異常記錄清單（含 anomaly_reason，可篩選）

報告頁面 3：平台效率比較
├── 雷達圖：各平台的 avg_odds_home、avg_odds_away、avg_stability
├── 盒鬚圖：各平台的 ROI 分佈
└── 熱力圖：賽事 × 平台的 implied_prob_sum（顏色越深 = 機率越高 = 賠率越差）
```

### 4.3 時間序列異常點標記（詳細步驟）

1. 在折線圖上加入「分析」→「固定參考線」（Y = 0，ROI 零線）
2. 新增「散佈圖」視覺效果，資料點設定：
   - X 軸：`timestamp`
   - Y 軸：`roi`
   - 顏色飽和度：`anomaly_flag`（0=藍色，1=紅色）
3. 或使用「條件格式」→「依欄位值」，將 `anomaly_flag = 1` 的資料點設為紅色

---

## 五、關聯鍵設定

在 Power BI Desktop「模型檢視」中建立以下關聯：

| 關聯 | 基數 | 方向 |
|------|------|------|
| `fact_odds_snapshot[match_id]` → `dim_match[match_id]` | 多對一 | 單向 |
| `fact_odds_snapshot[platform_id]` → `dim_platform[platform_id]` | 多對一 | 單向 |
| `fact_odds_snapshot[date_id]` → `dim_date[date_id]` | 多對一 | 單向 |

---

## 六、速率限制策略說明（如何確保不超過每月 500 次）

### 機制設計

```
每月 500 次 API 呼叫預算分配策略：

1. 持久化計數器（RateLimitState）
   └─ 程式重啟後仍保留本月已用次數
   └─ 偵測月份切換，自動重置計數器

2. 動態每日預算公式
   └─ 今日上限 = ceil(剩餘額度 / 月底剩餘天數)
   └─ 例：月初第 1 天：ceil(500/31) = 17 次/天
   └─     月中第 15 天：若已用 200 次 → ceil(300/16) = 19 次/天

3. 安全緩衝（預設 10%）
   └─ 用量超過 450/500 = 90% 時記錄 WARNING
   └─ 用量達 500/500 = 100% 時阻止請求，拋出 RuntimeError

4. 請求間隔（預設 2 秒）
   └─ 每次呼叫之間強制等待，避免突發式消耗

5. Header 回饋
   └─ The Odds API 在 Response Header 回傳 x-requests-remaining
   └─ 系統同步記錄，提供交叉驗證
```

### 典型每月用量估算

| 模式 | 運動項目數 | 輪詢間隔 | 每日呼叫 | 每月呼叫 |
|------|-----------|---------|---------|---------|
| 輕量研究 | 2 | 每 2 小時 | 24 次 | ~720 次 ❌ 超標 |
| 輕量研究 | 1 | 每 3 小時 | 8 次 | ~240 次 ✅ |
| 稽核用途 | 3 | 每 6 小時 | 12 次 | ~360 次 ✅ |
| 保守模式 | 2 | 每 12 小時 | 4 次 | ~120 次 ✅ |

> **建議**：免費方案（500 次/月）下，使用 `--mode single` 手動執行，或設定 `POLLING_INTERVAL_SECONDS=21600`（6 小時），搭配 2 個運動項目，可確保不超標。
