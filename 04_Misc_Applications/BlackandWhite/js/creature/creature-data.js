/**
 * 19 種神獸物種資料庫 (Creature Species Database)
 * 包含完整物種名稱、外觀符號、初始數值傾向與特徵
 */
export const CREATURE_SPECIES = [
    { id: 'ape', name: 'Ape 猿', symbol: '🦍', str: 80, spd: 70, mana: 85, pitch: 0.9, desc: '智慧高，學習神力法術的速度極快，體格勻稱。' },
    { id: 'brown_bear', name: 'Brown Bear 棕色熊', symbol: '🐻', str: 90, spd: 50, mana: 60, pitch: 0.6, desc: '力量強大且胃口驚人，喜歡捕捉魚與動物。' },
    { id: 'chicken', name: 'Chicken 雞', symbol: '🐓', str: 30, spd: 85, mana: 90, pitch: 1.8, desc: '體型雖小但動作極敏捷，施法消耗能量低。' },
    { id: 'chimpanzee', name: 'Chimpanzee 黑猩猩', symbol: '🦧', str: 65, spd: 80, mana: 95, pitch: 1.1, desc: '好奇心旺盛的最強法術學習者，善於模仿上帝手勢。' },
    { id: 'cow', name: 'Cow 牛', symbol: '🐄', str: 85, spd: 40, mana: 50, pitch: 0.7, desc: '個性溫馴的草食神獸，深受善神部落喜愛。' },
    { id: 'crocodile', name: 'Crocodile 鱷魚', symbol: '🐊', str: 95, spd: 60, mana: 40, pitch: 0.5, desc: '兇猛的掠食者，具有極強的物理破壞力與威嚇感。' },
    { id: 'gorilla', name: 'Gorilla 大猩猩', symbol: '🦍', str: 100, spd: 60, mana: 70, pitch: 0.6, desc: '叢林王者，擁有毀滅性的肉搏力量與不錯的悟性。' },
    { id: 'horse', name: 'Horse 馬', symbol: '🐎', str: 75, spd: 100, mana: 60, pitch: 1.0, desc: '奔跑速度島上第一，能迅速奔馳往返各地救援或干擾。' },
    { id: 'leopard', name: 'Leopard 豹', symbol: '🐆', str: 85, spd: 95, mana: 65, pitch: 1.2, desc: '隱匿與爆發力兼具的獵手，適合對抗敵對村莊。' },
    { id: 'lion', name: 'Lion 獅子', symbol: '🦁', str: 95, spd: 80, mana: 70, pitch: 0.7, desc: '百獸之王，具備威嚴的吼聲，能大幅威嚇敵對村民。' },
    { id: 'mandrill', name: 'Mandrill 山魈', symbol: '🐵', str: 70, spd: 85, mana: 90, pitch: 1.3, desc: '色彩斑斕的神秘神獸，精通施展善惡魔法。' },
    { id: 'ogre', name: 'Ogre 食人怪', symbol: '👹', str: 120, spd: 45, mana: 80, pitch: 0.4, desc: '傳說中的異界巨獸，天生傾向邪惡與毀滅性法術。' },
    { id: 'polar_bear', name: 'Polar Bear 北極熊', symbol: '🐻‍❄️', str: 95, spd: 55, mana: 65, pitch: 0.55, desc: '來自冰原的強悍巨獸，對冰凍與水系法術有天然抗性。' },
    { id: 'rhinoceros', name: 'Rhinoceros 犀牛', symbol: '🦏', str: 105, spd: 50, mana: 40, pitch: 0.5, desc: '衝鋒陷陣的重型坦克，衝撞房屋的效率極高。' },
    { id: 'sheep', name: 'Sheep 羊', symbol: '🐑', str: 40, spd: 65, mana: 80, pitch: 1.5, desc: '極限溫和的神獸，村民看到牠會感到安心與快樂。' },
    { id: 'tiger', name: 'Tiger 老虎', symbol: '🐯', str: 95, spd: 90, mana: 65, pitch: 0.75, desc: '孤傲而致命的頂級掠食者，戰鬥與追擊能力絕佳。' },
    { id: 'turtle', name: 'Turtle 烏龜', symbol: '🐢', str: 90, spd: 20, mana: 100, pitch: 0.6, desc: '擁有最堅固的甲殼防禦與最高的法力悟性，壽命悠長。' },
    { id: 'wolf', name: 'Wolf 狼', symbol: '🐺', str: 80, spd: 90, mana: 75, pitch: 1.1, desc: '忠誠的獵犬，善於與群獸神力配合進行狼群狩獵。' },
    { id: 'zebra', name: 'Zebra 斑馬', symbol: '🦓', str: 70, spd: 95, mana: 65, pitch: 1.2, desc: '黑白相間的神駿，代表著善與惡的中立平衡。' },
    { id: 'dragon', name: 'Dragon 神龍 (傳說)', symbol: '🐉', str: 130, spd: 95, mana: 120, pitch: 0.4, desc: '【商用限定傳說神獸】呼風喚雨的東方巨龍，擁有極高的攻擊與法術天賦！', premium: true, cost: 200 },
    { id: 'phoenix', name: 'Phoenix 不死鳥 (傳說)', symbol: '🦅', str: 110, spd: 110, mana: 130, pitch: 1.5, desc: '【商用限定傳說神獸】浴火重生的神聖神鳥，施放善惡魔法皆極致完美！', premium: true, cost: 200 }
];

export function getSpeciesById(id) {
    return CREATURE_SPECIES.find(s => s.id === id) || CREATURE_SPECIES[0];
}
