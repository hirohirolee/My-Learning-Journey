# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - GRI 揭露指標與子項目全域配置表
"""

from typing import Dict, Any

# GRI 揭露指標全域配置表，包含指標編號、名稱、檔案鍵名、Excel 解析函數、以及 Ollama Fallback 函數的對照關係
GRI_CONFIG: Dict[str, Dict[str, Any]] = {
    "GRI 305": {
        "code": "305",
        "name": "GRI 305: 溫室氣體排放 (Emissions)",
        "help": "統計範疇一與範疇二碳排放",
        "tab_index": 0, # Tab 0: GRI 305 & 404
        "processor_method": "process_environmental_excel",
        "file_key": "env_upload",
        "template_key": "env",
        "baseline_required": True,
        "sub_items": {
            "3.1.1": {
                "title": "3.1.1 範疇一（直接溫室氣體排放）來源與數據深度解讀",
                "label": "├─ 3.1.1 範疇一（直接排放）來源與數據解讀",
                "default": True,
                "instruction": "深入分析範疇一（直接排放）所涵蓋之所有排放源別（如柴油發電機、冷媒逸散等）的具體數值與占比。說明這些來源的製程本質、盤查結果，以及企業針對直接逸散所推動的常規維護措施與控制政策。"
            },
            "3.1.2": {
                "title": "3.1.2 範疇二（能源間接溫室氣體排放）外購電力分析與減碳路徑",
                "label": "├─ 3.1.2 範疇二（間接排放）電力分析與路徑",
                "default": True,
                "instruction": "深入分析範疇二（間接排放，主要是外購電力）的具體數值與占比。說明外購電力作為企業主要間接排放源的環境衝擊，並闡述綠電採購規劃、廠區節能設備改造、智慧能源管理等具體能效改善與減量路徑。"
            },
            "3.1.3": {
                "title": "3.1.3 年度排放變動率（YoY）與減量成效評估",
                "label": "└─ 3.1.3 年度排放變動率（YoY）與成效評估",
                "default": True,
                "instruction": "分析溫室氣體排放總量相較於基準年度 (或前年度) 的變動率 (YoY)。結合變動百分比，對本年度 the 減碳成效進行量化與質性評估，說明製程優化或減量計畫的實質成效，並闡述下一階段減碳路徑目標。"
            }
        },
        "fallback_method": "_get_gri_305_subchapters_fallback"
    },
    "GRI 404": {
        "code": "404",
        "name": "GRI 404: 培訓與教育 (Training)",
        "help": "統計平均培訓時數與留才機制",
        "tab_index": 0, # Tab 0: GRI 305 & 404
        "processor_method": "process_social_excel",
        "file_key": "soc_upload",
        "template_key": "soc",
        "baseline_required": False,
        "sub_items": {
            "4.1.1": {
                "title": "4.1.1 員工平均培訓時數結構分析（依職級與性別）",
                "label": "├─ 4.1.1 員工平均培訓時數結構分析",
                "default": True,
                "instruction": "深入分析各職級員工（高階主管、中階主管、基層員工）及不同性別員工（男性、女性）的平均培訓時數與統計表現，說明企業在教育資源分配的均衡性，以及在落實內部職涯能力培育上的承諾與數據成果。"
            },
            "4.1.2": {
                "title": "4.1.2 員工技能提升與過渡協助計畫執行效益",
                "label": "├─ 4.1.2 員工技能提升與成長規畫效益",
                "default": True,
                "instruction": "探討企業如何透過持續的培訓課程及技能提升計畫，協助同仁因應數位轉型、AI 製程優化等職涯技能變動，並闡述這類培訓與技能重建方案對組織韌性、長期留任與企業永續競爭力帶來的實質效益。"
            },
            "4.1.3": {
                "title": "4.1.3 組織人才穩定度與流動率指標解讀",
                "label": "└─ 4.1.3 組織人才穩定度與流動率解讀",
                "default": True,
                "instruction": "分析新進員工比率與員工離職率等指標數據。說明人才流動對組織穩定度、團隊凝聚力與長期營運效益的影響，並簡述企業在留才機制、升遷管道優化及友善職場工作氛圍上的具體方向與政策。"
            }
        },
        "fallback_method": "_get_gri_404_subchapters_fallback"
    },
    "GRI 302": {
        "code": "302",
        "name": "GRI 302: 能源消耗 (Energy)",
        "help": "統計柴油、電力等能源耗用與能效分析",
        "tab_index": 1, # Tab 1: GRI 302 & 306
        "processor_method": "process_energy_excel",
        "file_key": "energy_upload",
        "template_key": "energy",
        "baseline_required": False,
        "sub_items": {
            "3.2.1": {
                "title": "3.2.1 組織內部能源消耗數據解讀",
                "label": "├─ 3.2.1 組織內部能源消耗數據解讀",
                "default": True,
                "instruction": "深入分析組織內部的所有能源消耗數據（如外購電力、柴油、汽油消耗等）的具體數值與占比。說明這些能源耗用的製程或營運本質，並解讀本年度總體能源耗用的統計表現。"
            },
            "3.2.2": {
                "title": "3.2.2 能源密集度與節能減量成效",
                "label": "└─ 3.2.2 能源密集度與節能減量成效",
                "default": True,
                "instruction": "說明組織的能源密集度表現。闡述企業在提升能源效率、落實節電改造措施（如照明與空調系統升級、變頻改造）及降低能源消耗強度上的承諾與具體減量成效。"
            }
        },
        "fallback_method": "_get_gri_302_subchapters_fallback"
    },
    "GRI 306": {
        "code": "306",
        "name": "GRI 306: 廢棄物與回收 (Waste)",
        "help": "統計廢棄物產生與流向管理",
        "tab_index": 1, # Tab 1: GRI 302 & 306
        "processor_method": "process_waste_excel",
        "file_key": "waste_upload",
        "template_key": "waste",
        "baseline_required": False,
        "sub_items": {
            "3.6.1": {
                "title": "3.6.1 廢棄物產生源與源頭減量措施",
                "label": "├─ 3.6.1 廢棄物產生源與源頭減量措施",
                "default": True,
                "instruction": "說明組織在營運與生產過程中所產生的廢棄物來源（包含有害事業廢棄物與一般事業廢棄物）。闡述企業的廢棄物減量目標與源頭管理、包裝減塑等具體減量措施。"
            },
            "3.6.2": {
                "title": "3.6.2 廢棄物回收與循環再利用效益",
                "label": "├─ 3.6.2 廢棄物回收與循環再利用效益",
                "default": True,
                "instruction": "分析廢棄物的回收率與資源化再利用數據。說明企業如何推動垃圾分類、廢料回收再利用，以及邁向循環經濟、綠色設計之具體成效。"
            },
            "3.6.3": {
                "title": "3.6.3 廢棄物最終處置與合規評估",
                "label": "└─ 3.6.3 廢棄物最終處置與合規評估",
                "default": True,
                "instruction": "說明無法回收之廢棄物的最終處置方式（如委外焚化、衛生掩埋等）與處理量。闡明企業如何對委外清除處理機構進行合規審查與流向申報追蹤，確保符合環保法規要求。"
            }
        },
        "fallback_method": "_get_gri_306_subchapters_fallback"
    },
    "GRI 401": {
        "code": "401",
        "name": "GRI 401: 員工聘用與流動 (Employment)",
        "help": "統計新進員工與流動率指標",
        "tab_index": 2, # Tab 2: GRI 401 & 405
        "processor_method": "process_employment_excel",
        "file_key": "employment_upload",
        "template_key": "employment",
        "baseline_required": False,
        "sub_items": {
            "4.1.1.b": {
                "title": "4.1.1.b 員工流動率與新進率結構解讀",
                "label": "├─ 4.1.1.b 員工流動率與新進率結構解讀",
                "default": True,
                "instruction": "分析本年度新進員工與離職員工之總數、新進率及離職率數據。解讀此流動結構對組織人才儲備、營運穩定度及團隊活力所帶來的影響。"
            },
            "4.1.2": {
                "title": "4.1.2 關懷福利政策與育嬰留停成效",
                "label": "└─ 4.1.2 關懷福利政策與育嬰留停成效",
                "default": True,
                "instruction": "說明企業在吸引與留任人才上的各項福利政策與關懷措施，包括育嬰留职停薪、托兒補助、身心健康檢查及彈性工時等具體實踐與成效。"
            }
        },
        "fallback_method": "_get_gri_401_subchapters_fallback"
    },
    "GRI 405": {
        "code": "405",
        "name": "GRI 405: 多元與平等機會 (Diversity)",
        "help": "統計主管與基層性別及年齡結構占比",
        "tab_index": 2, # Tab 2: GRI 401 & 405
        "processor_method": "process_diversity_excel",
        "file_key": "diversity_upload",
        "template_key": "diversity",
        "baseline_required": False,
        "sub_items": {
            "4.5.1": {
                "title": "4.5.1 治理機構與員工結構多元化比例",
                "label": "├─ 4.5.1 治理機構與員工結構多元化比例",
                "default": True,
                "instruction": "分析治理機構（如董事會、高階管理層）與各級員工的多元化比例，特別是不同性別占比與年齡結構（30歲以下、30至50歲、50歲以上）。說明企業推動多元包容職場的承諾與數據成果。"
            },
            "4.5.2": {
                "title": "4.5.2 男女同工同酬與平等晉升機會",
                "label": "└─ 4.5.2 男女同工同酬與平等晉升機會",
                "default": True,
                "instruction": "說明企業如何維護職場平等機會，保障男女同工同酬、提供公正透明的績效考核與平等晉升管道，以消除 any 形式的職場性別歧視。"
            }
        },
        "fallback_method": "_get_gri_405_subchapters_fallback"
    },
    "GRI 201": {
        "code": "201",
        "name": "GRI 201: 經濟績效 (Economic Performance)",
        "help": "統計組織直接產出與分配的經濟價值",
        "tab_index": 3, # Tab 3: 經濟與治理
        "processor_method": "process_economic_excel",
        "file_key": "economic_upload",
        "template_key": "economic",
        "baseline_required": False,
        "sub_items": {
            "2.1.1": {
                "title": "2.1.1 直接產生與分配之經濟價值分析",
                "label": "├─ 2.1.1 直接產生與分配之經濟價值分析",
                "default": True,
                "instruction": "分析企業直接產生之經濟價值（營業收入）與分配之經濟價值（營運成本、員工薪資與福利、支付給出資人股利、支付公部門稅收及社區投資）及保留之經濟價值。說明如何透過合理的價值分配促進與所有持份者的共榮。"
            },
            "2.1.2": {
                "title": "2.1.2 氣候變遷對企業營運之財務衝擊",
                "label": "└─ 2.1.2 氣候變遷對企業營運之財務衝擊",
                "default": True,
                "instruction": "說明氣候變遷（如極端天氣、法規碳費等）對企業營運所帶來的潛在財務風險與機遇。闡明企業如何評估這些物理與轉型風險，並制定相應的適應性治理計畫。"
            }
        },
        "fallback_method": "_get_gri_201_subchapters_fallback"
    },
    "GRI 205": {
        "code": "205",
        "name": "GRI 205: 反貪腐 (Anti-corruption)",
        "help": "誠信經營守則宣導與貪腐風險評估",
        "tab_index": 3, # Tab 3: 經濟與治理
        "processor_method": "process_anti_corruption_excel",
        "file_key": "anti_corruption_upload",
        "template_key": "anti_corruption",
        "baseline_required": False,
        "sub_items": {
            "2.5.1": {
                "title": "2.5.1 反貪腐政策傳達、簽署與培訓統計",
                "label": "├─ 2.5.1 反貪腐政策傳達、簽署與培訓統計",
                "default": True,
                "instruction": "分析公司董事與員工在誠信經營與反貪腐守則的傳達、簽署率與培訓完成時數。說明企業如何對內建立誠信守則與反貪腐意識。"
            },
            "2.5.2": {
                "title": "2.5.2 誠信經營確立事件與檢舉防範機制",
                "label": "└─ 2.5.2 誠信經營確立事件與檢舉防範機制",
                "default": True,
                "instruction": "說明本年度是否發生 any 貪腐確立案件。闡述企業所建立的誠信經營檢舉管道（如匿名信箱、專線）及保護檢舉人的防護網機制與合規成效。"
            }
        },
        "fallback_method": "_get_gri_205_subchapters_fallback"
    },
    "GRI 2": {
        "code": "2",
        "name": "GRI 2: 一般揭露 (General Disclosures)",
        "help": "組織概況、報告實務與治理架構說明",
        "tab_index": 3, # Tab 3: 經濟與治理
        "processor_method": "process_general_disclosure_excel",
        "file_key": "general_upload",
        "template_key": "general",
        "baseline_required": False,
        "sub_items": {
            "2.2.1": {
                "title": "2.2.1 組織基本概況、據點與資本規模",
                "label": "├─ 2.2.1 組織基本概況、據點與資本規模",
                "default": True,
                "instruction": "說明企業之組織基本概況、營運據點分佈、主要產品與服務以及資本規模（實收資本額等）。展現企業的核心組織身分與業務版圖。"
            },
            "2.2.2": {
                "title": "2.2.2 商業活動與供應鏈價值關係",
                "label": "├─ 2.2.2 商業活動與供應鏈價值關係",
                "default": True,
                "instruction": "描述企業的主要商業活動與上下游供應鏈之價值關係，包含供應商管理政策、綠色採購方針，以及企業如何推動供應鏈之社會與環境合規責任。"
            },
            "2.2.3": {
                "title": "2.2.3 員工聘用特性與人力資源分佈",
                "label": "└─ 2.2.3 員工聘用特性與人力資源分佈",
                "default": True,
                "instruction": "分析企業員工總數及聘用特性（如全職、兼職、定期與不定期契約員工的性別與地區分布），說明企業人力資源的基本架構與穩定勞工關係政策。"
            }
        },
        "fallback_method": "_get_gri_2_subchapters_fallback"
    }
}
