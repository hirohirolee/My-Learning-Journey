/**
 * 多國語言在地化管理模組 (Internationalization & Localization Manager)
 * 支援繁體中文、英文、日文與簡體中文的即時切換與詞條插值，滿足商業化發行需求。
 */
const CATALOGS = {
    'zh-TW': {
        game_title: '善與惡：神蹟島嶼',
        subtitle: '上帝模擬策略遊戲',
        btn_start_game: '開始創世',
        btn_tutorial: '新手教學與手勢表',
        btn_menu: '遊戲選單',
        btn_talents: '天賦聖殿',
        btn_skins: '神獸裝扮',
        btn_shop: '水晶商城',
        btn_quests: '每日任務',
        energy_label: '祭壇能量',
        god_good: '慈悲救世主',
        god_evil: '毀滅破壞神',
        god_neutral: '威嚴中立之神',
        notice_stage_loaded: '🌟 【{stageName}】已載入！請使用右鍵畫上手勢或左鍵抓取物件獻祭！',
        notice_sacrifice: '🔥 獻祭了{symbol}！獲得 +{val} 祭壇能量！',
        notice_sacrifice_human: '🔥 獻祭了活人村民！獲得 +{val} 能量 (殘忍邪惡度 +20)',
        notice_spell_cast: '✨ 透過手勢【{symbol}】成功施放了【{spellName}】！',
        ad_reward_title: '觀看神聖感應 (獎勵型廣告)',
        ad_reward_desc: '觀看 30 秒神聖感應，即可獲得以下奇蹟獎勵之一：',
        ad_btn_watch: '📺 觀看感應 (+500 能量 & +50 水晶)',
        shop_title: '💎 信仰水晶商城',
        shop_desc: '使用信仰水晶解鎖傳說級神獸與稀有神力護符！',
        talents_title: '🏛️ 上帝天賦聖殿',
        talents_desc: '消耗信仰水晶升級您的三大神格分支，獲得永久力量加成！',
        skin_title: '👑 神獸獸舍與裝扮',
        skin_desc: '為您的神獸配戴神聖與深淵飾品，獲得屬性強化！',
        lang_select: '🌐 選擇語言 / Language'
    },
    'en-US': {
        game_title: 'Black & White: Divine Island',
        subtitle: 'God Simulator & Strategy Game',
        btn_start_game: 'Start Creation',
        btn_tutorial: 'Tutorial & Gestures',
        btn_menu: 'Game Menu',
        btn_talents: 'God Talents',
        btn_skins: 'Beast Skins',
        btn_shop: 'Crystal Shop',
        btn_quests: 'Daily Quests',
        energy_label: 'Altar Energy',
        god_good: 'Merciful Savior',
        god_evil: 'Ruthless Destroyer',
        god_neutral: 'Majestic Neutral God',
        notice_stage_loaded: '🌟 [{stageName}] Loaded! Right-click to draw gestures or left-click to grab & sacrifice!',
        notice_sacrifice: '🔥 Sacrificed {symbol}! Gained +{val} Altar Energy!',
        notice_sacrifice_human: '🔥 Sacrificed a human villager! Gained +{val} Energy (Evil +20)',
        notice_spell_cast: '✨ Cast [{spellName}] successfully via gesture [{symbol}]!',
        ad_reward_title: 'Divine Vision (Rewarded Ad)',
        ad_reward_desc: 'Watch a 30s Divine Vision to claim one of these miraculous rewards:',
        ad_btn_watch: '📺 Watch Vision (+500 Energy & +50 Crystals)',
        shop_title: '💎 Faith Crystal Shop',
        shop_desc: 'Spend Faith Crystals to unlock Legendary Beasts and Divine Amulets!',
        talents_title: '🏛️ God Talent Sanctuary',
        talents_desc: 'Spend Faith Crystals to upgrade your 3 Divine Branches for permanent bonuses!',
        skin_title: '👑 Beast Lair & Customizer',
        skin_desc: 'Equip divine and abyssal accessories to boost your Creature\'s stats!',
        lang_select: '🌐 Language / 語言'
    },
    'ja-JP': {
        game_title: '善と悪：神蹟の島',
        subtitle: 'ゴッドシミュレーター＆戦略ゲーム',
        btn_start_game: '創世を開始',
        btn_tutorial: 'チュートリアル・呪文表',
        btn_menu: 'メニュー',
        btn_talents: '神の天賦樹',
        btn_skins: '神獣スキン',
        btn_shop: 'クリスタルショップ',
        btn_quests: 'デイリークエスト',
        energy_label: '祭壇エネルギー',
        god_good: '慈悲深き救世主',
        god_evil: '無情なる破壊神',
        god_neutral: '威厳ある中立神',
        notice_stage_loaded: '🌟 【{stageName}】ロード完了！右クリックで手勢、左クリックで生け贄を掴もう！',
        notice_sacrifice: '🔥 {symbol} を捧げた！ +{val} 祭壇エネルギーを獲得！',
        notice_sacrifice_human: '🔥 村人を生け贄に捧げた！ +{val} エネルギー獲得 (悪意度 +20)',
        notice_spell_cast: '✨ 手勢【{symbol}】で【{spellName}】の発動に成功！',
        ad_reward_title: '神聖なる感応 (リワード広告)',
        ad_reward_desc: '30秒のビジョンを視聴して、奇跡の報酬を獲得しましょう：',
        ad_btn_watch: '📺 視聴する (+500 エネルギー & +50 クリスタル)',
        shop_title: '💎 信仰クリスタルショップ',
        shop_desc: 'クリスタルを使って伝説の神獣やレアな護符をアンロック！',
        talents_title: '🏛️ 神の天賦聖殿',
        talents_desc: 'クリスタルを消費して3つの神格ツリーを強化し、永久ボーナスを得よう！',
        skin_title: '👑 神獣の小屋とアクセサリー',
        skin_desc: '神獣に装飾品を装備させてステータスを強化しよう！',
        lang_select: '🌐 言語選択 / Language'
    },
    'zh-CN': {
        game_title: '善与恶：神迹岛屿',
        subtitle: '上帝模拟策略游戏',
        btn_start_game: '开始创世',
        btn_tutorial: '新手教学与手势表',
        btn_menu: '游戏菜单',
        btn_talents: '天赋圣殿',
        btn_skins: '神兽装扮',
        btn_shop: '水晶商城',
        btn_quests: '每日任务',
        energy_label: '祭坛能量',
        god_good: '慈悲救世主',
        god_evil: '毁灭破坏神',
        god_neutral: '威严中立之神',
        notice_stage_loaded: '🌟 【{stageName}】已载入！请使用右键画上手势或左键抓取物件献祭！',
        notice_sacrifice: '🔥 献祭了{symbol}！获得 +{val} 祭坛能量！',
        notice_sacrifice_human: '🔥 献祭了活人村民！获得 +{val} 能量 (残忍邪恶度 +20)',
        notice_spell_cast: '✨ 通过手势【{symbol}】成功施放了【{spellName}】！',
        ad_reward_title: '观看神圣感应 (奖励型广告)',
        ad_reward_desc: '观看 30 秒神圣感应，即可获得以下奇迹奖励之一：',
        ad_btn_watch: '📺 观看感应 (+500 能量 & +50 水晶)',
        shop_title: '💎 信仰水晶商城',
        shop_desc: '使用信仰水晶解锁传说级神兽与稀有神力护符！',
        talents_title: '🏛️ 上帝天赋圣殿',
        talents_desc: '消耗信仰水晶升级您的三大神格分支，获得永久力量加成！',
        skin_title: '👑 神兽兽舍与装扮',
        skin_desc: '为您的神兽配戴神圣与深渊饰品，获得属性强化！',
        lang_select: '🌐 选择语言 / Language'
    }
};

export class I18nManager {
    constructor() {
        this.currentLang = localStorage.getItem('BW_DIVINE_LANG') || 'zh-TW';
        this.listeners = [];
    }

    setLanguage(langCode) {
        if (!CATALOGS[langCode]) return;
        this.currentLang = langCode;
        localStorage.setItem('BW_DIVINE_LANG', langCode);
        this.notifyListeners();
    }

    t(key, params = {}) {
        const catalog = CATALOGS[this.currentLang] || CATALOGS['zh-TW'];
        let str = catalog[key] || CATALOGS['zh-TW'][key] || key;
        for (const [k, v] of Object.entries(params)) {
            str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
        }
        return str;
    }

    onChange(callback) {
        this.listeners.push(callback);
    }

    notifyListeners() {
        for (const cb of this.listeners) {
            cb(this.currentLang);
        }
    }
}

export const i18n = new I18nManager();
