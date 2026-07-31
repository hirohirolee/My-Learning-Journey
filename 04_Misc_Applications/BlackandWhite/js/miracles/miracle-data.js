/**
 * 26+ 種神力與魔法參數配置表 (Miracle & Spell Configuration)
 * 涵蓋：善性神力、惡性神力、輔助神力(作用於神獸) 與 其他神力
 */
export const MIRACLE_DATABASE = {
    // ==================== 1. 善性神力 (Good Miracles) ====================
    'food_1': { id: 'food_1', name: '造食神力', category: 'good', cost: 60, symbol: '〇', cd: 4, icon: '🍞', align: +10, desc: '在目標區域生產 150 糧食補給村莊' },
    'food_2': { id: 'food_2', name: '增強造食神力', category: 'good', cost: 120, symbol: '〇', cd: 8, icon: '🥐', align: +20, desc: '大量生產 350 糧食，瞬間解決飢荒' },
    'wood_1': { id: 'wood_1', name: '造木神力', category: 'good', cost: 80, symbol: '〇', cd: 5, icon: '🪵', align: +10, desc: '為部落庫存增加 200 建築木材' },
    'water_1': { id: 'water_1', name: '造水神力 (灑水)', category: 'good', cost: 50, symbol: '〇', cd: 3, icon: '🌧️', align: +8, desc: '降下溫和雨水，滋潤作物與村民' },
    'water_2': { id: 'water_2', name: '增強造水神力', category: 'good', cost: 100, symbol: '〇', cd: 7, icon: '⛈️', align: +15, desc: '長時間降雨，全島作物加速生長' },
    'forest_1': { id: 'forest_1', name: '造林神力', category: 'good', cost: 150, symbol: '〇', cd: 10, icon: '🌲', align: +15, desc: '在目標空地上瞬間造出一片茂盛樹林' },
    'heal_1': { id: 'heal_1', name: '冶療神力', category: 'good', cost: 70, symbol: '♡', cd: 5, icon: '💚', align: +15, desc: '釋放神聖愛心，冶療一定範圍內傷殘村民' },
    'heal_2': { id: 'heal_2', name: '增強冶療神力', category: 'good', cost: 140, symbol: '♡', cd: 9, icon: '💖', align: +25, desc: '廣域冶療村民並大幅增加愛與崇敬信仰' },
    'heal_3': { id: 'heal_3', name: '終極冶療神力', category: 'good', cost: 250, symbol: '♡', cd: 15, icon: '🌟', align: +40, desc: '超大範圍璀璨神光，全村恢復健康與滿點信仰' },

    // ==================== 2. 惡性神力 (Evil Miracles) ====================
    'fireball_1': { id: 'fireball_1', name: '火球神力', category: 'evil', cost: 60, symbol: '△', cd: 4, icon: '🔥', align: -15, desc: '從天降下一顆爆裂火球，摧毀房屋與敵方目標' },
    'fireball_2': { id: 'fireball_2', name: '增強火球神力', category: 'evil', cost: 150, symbol: '△', cd: 8, icon: '☄️', align: -30, desc: '連放三顆火球轟炸，造成巨大恐懼' },
    'fireball_3': { id: 'fireball_3', name: '終極火球神力', category: 'evil', cost: 300, symbol: '△', cd: 14, icon: '💥', align: -50, desc: '八顆火球連環毀滅轟炸，瞬間摧毀對手村莊' },
    'lightning_1': { id: 'lightning_1', name: '雷電神力', category: 'evil', cost: 70, symbol: 'Z', cd: 4, icon: '⚡', align: -15, desc: '召喚天雷劈擊目標點，威嚇敵人' },
    'lightning_2': { id: 'lightning_2', name: '增強雷電神力', category: 'evil', cost: 140, symbol: 'Z', cd: 8, icon: '🌩️', align: -30, desc: '強力雙重落雷，破壞力翻倍' },
    'lightning_3': { id: 'lightning_3', name: '終極雷電神力', category: 'evil', cost: 260, symbol: 'Z', cd: 12, icon: '🌩️', align: -50, desc: '毀滅天雷巨響，引發全區震撼恐懼' },
    'storm_1': { id: 'storm_1', name: '暴風雨神力', category: 'evil', cost: 100, symbol: 'S', cd: 8, icon: '🌪️', align: -20, desc: '造出狂風暴雨雲層，阻礙敵對採集' },
    'storm_2': { id: 'storm_2', name: '增強暴風雨神力', category: 'evil', cost: 200, symbol: 'S', cd: 12, icon: '⛈️', align: -35, desc: '暴風雨伴隨隨機落雷閃電' },
    'storm_3': { id: 'storm_3', name: '終極暴風雨神力', category: 'evil', cost: 350, symbol: 'S', cd: 18, icon: '🌀', align: -60, desc: '召喚暴風雨、雷電與毀滅性龍捲風席捲大地' },
    'blast_1': { id: 'blast_1', name: '爆破神力', category: 'evil', cost: 80, symbol: '△', cd: 5, icon: '💣', align: -15, desc: '破壞一定範圍內的物件與城牆' },
    'blast_2': { id: 'blast_2', name: '增強爆破神力', category: 'evil', cost: 160, symbol: '△', cd: 9, icon: '🧨', align: -30, desc: '破壞範圍與衝擊波加大' },
    'blast_3': { id: 'blast_3', name: '終極爆破神力', category: 'evil', cost: 280, symbol: '△', cd: 15, icon: '💥', align: -50, desc: '超廣域核彈級爆破，撼動整座島嶼' },
    'wolf_pack': { id: 'wolf_pack', name: '群獸神力', category: 'evil', cost: 220, symbol: 'Z', cd: 16, icon: '🐺', align: -40, desc: '召喚一群凶狠狼群，侵襲並撕咬敵方部落' },

    // ==================== 3. 輔助神力 (Auxiliary / Creature Buffs) ====================
    'aux_strong': { id: 'aux_strong', name: '強壯神力', category: 'aux', cost: 80, symbol: '♡', cd: 6, icon: '💪', align: 0, desc: '使神獸力量大增 1.5 倍' },
    'aux_weak': { id: 'aux_weak', name: '虛弱神力', category: 'aux', cost: 60, symbol: '♡', cd: 6, icon: '🥀', align: -10, desc: '使神獸或敵對神獸力量降低至 60%' },
    'aux_freeze': { id: 'aux_freeze', name: '冰凍神力', category: 'aux', cost: 70, symbol: '〇', cd: 8, icon: '❄️', align: -10, desc: '將神獸凍結在冰塊中動彈不得' },
    'aux_speed': { id: 'aux_speed', name: '加速神力', category: 'aux', cost: 80, symbol: 'Z', cd: 6, icon: '⚡', align: +5, desc: '使神獸移動與衝刺速度加倍' },
    'aux_enlarge': { id: 'aux_enlarge', name: '放大神力', category: 'aux', cost: 120, symbol: '△', cd: 12, icon: '🦖', align: 0, desc: '使神獸體格巨大化至 2 倍，極致威嚴' },
    'aux_shrink': { id: 'aux_shrink', name: '縮小神力', category: 'aux', cost: 60, symbol: '〇', cd: 6, icon: '🐭', align: 0, desc: '使神獸縮小至 0.6 倍，靈巧但力量低' },
    'aux_compassion': { id: 'aux_compassion', name: '喜愛神力', category: 'aux', cost: 100, symbol: '♡', cd: 10, icon: '💖', align: +30, desc: '感化神獸心靈，使牠積極幫助村民行善' },
    'aux_anger': { id: 'aux_anger', name: '憤怒神力', category: 'aux', cost: 100, symbol: '△', cd: 10, icon: '😡', align: -30, desc: '激怒神獸，使牠立刻想摧毀房屋與進食' },
    'aux_invisible': { id: 'aux_invisible', name: '隱形神力', category: 'aux', cost: 90, symbol: '〇', cd: 10, icon: '👻', align: 0, desc: '使神獸進入隱身狀態，不受敵方威脅' },
    'aux_fly': { id: 'aux_fly', name: '聖蒼蠅神力', category: 'aux', cost: 110, symbol: 'S', cd: 12, icon: '🪰', align: -15, desc: '使神獸暫時失控並在大氣中亂飛奔波' },
    'aux_shield': { id: 'aux_shield', name: '抗法術神力', category: 'aux', cost: 130, symbol: '□', cd: 14, icon: '🛡️', align: 0, desc: '賦予神獸魔法免疫護盾，抵擋任何傷害' },

    // ==================== 4. 其他神力 (Other Miracles) ====================
    'other_teleport': { id: 'other_teleport', name: '傳送神力', category: 'other', cost: 150, symbol: '〇', cd: 10, icon: '🌀', align: 0, desc: '建立空間傳送光環，將神獸瞬間傳送到游標位置' },
    'other_flight': { id: 'other_flight', name: '怪物飛翔神力', category: 'other', cost: 120, symbol: 'S', cd: 8, icon: '🕊️', align: 0, desc: '善神釋放神聖白鴿；惡神釋放吸血蝙蝠群，漫天飛舞' },
    'other_phys_shield': { id: 'other_phys_shield', name: '物理防禦神力', category: 'other', cost: 180, symbol: '□', cd: 15, icon: '🏰', align: +10, desc: '創造巨大的黃金防禦穹頂，抵擋一切物理破壞' },
    'other_magic_shield': { id: 'other_magic_shield', name: '心靈防禦神力', category: 'other', cost: 180, symbol: '□', cd: 15, icon: '🔮', align: +10, desc: '創造神秘的心靈護盾穹頂，抵擋法術與威嚇' }
};

export function getMiraclesByCategory(category) {
    return Object.values(MIRACLE_DATABASE).filter(m => m.category === category);
}

export function getMiraclesByGestureSymbol(symbol) {
    return Object.values(MIRACLE_DATABASE).filter(m => m.symbol === symbol);
}
