import streamlit as st
st.title('config.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
from dataclasses import dataclass
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict

@dataclass(frozen=True)
class ASICSpecs:
    """比特幣挖礦 ASIC 硬體的規格參數。"""
    name: str
    hashrate_th: float  # 算力，單位為每秒太拉雜湊 (TH/s)
    power_watts: float  # 功耗，單位為瓦特 (W)
    efficiency_j_th: float  # 能效比，單位為焦耳/太拉雜湊 (J/TH)
    release_year: int
    typical_price_usd: float

# 預先載入的標準 ASIC 礦機規格數據庫
ASIC_DATABASE: Dict[str, ASICSpecs] = {
    "Antminer S21 Hyd": ASICSpecs(
        name="Antminer S21 Hyd",
        hashrate_th=335.0,
        power_watts=5360.0,
        efficiency_j_th=16.0,
        release_year=2024,
        typical_price_usd=5700.0,
    ),
    "Antminer S21": ASICSpecs(
        name="Antminer S21",
        hashrate_th=200.0,
        power_watts=3500.0,
        efficiency_j_th=17.5,
        release_year=2024,
        typical_price_usd=4000.0,
    ),
    "Antminer S19 XP": ASICSpecs(
        name="Antminer S19 XP",
        hashrate_th=141.0,
        power_watts=3030.0,
        efficiency_j_th=21.5,
        release_year=2022,
        typical_price_usd=2800.0,
    ),
    "WhatsMiner M60S": ASICSpecs(
        name="WhatsMiner M60S",
        hashrate_th=186.0,
        power_watts=3441.0,
        efficiency_j_th=18.5,
        release_year=2023,
        typical_price_usd=3900.0,
    ),
    "WhatsMiner M60": ASICSpecs(
        name="WhatsMiner M60",
        hashrate_th=170.0,
        power_watts=3383.0,
        efficiency_j_th=19.9,
        release_year=2023,
        typical_price_usd=3100.0,
    ),
    "Avalon A1566": ASICSpecs(
        name="Avalon A1566",
        hashrate_th=185.0,
        power_watts=3422.0,
        efficiency_j_th=18.5,
        release_year=2024,
        typical_price_usd=3200.0,
    ),
    "Avalon A1466": ASICSpecs(
        name="Avalon A1466",
        hashrate_th=150.0,
        power_watts=3225.0,
        efficiency_j_th=21.5,
        release_year=2023,
        typical_price_usd=2200.0,
    ),
}

class Settings(BaseSettings):
    """從環境變數載入的應用程式設定與 API 配置。"""
    
    # API 連結地址
    MEMPOOL_SPACE_URL: str = "https://mempool.space/api"
    BLOCKCHAIN_INFO_URL: str = "https://blockchain.info"
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3"
    
    # API 快取與重試次數
    API_CACHE_TTL_SEC: int = 300  # 5 分鐘
    API_MAX_RETRIES: int = 3
    API_TIMEOUT_SEC: int = 10
    
    # 硬編碼回退值（當 API 斷線時使用）
    FALLBACK_BTC_PRICE_USD: float = 95000.0
    FALLBACK_DIFFICULTY: float = 90_000_000_000_000.0
    FALLBACK_HASHRATE_EH: float = 650.0
    FALLBACK_BLOCK_HEIGHT: int = 850000
    FALLBACK_BLOCK_REWARD: float = 3.125
    FALLBACK_TX_FEES_BTC: float = 0.15
    
    # 應用程式配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    DEFAULT_SIMULATION_COUNT: int = 10000
    MAX_SIMULATION_COUNT: int = 100000
    
    # 減半區塊間隔
    HALVING_INTERVAL_BLOCKS: int = 210000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# 實例化配置對象
settings = Settings()
