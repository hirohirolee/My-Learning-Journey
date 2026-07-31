/**
 * ============================================================================
 * 遊戲靜態設定檔載入與驗證器 (ConfigLoader)
 * 負責從 ./data/game_config.json 非同步載入所有平衡參數
 * 內建 Inline JSON Fallback，確保在本地 file:// 協議下依然能 100% 正常讀取！
 * ============================================================================
 */

const FALLBACK_CONFIG = {
  "unit_definitions": {
    "unit_peasant": { "name": "Peasant Conscript 農民徵召兵", "cost": { "wood": 10, "food": 20, "rock": 0 }, "base_stats": { "hp": 40, "attack": 5, "defense": 1, "speed": 55, "range": 40, "morale": 60 }, "veteran_growth": { "hp_mult": 1.35, "atk_mult": 1.35, "def_mult": 1.35, "morale_bonus": 10 } },
    "unit_swordsman": { "name": "Iron Swordsman 鐵甲劍士", "cost": { "wood": 20, "food": 40, "rock": 30 }, "base_stats": { "hp": 80, "attack": 14, "defense": 5, "speed": 50, "range": 40, "morale": 70 }, "veteran_growth": { "hp_mult": 1.35, "atk_mult": 1.35, "def_mult": 1.35, "morale_bonus": 12 }, "morality_requirement": -10 },
    "unit_crossbow": { "name": "Heavy Crossbowman 重型弩弓手", "cost": { "wood": 50, "food": 35, "rock": 15 }, "base_stats": { "hp": 60, "attack": 18, "defense": 2, "speed": 45, "range": 220, "morale": 65 }, "veteran_growth": { "hp_mult": 1.3, "atk_mult": 1.4, "def_mult": 1.2, "morale_bonus": 10 }, "morality_requirement": -20 },
    "unit_cavalry": { "name": "Royal Cavalry 皇家重騎兵", "cost": { "wood": 30, "food": 80, "rock": 40 }, "base_stats": { "hp": 120, "attack": 22, "defense": 8, "speed": 95, "range": 50, "morale": 80 }, "veteran_growth": { "hp_mult": 1.4, "atk_mult": 1.4, "def_mult": 1.4, "morale_bonus": 15 }, "morality_requirement": -30 }
  },
  "building_definitions": {
    "bld_barracks": { "name": "Military Barracks 基礎兵營", "cost": { "wood": 150, "food": 0, "rock": 100 }, "stats": { "hp": 500, "defense": 10, "housing_capacity": 0, "influence_radius": 0 } },
    "bld_armory": { "name": "Advanced Armory 進階軍備庫", "cost": { "wood": 300, "food": 0, "rock": 250 }, "stats": { "hp": 800, "defense": 15, "housing_capacity": 0, "influence_radius": 0 } },
    "bld_sanctuary": { "name": "Divine Sanctuary 庇護大教堂", "cost": { "wood": 400, "food": 200, "rock": 300 }, "stats": { "hp": 1200, "defense": 20, "housing_capacity": 50, "influence_radius": 500 }, "morality_requirement": 30 },
    "bld_dark_citadel": { "name": "Dark Citadel 毀滅黑色要塞", "cost": { "wood": 200, "food": 0, "rock": 500 }, "stats": { "hp": 1500, "defense": 25, "housing_capacity": 0, "influence_radius": 600 }, "morality_requirement": -40 }
  },
  "creature_species_config": {
    "ape": { "name": "Ape 猿", "base_attributes": { "str": 80, "spd": 70, "mana": 85, "intelligence": 1.3 }, "default_alignment": 0 },
    "chimpanzee": { "name": "Chimpanzee 黑猩猩", "base_attributes": { "str": 65, "spd": 80, "mana": 95, "intelligence": 1.5 }, "default_alignment": 5 },
    "ogre": { "name": "Ogre 食人怪", "base_attributes": { "str": 120, "spd": 45, "mana": 80, "intelligence": 0.6 }, "default_alignment": -40 },
    "dragon": { "name": "Dragon 神龍 (傳說)", "base_attributes": { "str": 130, "spd": 95, "mana": 120, "intelligence": 1.4 }, "default_alignment": -30, "is_premium": true },
    "phoenix": { "name": "Phoenix 不死鳥 (傳說)", "base_attributes": { "str": 110, "spd": 110, "mana": 130, "intelligence": 1.4 }, "default_alignment": 30, "is_premium": true }
  },
  "morality_balance_rules": {
    "paragon_good": { "threshold": 50, "inflow_modifiers": { "altar_prayer": 1.5, "crop_growth": 2.0, "sacrifice_yield": 0.4 }, "outflow_modifiers": { "civic_cost": 0.8, "military_cost": 1.25 } },
    "tyrant_evil": { "threshold": -50, "inflow_modifiers": { "altar_prayer": 0.8, "crop_growth": 0.7, "sacrifice_yield": 3.0 }, "outflow_modifiers": { "civic_cost": 1.2, "military_cost": 0.75 } }
  }
};

export class ConfigLoader {
    constructor() {
        this.data = FALLBACK_CONFIG;
        this.isLoaded = false;
        this.init();
    }

    async init() {
        try {
            const response = await fetch('./data/game_config.json');
            if (response.ok) {
                this.data = await response.json();
                console.log("✅ [ConfigLoader] 成功載入 ./data/game_config.json 結構化設定檔！");
            } else {
                console.warn("⚠️ [ConfigLoader] 網路或路徑請求失敗，使用內建 Fallback JSON 設定。");
            }
        } catch (e) {
            console.warn("⚠️ [ConfigLoader] file:// 協議或跨域限制，自動切換至內建 Fallback JSON 設定。");
        } finally {
            this.isLoaded = true;
        }
    }

    getUnitConfig(unitId) {
        return (this.data.unit_definitions && this.data.unit_definitions[unitId]) || this.data.unit_definitions['unit_peasant'];
    }

    getBuildingConfig(bldId) {
        return (this.data.building_definitions && this.data.building_definitions[bldId]) || null;
    }

    getCreatureConfig(speciesId) {
        return (this.data.creature_species_config && this.data.creature_species_config[speciesId]) || null;
    }

    getMoralityModifiers(alignment) {
        if (alignment >= 20) return this.data.morality_balance_rules.paragon_good;
        if (alignment <= -20) return this.data.morality_balance_rules.tyrant_evil;
        return {
            inflow_modifiers: { altar_prayer: 1.0, crop_growth: 1.0, sacrifice_yield: 1.0 },
            outflow_modifiers: { civic_cost: 1.0, military_cost: 1.0 }
        };
    }
}

export const configLoader = new ConfigLoader();
