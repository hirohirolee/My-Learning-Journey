# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - 地端 AI 管理模組 (升級版)
"""

import os
import json
import ollama
import config
from gri_config import GRI_CONFIG

class ESGLLMManager:
    """
    調度地端 Ollama AI 進行符合 GRI 規範的永續報告書子章節文本撰寫與擴寫。
    """
    
    def __init__(self, model_name=None, host=None):
        self.model_name = model_name or config.MODEL_NAME
        self.host = host or config.OLLAMA_HOST
        
        # 初始化 Ollama 客戶端，設置 10 秒超時限制以防連線掛起
        try:
            self.client = ollama.Client(host=self.host, timeout=10.0)
        except Exception as e:
            self.client = None
            print(f"⚠️ 初始化 Ollama 客戶端失敗，將使用預設的備用方案。錯誤原因: {e}")

    @staticmethod
    def check_connection(host, model_name):
        """
        檢查與地端 Ollama 伺服器的連線，並確認選擇的模型是否已安裝。
        回傳: (is_connected, model_downloaded, installed_models)
        """
        try:
            # 使用較短的 2.0 秒超時進行快速連線測試
            client = ollama.Client(host=host, timeout=2.0)
            # 獲取模型列表，此呼叫可同時驗證 Ollama 服務是否正常在線
            models_response = client.list()
            
            # 從回傳中提取已安裝模型的名稱
            installed_models = []
            for m in models_response.get("models", []):
                # 兼容不同的 ollama-python 版本與欄位命名
                if "name" in m:
                    installed_models.append(m["name"])
                elif "model" in m:
                    installed_models.append(m["model"])
            
            # 檢查目標模型是否在列表中 (支援模型名稱帶 tag 與不帶 tag 的匹配)
            model_downloaded = False
            for name in installed_models:
                if name == model_name or name.startswith(f"{model_name}:"):
                    model_downloaded = True
                    break
            
            return True, model_downloaded, installed_models
        except Exception:
            return False, False, []

    def generate_chapter_subsections(self, json_data, framework_code, target_words=350, selected_subs=None):
        """
        為特定的 GRI 框架代碼分別生成核心子項文本。
        回傳字典： {"3.1.1": text_311, ...}
        """
        framework_code = str(framework_code).strip().upper()
        results = {}
        
        # 從全域配置中動態尋找對應的指標設定
        matched_config = None
        for key, cfg in GRI_CONFIG.items():
            if cfg["code"] == framework_code or framework_code in key:
                matched_config = cfg
                break
                
        if not matched_config:
            # 預設回退
            return {"無子章節": f"已收到數據：{json.dumps(json_data, ensure_ascii=False)}"}
            
        subs = matched_config["sub_items"]
        fallback_method_name = matched_config["fallback_method"]
        fallback_func = getattr(self, fallback_method_name, None)

        # 如果客戶端存在，先進行一次快速連線檢測，避免連線失敗導致多次等待超時
        if self.client is not None:
            is_connected, _, _ = self.check_connection(self.host, self.model_name)
            if not is_connected:
                print("⚠️ 檢測到 Ollama 伺服器未連線，將直接使用備用文本。")
                self.client = None

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
                # 實作重試與最低長度檢查邏輯，避免 Ollama 出現過短或空白的異常輸出
                min_len = max(50, target_words // 2)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        response = self.client.chat(
                            model=self.model_name,
                            messages=[
                                {'role': 'system', 'content': system_instruction},
                                {'role': 'user', 'content': user_prompt}
                            ]
                        )
                        candidate_text = response['message']['content'].strip()
                        if len(candidate_text) >= min_len:
                            sub_text = candidate_text
                            break
                        else:
                            print(f"⚠️ 第 {attempt} 次生成文本長度不足 ({len(candidate_text)} < {min_len} 字)，將重試。")
                    except Exception as e:
                        print(f"❌ 第 {attempt} 次呼叫 Ollama {self.model_name} 失敗。錯誤: {e}")
                        if attempt == max_attempts:
                            print("⚠️ 偵測到地端 Ollama 服務多次呼叫失敗，已將連線重設，後續子章節將直接採用備用方案。")
                            self.client = None
                            break
            
            # 如果 AI 生成失敗或未連線，則調用本地高質量 Fallback
            if not sub_text:
                if fallback_func is not None:
                    fallback_dict = fallback_func(json_data)
                    sub_text = fallback_dict.get(sub_id, "")
                else:
                    sub_text = f"數據摘要: {json.dumps(json_data, ensure_ascii=False)}"
                
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

    def _get_gri_302_subchapters_fallback(self, data):
        """GRI 302 能源消耗的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        ed = data.get("energy_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in ed.items()]
        res = {
            "3.2.1": (
                f"依據 GRI 302 能源消耗量揭露準則，{company} 於 {year} 年度落實了全面的內部能源使用排查。 "
                f"本年度我們所統計的組織內部能源消耗數據包含：{', '.join(details)}。 "
                f"其中，生產營運所必需之外購電力占總能源消耗比重最深。此數據盤點有助於企業精確掌握高能耗製程，為能效優化與低碳經營奠定實證數據基礎。"
            ),
            "3.2.2": (
                f"在能源密集度與節能減量方面，{company} 透過導入系統化的節能管理方案以提升能源使用效率。 "
                f"本年度除了針對老舊空調與照明系統進行 LED 及變頻設備汰換外，亦透過智慧電網實時追蹤能耗強度。 "
                f"透過此等節能減碳舉措，本公司在控制能耗密度的同時，將逐步提高綠色能源的採購比率，實踐永續低碳營運的長期承諾。"
            )
        }
        return res

    def _get_gri_306_subchapters_fallback(self, data):
        """GRI 306 廢棄物與回收的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        wd = data.get("waste_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in wd.items()]
        res = {
            "3.6.1": (
                f"依據 GRI 306 廢棄物揭露準則，{company} 針對 {year} 年度營運與製造過程所產生的各類廢棄物進行源頭盤查。 "
                f"我們分析發現廢棄物主要源自製程廢料及包材物料，並已統計之相關指標如：{', '.join(details)}。 "
                f"本公司致力推動源頭減量，實施包材包裝簡化與生產流程廢料最小化管理，從起點降低廢棄物產生量。"
            ),
            "3.6.2": (
                f"在廢棄物回收與循環經濟方面，{company} 建立並優化了內部資源分類與回收管理機制。 "
                f"本公司落實一般資源垃圾與製程可回收物（如廢金屬、紙箱）的精細分類，促使資源二次再利用。 "
                f"透過與合格回收廠商的長期合作，我們顯著提升了廠區的整體廢棄物回收率，將廢棄資源轉化為再生材料，實現循環再生價值。"
            ),
            "3.6.3": (
                f"在最終處置與環保合規方面，{company} 針對本年度無法回收的殘留廢棄物採取合規處置。 "
                f"所有有害事業廢棄物均委託具備國家合格牌照之清除處理機構，透過焚化或安全掩埋方式處理，並使用三聯單聯單申報系統落實流向追蹤。 "
                f"本年度所有處置流程皆完全符合政府環境保護法規要求，未發生任何違規處分情事。"
            )
        }
        return res

    def _get_gri_401_subchapters_fallback(self, data):
        """GRI 401 員工聘用的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        ed = data.get("employment_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in ed.items()]
        res = {
            "4.1.1.b": (
                f"依據 GRI 401 聘用與流動揭露準則，{company} 精確統計並分析了 {year} 年度的招募與離職員工數據， "
                f"關鍵指標包括：{', '.join(details)}。 "
                f"人才流動率的波動能反映組織內部的活力與職缺遞補效率。本公司透過定期的員工訪談與離職調查，深入分析流動原因，以健全人才儲備鏈並維持穩定的業務營運。"
            ),
            "4.1.2": (
                f"為營造吸引與留任優秀人才之環境，{company} 提供健全的福利制度與友善職場關懷措施。 "
                f"除了依法提供勞健保、提撥退休金外，本公司亦提供育嬰留職停薪制度、托兒津貼、員工子女獎學金與彈性工作時間等政策。 "
                f"這些關懷專案旨在協助員工平衡工作與家庭生活，提升對企業之認同感，並建立長久穩固的夥伴關係。"
            )
        }
        return res

    def _get_gri_405_subchapters_fallback(self, data):
        """GRI 405 多元的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        dd = data.get("diversity_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in dd.items()]
        res = {
            "4.5.1": (
                f"依據 GRI 405 多元與平等機會揭露指標，{company} 致力於促進組織內部的包容性與多元化。 "
                f"我們於 {year} 年度對管理階層與基層員工之性別占比、年齡組成進行了普查，數據顯示：{', '.join(details)}。 "
                f"公司在人才選拔與晉升中重視性別平等，確保多元觀點融入決策階層，並提供各世代員工和諧共融的工作舞台。"
            ),
            "4.5.2": (
                f"為落實職場平等與消除歧視，{company} 堅定維護同工同酬之薪酬與獎酬政策。 "
                f"本公司之招募、核薪、考績與晉升流程皆以專業職能與實際工作表現為評分基礎，排除性別、年齡、種族或信仰等非關工作績效之干擾因素。 "
                f"我們亦定期檢視內部薪資結構，確保相同職等與工作價值之同仁獲得對等的經濟回饋與平等之晉升機會。"
            )
        }
        return res

    def _get_gri_201_subchapters_fallback(self, data):
        """GRI 201 經濟績效的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        ed = data.get("economic_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in ed.items()]
        res = {
            "2.1.1": (
                f"依據 GRI 201 經濟績效揭露標準，{company} 於 {year} 年度持續實現經營效益，並致力於合理分配經濟價值。 "
                f"本年度我們的直接經濟產生與持份者分配數據包含：{', '.join(details)}。 "
                f"我們藉由向供應商支付成本、給予同仁具競爭力之薪資福利、依法繳納國家稅收，以及推動社區公益與地方共融，將營運成果反饋至社會，實現企業與環境、社會之多贏局勢。"
            ),
            "2.1.2": (
                f"在氣候變遷財務衝擊評估方面，{company} 高度重視氣候變遷對營運所產生的風險與契機。 "
                f"本公司正評估如極端氣候導致產線停工之實體風險，以及政府未來開徵碳費等轉型風險。 "
                f"我們已將低碳節能目標融入企業策略中，透過逐步導入低碳工藝、提升水電利用效率等適應性作為，減輕潛在氣候風險之財務衝擊。"
            )
        }
        return res

    def _get_gri_205_subchapters_fallback(self, data):
        """GRI 205 反貪腐的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        ad = data.get("anti_corruption_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v:,}" for k, v in ad.items()]
        res = {
            "2.5.1": (
                f"依據 GRI 205 反貪腐揭露標準，{company} 積極推廣商業誠信經營守則。 "
                f"我們於 {year} 年度的反貪腐與合規推動數據為：{', '.join(details)}。 "
                f"本公司董事及全體員工已依法簽署誠信經營承諾，並舉辦定期的反貪腐與商業道德教育訓練課程，確保所有同仁在對外商務合作與對內日常營運中，均嚴格遵守合規紀律。"
            ),
            "2.5.2": (
                f"為防範商業貪腐與違規行為，{company} 建立了嚴密的內部控制、合規稽核與健全的 Whistleblowing 檢舉機制。 "
                f"本公司設有獨立的內部稽核室與匿名檢舉申訴管道，並明文保障檢舉人的隱私與安全，防止打壓報復。 "
                f"在 {year} 年度中，本公司並無任何貪腐、受賄或違反誠實信用原則之確立案件，展現健全誠信治理成果。"
            )
        }
        return res

    def _get_gri_2_subchapters_fallback(self, data):
        """GRI 2 一般揭露的備用文本"""
        company = data.get("company_name", "本公司")
        year = data.get("reporting_year", "2025")
        gd = data.get("general_data", {})
        details = [f"「{k.replace('_', ' ')}」為 {v}" for k, v in gd.items()]
        res = {
            "2.2.1": (
                f"依據 GRI 2 一般揭露準則，{company} 詳實揭露本年度之基礎概況。 "
                f"本公司之核心資本結構、註冊地與營運規模數據包含：{', '.join(details)}。 "
                f"本公司營運聚焦於核心產品研發，並推動高品質製造服務，在市場中穩步擴張，為投資人與社會大眾建立透明的公司身分形象。"
            ),
            "2.2.2": (
                f"在商業活動與供應鏈關係方面，{company} 健全上下游價值鏈管理與合作夥伴規範。 "
                f"我們建立了供應商社會與環境責任審查機制，要求關鍵合作廠商承諾遵守人權保障、環保安全及誠信經營等核心條款。 "
                f"本公司亦積極落實綠色採購計畫，優先選用環保低耗能原料與服務，以協同價值鏈夥伴共同降低營運的環境足跡。"
            ),
            "2.2.3": (
                f"在人資聘用特性方面，{company} 全面普查內部全職、兼職及其他不同聘用形式的同仁。 "
                f"我們維持高度穩定的雇用關係，不採取剝削性短期契約，並依據國家法規提供全體同仁平等的職業機會、公平的績效待遇及友善的工作場域。 "
                f"此舉有助於維繫穩健、和諧的勞資互動，降低人才流失率，為企業永續營運儲蓄核心的人力資源動能。"
            )
        }
        return res

