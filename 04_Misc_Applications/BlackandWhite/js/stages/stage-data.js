/**
 * 關卡與沙盒設定配置庫 (Stage & Sandbox Level Data - 8-Stage Epic Campaign)
 * 善與惡2專屬史詩八關：對抗古挪威人、幕府日本人與阿茲特克人三大敵對文明！
 * 包含敵對文明神獸配置、建築與部隊規模、模擬城市繁榮度勝利與世紀帝國武力征服目標。
 */

export const STAGE_DATABASE = [
    {
        id: 1,
        name: '第一關：甦醒的神島 (教學與啟蒙)',
        desc: '學習抓取物件獻祭、召喚祈禱與引導神獸行善或破壞。透過建造或奇蹟降服鄰近的部落。',
        targetVillagesCount: 2,
        isSandbox: false,
        initialEnergy: 500,
        rivalFaction: null,
        rivalCreatureSpecies: null,
        villages: [
            { id: 'v1', name: '晨曦村 (您的部落)', x: 800, y: 900, owner: 'player' },
            { id: 'v2', name: '綠野村 (中立部落)', x: 1250, y: 1100, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 750, y: 800 },
            { id: 'r2', type: 'tree', x: 850, y: 820 },
            { id: 'r3', type: 'tree', x: 700, y: 950 },
            { id: 'r4', type: 'crop', x: 850, y: 950 },
            { id: 'r5', type: 'animal_sheep', x: 920, y: 880 },
            { id: 'r6', type: 'animal_cow', x: 1180, y: 1050 },
            { id: 'r7', type: 'tree', x: 1300, y: 1000 },
            { id: 'r8', type: 'crop', x: 1200, y: 1150 }
        ]
    },
    {
        id: 2,
        name: '第二關：異教徒的邊境抵抗',
        desc: '島上存在著反抗您的原住異教徒部落，您可以選擇建立神聖噴泉吸引他們投誠，或是訓練民團出兵攻佔！',
        targetVillagesCount: 3,
        isSandbox: false,
        initialEnergy: 800,
        rivalFaction: null,
        rivalCreatureSpecies: null,
        villages: [
            { id: 'v1', name: '聖泉村 (您的部落)', x: 700, y: 850, owner: 'player' },
            { id: 'v2', name: '紅岩村 (敵對部落)', x: 1300, y: 850, owner: 'rival' },
            { id: 'v3', name: '月灣村 (中立部落)', x: 1000, y: 1250, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 650, y: 780 },
            { id: 'r2', type: 'tree', x: 750, y: 780 },
            { id: 'r3', type: 'crop', x: 680, y: 920 },
            { id: 'r4', type: 'animal_sheep', x: 800, y: 950 },
            { id: 'r5', type: 'animal_cow', x: 950, y: 1150 },
            { id: 'r6', type: 'tree', x: 1350, y: 780 },
            { id: 'r7', type: 'crop', x: 1250, y: 920 },
            { id: 'r8', type: 'tree', x: 1050, y: 1300 },
            { id: 'r9', type: 'rock', x: 1150, y: 1050 }
        ]
    },
    {
        id: 3,
        name: '第三關：古挪威海盜的峽灣突擊 (Norsemen)',
        desc: '強悍的【古挪威人】帶著維京狂戰士與他們的守護巨獸【芬里爾神狼】入侵！準備迎接驚天動地的巨獸格鬥！',
        targetVillagesCount: 3,
        isSandbox: false,
        initialEnergy: 1200,
        rivalFaction: 'norse',
        rivalCreatureSpecies: 'wolf',
        villages: [
            { id: 'v1', name: '峽灣守備營 (您的部落)', x: 650, y: 800, owner: 'player' },
            { id: 'v2', name: '維京戰港 (古挪威要塞)', x: 1350, y: 750, owner: 'rival' },
            { id: 'v3', name: '冰沙灘部落 (中立村莊)', x: 1000, y: 1250, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 600, y: 750 },
            { id: 'r2', type: 'crop', x: 650, y: 880 },
            { id: 'r3', type: 'animal_cow', x: 750, y: 900 },
            { id: 'r4', type: 'tree', x: 1300, y: 700 },
            { id: 'r5', type: 'crop', x: 1400, y: 820 },
            { id: 'r6', type: 'animal_sheep', x: 1050, y: 1200 },
            { id: 'r7', type: 'rock', x: 950, y: 1000 }
        ]
    },
    {
        id: 4,
        name: '第四關：冰封極地的凜冬要塞 (Norsemen)',
        desc: '深入古挪威文明的冰雪老巢！敵人建立了強大的武力軍團與戰神巨碑，您必須展現更強的繁榮奇觀或以烈火法術燒毀要塞！',
        targetVillagesCount: 4,
        isSandbox: false,
        initialEnergy: 1500,
        rivalFaction: 'norse',
        rivalCreatureSpecies: 'polar_bear',
        villages: [
            { id: 'v1', name: '破冰營地 (您的部落)', x: 600, y: 700, owner: 'player' },
            { id: 'v2', name: '奧丁神殿城 (挪威主城)', x: 1400, y: 700, owner: 'rival' },
            { id: 'v3', name: '霜雪哨站 (挪威部隊營)', x: 1400, y: 1300, owner: 'rival' },
            { id: 'v4', name: '極光村 (中立部落)', x: 650, y: 1300, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 550, y: 650 },
            { id: 'r2', type: 'crop', x: 650, y: 750 },
            { id: 'r3', type: 'animal_sheep', x: 700, y: 780 },
            { id: 'r4', type: 'tree', x: 1350, y: 650 },
            { id: 'r5', type: 'rock', x: 1000, y: 1000 },
            { id: 'r6', type: 'tree', x: 600, y: 1250 },
            { id: 'r7', type: 'animal_cow', x: 1350, y: 1250 }
        ]
    },
    {
        id: 5,
        name: '第五關：幕府武士與櫻花迷霧 (Japanese)',
        desc: '踏入神秘的東方島嶼，對抗【幕府日本文明】與他們的鎮國神獸【白虎神君】！敵人擅長以精銳武士刀客襲擾。',
        targetVillagesCount: 4,
        isSandbox: false,
        initialEnergy: 1800,
        rivalFaction: 'japanese',
        rivalCreatureSpecies: 'tiger',
        villages: [
            { id: 'v1', name: '櫻華山莊 (您的部落)', x: 650, y: 750, owner: 'player' },
            { id: 'v2', name: '幕府天守閣 (日本主城)', x: 1350, y: 750, owner: 'rival' },
            { id: 'v3', name: '京都茶寮 (中立村莊)', x: 1000, y: 1300, owner: 'neutral' },
            { id: 'v4', name: '武士道館 (日本兵營)', x: 650, y: 1300, owner: 'rival' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 600, y: 700 },
            { id: 'r2', type: 'crop', x: 700, y: 800 },
            { id: 'r3', type: 'animal_cow', x: 750, y: 820 },
            { id: 'r4', type: 'tree', x: 1300, y: 700 },
            { id: 'r5', type: 'crop', x: 1400, y: 800 },
            { id: 'r6', type: 'tree', x: 950, y: 1250 },
            { id: 'r7', type: 'rock', x: 1050, y: 1000 }
        ]
    },
    {
        id: 6,
        name: '第六關：天守閣的雷電結界與弓箭防線 (Japanese)',
        desc: '日本文明建立了極其嚴密的弓箭塔樓防線與雷電結界！您可以選擇大規模發展模擬城市文化，讓敵方居民自願背叛幕府投誠！',
        targetVillagesCount: 4,
        isSandbox: false,
        initialEnergy: 2200,
        rivalFaction: 'japanese',
        rivalCreatureSpecies: 'leopard',
        villages: [
            { id: 'v1', name: '日出營地 (您的部落)', x: 600, y: 700, owner: 'player' },
            { id: 'v2', name: '江戶大城 (日本要塞)', x: 1400, y: 700, owner: 'rival' },
            { id: 'v3', name: '神社村 (日本部落)', x: 1400, y: 1300, owner: 'rival' },
            { id: 'v4', name: '竹林村 (中立村莊)', x: 600, y: 1300, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 550, y: 650 },
            { id: 'r2', type: 'crop', x: 650, y: 750 },
            { id: 'r3', type: 'tree', x: 1350, y: 650 },
            { id: 'r4', type: 'rock', x: 1000, y: 1000 },
            { id: 'r5', type: 'animal_sheep', x: 650, y: 1250 }
        ]
    },
    {
        id: 7,
        name: '第七關：太陽金字塔與血祭叢林 (Aztecs)',
        desc: '進入古老的【阿茲特克帝國】領土！敵人將活人獻祭至極限，換取無盡的法術能量，並喚醒了巨型傳說巨獸【太陽羽蛇神龍】！',
        targetVillagesCount: 5,
        isSandbox: false,
        initialEnergy: 2600,
        rivalFaction: 'aztec',
        rivalCreatureSpecies: 'dragon',
        villages: [
            { id: 'v1', name: '遠征軍港 (您的部落)', x: 600, y: 650, owner: 'player' },
            { id: 'v2', name: '太陽神金字塔 (阿茲特克皇城)', x: 1400, y: 650, owner: 'rival' },
            { id: 'v3', name: '羽蛇祭壇村 (阿茲特克要塞)', x: 1400, y: 1350, owner: 'rival' },
            { id: 'v4', name: '豹戰士營地 (阿茲特克兵營)', x: 1000, y: 1000, owner: 'rival' },
            { id: 'v5', name: '密林村 (中立部落)', x: 600, y: 1350, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 550, y: 600 },
            { id: 'r2', type: 'crop', x: 650, y: 700 },
            { id: 'r3', type: 'animal_cow', x: 700, y: 720 },
            { id: 'r4', type: 'tree', x: 1350, y: 600 },
            { id: 'r5', type: 'rock', x: 950, y: 950 },
            { id: 'r6', type: 'tree', x: 550, y: 1300 }
        ]
    },
    {
        id: 8,
        name: '第八關：最終對決：諸神黃昏與末日神島 (Campaign Finale)',
        desc: '史詩戰役的終極決戰！古挪威人、幕府日本人與阿茲特克人組成了三國聯合艦隊，派出雙重神獸前來圍攻！展現您是終極善神救世主，或是毀滅世界的無情魔神！',
        targetVillagesCount: 5,
        isSandbox: false,
        initialEnergy: 3500,
        rivalFaction: 'aztec',
        rivalCreatureSpecies: 'phoenix',
        villages: [
            { id: 'v1', name: '創世神域 (您的王都)', x: 600, y: 700, owner: 'player' },
            { id: 'v2', name: '挪威聯軍營 (挪威要塞)', x: 1400, y: 600, owner: 'rival' },
            { id: 'v3', name: '幕府聯軍營 (日本要塞)', x: 1400, y: 1400, owner: 'rival' },
            { id: 'v4', name: '阿茲特克皇城 (主聯軍城)', x: 1000, y: 1000, owner: 'rival' },
            { id: 'v5', name: '祈禱聖地 (中立部落)', x: 600, y: 1400, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 550, y: 650 },
            { id: 'r2', type: 'crop', x: 650, y: 750 },
            { id: 'r3', type: 'animal_cow', x: 700, y: 780 },
            { id: 'r4', type: 'tree', x: 1350, y: 550 },
            { id: 'r5', type: 'rock', x: 950, y: 950 },
            { id: 'r6', type: 'tree', x: 550, y: 1350 },
            { id: 'r7', type: 'animal_sheep', x: 1350, y: 1350 }
        ]
    },
    {
        id: 0,
        name: '自由模式：創世沙盒 (Sandbox)',
        desc: '無限能量、解鎖全部神力！自由測試 19 種神獸調教、奇觀建築與巨獸格鬥極限。',
        targetVillagesCount: 4,
        isSandbox: true,
        initialEnergy: 9999,
        rivalFaction: 'aztec',
        rivalCreatureSpecies: 'dragon',
        villages: [
            { id: 'v1', name: '創世主城 (您的部落)', x: 700, y: 700, owner: 'player' },
            { id: 'v2', name: '試驗東村 (中立部落)', x: 1300, y: 700, owner: 'neutral' },
            { id: 'v3', name: '試驗南村 (敵對部落)', x: 1300, y: 1300, owner: 'rival' },
            { id: 'v4', name: '試驗西村 (中立部落)', x: 700, y: 1300, owner: 'neutral' }
        ],
        resources: [
            { id: 'r1', type: 'tree', x: 650, y: 650 },
            { id: 'r2', type: 'tree', x: 750, y: 650 },
            { id: 'r3', type: 'crop', x: 700, y: 780 },
            { id: 'r4', type: 'animal_sheep', x: 800, y: 800 },
            { id: 'r5', type: 'animal_cow', x: 900, y: 900 },
            { id: 'r6', type: 'tree', x: 1250, y: 650 },
            { id: 'r7', type: 'crop', x: 1350, y: 750 },
            { id: 'r8', type: 'animal_cow', x: 1250, y: 1250 },
            { id: 'r9', type: 'tree', x: 650, y: 1250 },
            { id: 'r10', type: 'rock', x: 1000, y: 1000 }
        ]
    }
];

export function getStageData(stageId) {
    return STAGE_DATABASE.find(s => s.id === Number(stageId)) || STAGE_DATABASE[0];
}
