# -*- coding: utf-8 -*-
"""
scenario_config.py — 企業數位韌性系統三大情境數據配置
"""

SCENARIOS = {
    "scenario_1": {
        "carbon_intensity": 0.52,
        "user_id": "EMP-1024",
        "event_log": "生產線警報：C線 SMT 區發生製程異常，當班良率自平均 98.5% 急遽跌至 82.1%，低於公司內部合規標準門檻 85%，觸發 SOP-PROD-001 生產合規稽核流程。",
        "department": "生產部-SMT區",
        "shift": "A班",
        "equipment_id": "SMT-LINE-C",
        "production_yield": 82.1
    },
    "scenario_2": {
        "carbon_intensity": 0.45,
        "user_id": "unknown.user",
        "event_log": "SIEM資安告警：於凌晨 02:30 偵測到研發伺服器遭受來自海外不明來源之 15 次連續登入失敗嘗試，隨後有高達 5GB 的敏感專利代碼與合規文件遭異常下載導出，觸發 ISO 27001 A.8.16 資訊安全事件響應與審計。",
        "department": "研發部",
        "shift": "C班",
        "equipment_id": "SERVER-RND-01",
        "production_yield": 99.8
    },
    "scenario_3": {
        "carbon_intensity": 24.75,
        "user_id": "EHS_Auditor",
        "event_log": "EHS系統警報：二廠當日電力消耗高達 50 萬度，合計產出 1 萬件產品，換算碳排放強度達 24.75 kgCO₂e/unit，已超標 15%，觸發 ISO 14064-1 溫室氣體盤查與矯正預警程序。",
        "department": "製造二廠",
        "shift": "B班",
        "equipment_id": "FACTORY-02",
        "production_yield": 98.2
    }
}
