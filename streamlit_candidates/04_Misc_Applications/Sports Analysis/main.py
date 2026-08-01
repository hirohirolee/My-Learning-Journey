import streamlit as st
st.title('main.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
main.py - 市場套利分析與資訊效率稽核系統 主入口

【asyncio 設計決策】
本系統使用同步 `requests` 作為 HTTP 客戶端，並透過
`loop.run_in_executor()` 將阻塞式 I/O 包裝為非同步任務，
而非採用 `aiohttp`。

選擇理由：
1. The Odds API 的速率限制要求每次請求之間有明確間隔，並發請求意義不大。
2. `requests` 的同步介面更易於測試（Mock）、除錯與指數退避重試實作。
3. `run_in_executor()` 讓我們在需要並發其他非阻塞任務時（如計時器、
   日誌寫入），仍能保持事件迴圈響應，而不需要重寫整個 HTTP 層。
4. 若未來需要高並發（多 API 端點同時請求），可將此模組無縫替換為 aiohttp。

執行模式：
  python main.py --mode single       # 單輪抓取 + 分析 + 匯出
  python main.py --mode poll         # 持續輪詢模式（Ctrl+C 停止）
  python main.py --mode analyze      # 僅分析現有 DB 資料並匯出
  python main.py --mode status       # 顯示 API 額度狀態
"""

import argparse
import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from config import get_config, setup_logging
from data_provider import OddsApiClient, OddsRecord
from data_warehouse import OddsDatabase
from analysis_engine import ArbitrageAnalyzer

# 全域停止事件（用於優雅地終止輪詢迴圈）
_stop_event = asyncio.Event()


def _handle_signal(signum: int, frame) -> None:
    """捕捉 SIGINT / SIGTERM，設定停止事件以優雅結束輪詢。"""
    logger = logging.getLogger(__name__)
    logger.info("收到停止信號（%d），正在優雅地關閉系統...", signum)
    _stop_event.set()


# ---------------------------------------------------------------------------
# 非同步核心任務
# ---------------------------------------------------------------------------

async def fetch_and_store(
    client: OddsApiClient,
    db: OddsDatabase,
    sport_keys: list[str],
    executor: ThreadPoolExecutor,
    loop: asyncio.AbstractEventLoop
) -> dict[str, int]:
    """
    非同步包裝器：在執行緒池中呼叫同步 API，避免阻塞事件迴圈。

    流程：
    1. 對每個 sport_key 呼叫 OddsApiClient.get_odds()（透過 executor）
    2. 將結果寫入 SQLite（透過 executor）
    3. 回傳本輪寫入統計

    Args:
        client:     OddsApiClient 實例
        db:         OddsDatabase 實例
        sport_keys: 要抓取的運動項目列表
        executor:   ThreadPoolExecutor（避免每次創建新執行緒）
        loop:       當前事件迴圈

    Returns:
        寫入統計 dict（inserted, invalid, duplicate）
    """
    logger = logging.getLogger(__name__)
    all_records: list[OddsRecord] = []

    for sport_key in sport_keys:
        try:
            logger.info("正在抓取 %s 賠率...", sport_key)
            records = await loop.run_in_executor(
                executor,
                lambda sk=sport_key: client.get_odds(sk)
            )
            all_records.extend(records)
            logger.info("✓ %s：取得 %d 筆記錄", sport_key, len(records))
        except RuntimeError as exc:
            # 月額度耗盡時停止整個抓取流程
            logger.error("API 額度錯誤，停止本輪抓取：%s", exc)
            break
        except Exception as exc:
            logger.error("抓取 %s 失敗：%s", sport_key, exc)

    if not all_records:
        logger.warning("本輪未取得任何賠率記錄。")
        return {"inserted": 0, "invalid": 0, "duplicate": 0}

    # 在執行緒池中執行 SQLite 寫入（避免阻塞事件迴圈）
    stats = await loop.run_in_executor(
        executor,
        lambda: db.insert_records(all_records)
    )
    return stats


async def run_analysis_and_export(
    db: OddsDatabase,
    analyzer: ArbitrageAnalyzer,
    executor: ThreadPoolExecutor,
    loop: asyncio.AbstractEventLoop
) -> tuple[str, str]:
    """
    非同步包裝器：執行分析並匯出結果。

    Args:
        db:       OddsDatabase 實例
        analyzer: ArbitrageAnalyzer 實例
        executor: ThreadPoolExecutor
        loop:     當前事件迴圈

    Returns:
        (csv_path, markdown_path) 元組
    """
    logger = logging.getLogger(__name__)

    # 在執行緒池中讀取 DB（可能涉及大量 I/O）
    records = await loop.run_in_executor(
        executor,
        lambda: db.fetch_all(valid_only=True)
    )

    if not records:
        logger.warning("資料庫中無有效記錄，跳過分析。")
        return "", ""

    logger.info("載入 %d 筆記錄，開始分析...", len(records))

    # 分析（CPU 密集，在執行緒池中執行）
    def _analyze() -> tuple[str, str]:
        df = analyzer.analyze(records)
        arb_opportunities = analyzer.get_arbitrage_opportunities(df)
        csv_path = analyzer.export_for_powerbi(df)
        md_path = analyzer.export_markdown_report(df, arb_opportunities)
        return csv_path, md_path

    csv_path, md_path = await loop.run_in_executor(executor, _analyze)
    logger.info("分析完成 → CSV: %s | Markdown: %s", csv_path, md_path)
    return csv_path, md_path


# ---------------------------------------------------------------------------
# 執行模式
# ---------------------------------------------------------------------------

async def run_single(
    client: OddsApiClient,
    db: OddsDatabase,
    analyzer: ArbitrageAnalyzer,
    sport_keys: list[str]
) -> None:
    """
    單輪執行模式：抓取一次 → 儲存 → 分析 → 匯出。

    Args:
        client:     OddsApiClient
        db:         OddsDatabase
        analyzer:   ArbitrageAnalyzer
        sport_keys: 運動項目列表
    """
    logger = logging.getLogger(__name__)
    logger.info("═" * 60)
    logger.info("  單輪執行模式啟動")
    logger.info("═" * 60)

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        # Step 1: 抓取並儲存
        stats = await fetch_and_store(client, db, sport_keys, executor, loop)
        logger.info("寫入統計：%s", stats)

        # Step 2: 分析並匯出
        csv_path, md_path = await run_analysis_and_export(
            db, analyzer, executor, loop
        )

    # Step 3: 顯示 API 額度狀態
    quota = client.get_remaining_quota()
    logger.info(
        "API 額度狀態：本月已用 %d/%d 次（%.1f%%），今日建議上限 %d 次。",
        quota["calls_this_month"], quota["monthly_quota"],
        quota["usage_ratio_pct"], quota["daily_budget"]
    )

    # Step 4: 顯示資料庫摘要
    summary = db.get_summary_stats()
    logger.info("資料庫摘要：%s", summary)

    st.write(f"\n✅ 執行完成！")
    if csv_path:
        st.write(f"   📊 Power BI CSV：{csv_path}")
    if md_path:
        st.write(f"   📋 分析報告：{md_path}")


async def run_poll(
    client: OddsApiClient,
    db: OddsDatabase,
    analyzer: ArbitrageAnalyzer,
    sport_keys: list[str],
    interval_seconds: float
) -> None:
    """
    持續輪詢模式：每隔 interval_seconds 秒執行一輪抓取 + 分析。

    透過 asyncio.Event 實現優雅終止（Ctrl+C 或 SIGTERM）。
    每輪執行時間不計入間隔（若執行時間超過間隔，下一輪立即開始）。

    Args:
        client:           OddsApiClient
        db:               OddsDatabase
        analyzer:         ArbitrageAnalyzer
        sport_keys:       運動項目列表
        interval_seconds: 輪詢間隔（秒）
    """
    logger = logging.getLogger(__name__)
    logger.info("═" * 60)
    logger.info("  持續輪詢模式啟動（間隔：%.0f 秒）", interval_seconds)
    logger.info("  按 Ctrl+C 可優雅停止")
    logger.info("═" * 60)

    loop = asyncio.get_event_loop()
    round_num = 0

    with ThreadPoolExecutor(max_workers=1) as executor:
        while not _stop_event.is_set():
            round_num += 1
            round_start = datetime.utcnow()
            logger.info("--- 輪詢第 %d 輪（%s UTC）---", round_num,
                        round_start.strftime("%H:%M:%S"))

            try:
                stats = await fetch_and_store(
                    client, db, sport_keys, executor, loop
                )
                logger.info("第 %d 輪寫入完成：%s", round_num, stats)

                await run_analysis_and_export(db, analyzer, executor, loop)

            except Exception as exc:
                logger.error("第 %d 輪執行失敗：%s", round_num, exc)

            # 顯示額度狀態
            quota = client.get_remaining_quota()
            logger.info(
                "額度狀態：%d/%d 次已用（%.1f%%）。",
                quota["calls_this_month"], quota["monthly_quota"],
                quota["usage_ratio_pct"]
            )

            # 等待下一輪（可被停止事件中斷）
            elapsed = (datetime.utcnow() - round_start).total_seconds()
            remaining_wait = max(0.0, interval_seconds - elapsed)
            logger.info(
                "本輪耗時 %.1f 秒，下一輪等待 %.1f 秒...",
                elapsed, remaining_wait
            )

            try:
                await asyncio.wait_for(
                    _stop_event.wait(), timeout=remaining_wait
                )
                break  # 停止事件被設定
            except asyncio.TimeoutError:
                continue  # 正常等待完成，進入下一輪

    logger.info("輪詢模式已停止。")


async def run_analyze_only(
    db: OddsDatabase,
    analyzer: ArbitrageAnalyzer
) -> None:
    """
    僅分析模式：讀取現有 DB 資料，執行分析並匯出，不抓取新資料。

    Args:
        db:       OddsDatabase
        analyzer: ArbitrageAnalyzer
    """
    logger = logging.getLogger(__name__)
    logger.info("═" * 60)
    logger.info("  僅分析模式啟動")
    logger.info("═" * 60)

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        csv_path, md_path = await run_analysis_and_export(
            db, analyzer, executor, loop
        )

    st.write(f"\n✅ 分析完成！")
    if csv_path:
        st.write(f"   📊 Power BI CSV：{csv_path}")
    if md_path:
        st.write(f"   📋 分析報告：{md_path}")


async def run_status(client: OddsApiClient, db: OddsDatabase) -> None:
    """
    顯示 API 額度與資料庫狀態摘要（不消耗額度）。

    Args:
        client: OddsApiClient
        db:     OddsDatabase
    """
    quota = client.get_remaining_quota()
    summary = db.get_summary_stats()

    st.write("\n" + "═" * 50)
    st.write("  系統狀態摘要")
    st.write("═" * 50)
    st.write(f"  月份：        {quota['month_key']}")
    st.write(f"  月額度：      {quota['monthly_quota']} 次")
    st.write(f"  已用次數：    {quota['calls_this_month']} 次（{quota['usage_ratio_pct']:.1f}%）")
    st.write(f"  剩餘次數：    {quota['remaining_quota']} 次")
    st.write(f"  今日建議上限：{quota['daily_budget']} 次")
    st.write("─" * 50)
    st.write(f"  DB 總記錄：   {summary['total_records']:,} 筆")
    st.write(f"  有效記錄：    {summary['valid_records']:,} 筆")
    st.write(f"  無效記錄：    {summary['invalid_records']:,} 筆")
    st.write(f"  運動項目：    {', '.join(summary['sports']) or '(無資料)'}")
    st.write(f"  覆蓋平台：    {len(summary['platforms'])} 個")
    st.write(f"  最新資料：    {summary['latest_timestamp'] or '(無資料)'}")
    st.write("═" * 50)


# ---------------------------------------------------------------------------
# CLI 參數解析
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """解析命令列參數。"""
    parser = argparse.ArgumentParser(
        description="市場套利分析與資訊效率稽核系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
執行範例：
  python main.py --mode single                    # 單輪執行
  python main.py --mode poll --interval 300       # 每 5 分鐘輪詢
  python main.py --mode analyze                   # 僅分析現有資料
  python main.py --mode status                    # 查看 API 額度狀態
  python main.py --mode single --sports basketball_nba soccer_epl
        """
    )
    parser.add_argument(
        "--mode",
        choices=["single", "poll", "analyze", "status"],
        default="single",
        help="執行模式（預設：single）"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="輪詢間隔（秒），僅 poll 模式有效（覆蓋 .env 設定）"
    )
    parser.add_argument(
        "--sports",
        nargs="+",
        default=None,
        help="指定要抓取的運動項目（空格分隔，e.g., basketball_nba soccer_epl）"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# 主函式
# ---------------------------------------------------------------------------

async def main() -> None:
    """應用程式主入口。"""
    # 1. 載入設定
    config = get_config()
    setup_logging(config.logging)

    logger = logging.getLogger(__name__)
    logger.info("市場套利分析與資訊效率稽核系統 啟動")

    # 2. 解析 CLI 參數
    args = parse_args()

    # 3. 初始化元件
    client = OddsApiClient(
        config=config.api,
        state_file="./data/rate_limit_state.json"
    )
    db = OddsDatabase(
        db_path=config.database.db_path,
        min_valid_odds=config.database.min_valid_odds,
        max_valid_odds=config.database.max_valid_odds
    )
    analyzer = ArbitrageAnalyzer(
        anomaly_threshold_sigma=config.analysis.anomaly_threshold_sigma,
        stability_window_minutes=config.analysis.stability_window_minutes,
        min_roi_threshold=config.analysis.min_roi_threshold,
        csv_output_dir=config.analysis.csv_output_dir,
        markdown_output_path=config.analysis.markdown_output_path
    )

    # 4. 預設運動項目（若未由 CLI 指定）
    # 常用項目：basketball_nba, americanfootball_nfl, soccer_epl,
    #           baseball_mlb, icehockey_nhl
    sport_keys = args.sports or [
        "basketball_nba",
        "americanfootball_nfl",
        "soccer_epl"
    ]

    # 5. 設定信號處理（優雅停止）
    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    # 6. 執行指定模式
    try:
        if args.mode == "single":
            await run_single(client, db, analyzer, sport_keys)

        elif args.mode == "poll":
            interval = args.interval or config.polling.polling_interval_seconds
            await run_poll(client, db, analyzer, sport_keys, interval)

        elif args.mode == "analyze":
            await run_analyze_only(db, analyzer)

        elif args.mode == "status":
            await run_status(client, db)

    except KeyboardInterrupt:
        logger.info("使用者中斷，系統關閉。")
    except Exception as exc:
        logger.critical("系統發生未預期錯誤：%s", exc, exc_info=True)
        sys.exit(1)

    logger.info("系統正常關閉。")


if __name__ == "__main__":
    asyncio.run(main())
