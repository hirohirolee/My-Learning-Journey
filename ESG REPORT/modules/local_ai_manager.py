# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - 地端 AI 管理模組 (升級版)
"""

import os
import json
import ollama
import config

class ESGLLMManager:
    """
    調度地端 Ollama AI 進行符合 GRI 規範的永續報告書子章節文本撰寫與擴寫。
    """
    
    def __init__(self, model_name=None, host=None):
        self.model_name = model_name or config.MODEL_NAME
        self.host = host or config.OLLAMA_HOST
        
        # 初始化 Ollama 客戶端
        try:
            self.client = ollama.Client(host=self.host)
        except Exception as e:
            self.client = None
            print(f"⚠️ 初始化 Ollama 客戶端失敗，將使用預設的備用生成方案。錯誤原因: {e}")

    def generate_chapter_subsections(self, json_data, framework_code, target_words=350, selected_subs=None):
        """
        為特定的 GRI 框架代碼（GRI 305 或 GRI 404）分別生成三個核心子項文本。
        回傳字典： {"3.1.1": text_311, "3.1.2": text_312, ...}
        """
        framework_code = str(framework_code).strip().upper()
        results = {}
        
        # 定義各指標之子章節對照與 Prompt
        if "305" in framework_code:
            subs = {
                "3.1.1": {
                    "title": "3.1.1 範疇一（直接溫室氣體排放）來源與數據深度解讀",
                    "instruction": "深入分析範疇一（直接排放）所涵蓋之所有排放源別（如柴油發電機、冷媒逸散等）的具體數值與占比。說明這些來源的製程本質、盤查結果，以及企業針對直接逸散所推動的常規維護措施與控制政策。"
                },
                "3.1.2": {
                    "title": "3.1.2 範疇二（能源間接溫室氣體排放）外購電力分析與減碳路徑",
                    "instruction": "深入分析範疇二（間接排放，主要是外購電力）的具體數值與占比。說明外購電力作為企業主要間接排放源的環境衝擊，並闡述綠電採購規劃、廠區節能設備改造、智慧能源管理等具體能效改善與減量路徑。"
                },
                "3.1.3": {
                    "title": "3.1.3 年度排放變動率（YoY）與減量成效評估",
                    "instruction": "分析溫室氣體排放總量相較於基準年度 (或前年度) 的變動率 (YoY)。結合變動百分比，對本年度的減碳成效進行量化與質性評估，說明製程優化或減量計畫的實質成效，並闡述下一階段減碳路徑目標。"
                }
            }
            fallback_func = self._get_gri_305_subchapters_fallback
            
        elif "404" in framework_code:
            subs = {
                "4.1.1": {
                    "title": "4.1.1 員工平均培訓時數結構分析（依職級與性別）",
                    "instruction": "深入分析各職級員工（高階主管、中階主管、基層員工）及不同性別員工（男性、女性）的平均培訓時數與統計表現，說明企業在教育資源分配的均衡性，以及在落實內部職涯能力培育上的承諾與數據成果。"
                },
                "4.1.2": {
                    "title": "4.1.2 員工技能提升與過渡協助計畫執行效益",
                    "instruction": "探討企業如何透過持續的培訓課程及技能提升計畫，協助同仁因應數位轉型、AI 製程優化等職涯技能變動，並闡述這類培訓與技能重建方案對組織韌性、長期留任與企業永續競爭力帶來的實質效益。"
                },
                "4.1.3": {
                    "title": "4.1.3 組織人才穩定度與流動率指標解讀",
                    "instruction": "分析新進員工比率與員工離職率等指標數據。說明人才流動對組織穩定度、團隊凝聚力與長期營運效益的影響，並簡述企業在留才機制、升遷管道優化及友善職場工作氛圍上的具體方向與政策。"
                }
            }
            fallback_func = self._get_gri_404_subchapters_fallback
            
        else:
            # 預設回退
            return {"無子章節": f"已收到數據：{json.dumps(json_data, ensure_ascii=False)}"}

        # 對各個子章節單獨進行 AI 生成
        for sub_id, info in subs.items():
            if selected_subs is not None and sub_id not in selected_subs:
                continue
            print(f"⏳ 正在生成地端 AI 子章節文本: {info['title']} ...")
            
            system_instruction = (
                "你是一位精通 GRI 準則與企業永續發展 (ESG) 實務的資深企業管理顧問。\n"
                f"你的任務是為企業永續報告書撰寫正式子章節內文：『{info['title']}』。\n\n"
                "【極重要強制指令】：\n"
                "1. 不論輸入與欄位為任何語言，你必須『完全使用繁體中文 (Traditional Chinese)』進行撰寫回答。報告書內文中絕對不能出現英文或簡體中文（除非是 GRI 專有名詞簡寫）！\n"
                f"2. 你必須依據使用者提供的 JSON 數據來撰寫。只能使用 JSON 中提及的數據，絕對不能憑空捏造、發明或修改任何數值。\n"
                "3. 報告語氣必須嚴謹、專業、客觀、高階經理人化，採取企業永續報告官方的官方第三人稱視角。\n"
                f"4. 本段字數請控制在 {target_words} 字左右。請直接輸出子章節的描述內文，絕對不要包含任何前言問候（如「好的，以下是您需要的...」）、結論問候、或解釋性自我對話。\n"
                f"5. 本段寫作的核心指示：{info['instruction']}"
            )
            
            user_prompt = f"請根據以下 JSON 數據寫作『{info['title']}』段落：\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
            
            # 呼叫地端 AI
            sub_text = ""
            if self.client is not None:
                try:
                    response = self.client.chat(
                        model=self.model_name,
                        messages=[
                            {'role': 'system', 'content': system_instruction},
                            {'role': 'user', 'content': user_prompt}
                        ]
                    )
                    sub_text = response['message']['content'].strip()
                except Exception as e:
                    print(f"❌ 呼叫 Ollama {self.model_name} 失敗。將對該子項啟用備用文本。錯誤: {e}")
                    sub_text = ""
            
            # 如果 AI 生成失敗或未連線，則調用本地高質量 Fallback
            if not sub_text:
                fallback_dict = fallback_func(json_data)
                sub_text = fallback_dict.get(sub_id, "")
                
            results[sub_id] = sub_text
            
        return results

    def _get_gri_305_subchapters_fallback(self, data):
        """GRI 305 的三個子章節備用高質量質化文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        em = data.get("emissions_data", {})
        
        scope_1_items = [f"「{k}」排放量為 {v} 公噸 CO2e" for k, v in em.get("scope_1_direct", {}).items() if k != "總計"]
        scope_1_total = em.get("scope_1_direct", {}).get("總計", 0.0)
        scope_2_items = [f"「{k}」排放量為 {v} 公噸 CO2e" for k, v in em.get("scope_2_indirect", {}).items() if k != "總計"]
        scope_2_total = em.get("scope_2_indirect", {}).get("總計", 0.0)
        total = em.get("total_emissions_tCO2e", 0.0)
        yoy = em.get("yoy_change_percentage", 0.0)
        
        yoy_text = f"減少了 {abs(yoy)}%" if yoy < 0 else f"增加了 {yoy}%"
        
        res = {
            "3.1.1": (
                f"依據 GRI 305 溫室氣體排放揭露準則，{company} 針對 {year} 年度的直接溫室氣體排放（範疇一）進行了精準的盤查工作。 "
                f"本公司的範疇一排放主要源自於營運廠區內的直接化石燃料燃燒與逸散源，經盤查明細包括：{', '.join(scope_1_items)}。 "
                f"範疇一合計直接排放量共計達到 {scope_1_total} 公噸 CO2e。 "
                f"本公司致力於源頭減量，已著手評估將老舊柴油發電機汰換為低排放機型，並定期實施冷媒洩漏檢測，確保範疇一直接排放量維持在最優化水平。"
            ),
            "3.1.2": (
                f"針對能源間接溫室氣體排放（範疇二），{company} 於 {year} 年度的排放源主要為營運廠區與辦公大樓之「外購電力」， "
                f"其外購電力間接碳排放量共計達 {scope_2_total} 公噸 CO2e。 "
                f"由於外購電力占本公司整體溫室氣體排放量之大宗，電力能效的控制與減量為本公司綠色轉型的核心工作。 "
                f"本公司目前正全面落實廠區照明與空調系統之節能改造，推廣智慧電網管理，並評估於廠區屋頂鋪設太陽能光電系統與採購再生能源憑證（綠電），以加速推動能源轉型，降低範疇二之環境負擔。"
            ),
            "3.1.3": (
                f"在年度排放變動分析方面，{company} 統計 {year} 年度的範疇一與範疇二溫室氣體排放總量共計為 {total} 公噸 CO2e。 "
                f"相較於基準年度，排放總量{yoy_text}，顯示本公司在落實能源節約與低碳營運轉型上取得實質進展。 "
                f"此項減碳成效源自跨部門小組協同合作，積極推動節能製程改善及低碳材料導入。 "
                f"本公司將持續深化低碳工藝的研發與再生能源之應用，健全低碳永續經營模式，朝向全球倡議之淨零碳排終極目標穩健前進。"
            )
        }
        return res

    def _get_gri_404_subchapters_fallback(self, data):
        """GRI 404 的三個子章節備用高質量質化文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        sd = data.get("social_data", {})
        tm = sd.get("training_metrics", {})
        to = sd.get("turnover_metrics", {})
        
        t_items = [f"「{k}」平均達 {v['value']} {v['unit']}" for k, v in tm.items()]
        to_items = [f"「{k}」為 {v['value']}{v['unit']}" for k, v in to.items()]
        
        res = {
            "4.1.1": (
                f"依據 GRI 404 培訓與教育揭露準則，{company} 深信持續提升員工專業知能是企業成長的關鍵。 "
                f"在 {year} 年度員工平均培訓時數的結構分析中，數據顯示：{', '.join(t_items)}。 "
                f"本公司針對高階主管、中階主管以及基層員工，因應其工作範疇與管理層級之不同，提供相應的學程培訓，同時確保性別平權與資源分配的均等。 "
                f"此數據充分顯現本公司在落實內部職涯技能輔導與組織核心能力建構上，皆維持高標準之投入。"
            ),
            "4.1.2": (
                f"為配合科技進步與產業快速轉型，{company} 於 {year} 年度積極推展多元化的員工技能提升與過渡協助計畫。 "
                f"我們除了舉辦內部專業工作坊、管理職特訓班之外，亦提供外部進修學費補助，以協助同仁在變動的市場中持續掌握前沿技能。 "
                f"這些培訓與技能重建方案，性能激發同仁的自我實現潛能，更有助於縮短新技術導入的學習曲線，提升公司的營運彈性與長期永續競爭力。"
            ),
            "4.1.3": (
                f"在人力結構穩定度指標方面，{company} 統計本報告年度之關鍵數據顯示：{', '.join(to_items)}。 "
                f"本公司高度重視新進員工之融入狀況以及核心關鍵人才的留任率。 "
                f"為健全組織活力，我們將深入解讀此人才流動指標，並配合員工回饋機制，著手優化整體薪酬待遇、心理諮商關懷服務、以及友善職場工作氛圍之建立，以維持穩定的勞動關係。"
            )
        }
        return res
