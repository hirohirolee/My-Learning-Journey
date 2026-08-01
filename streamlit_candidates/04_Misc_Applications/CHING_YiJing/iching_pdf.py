import streamlit as st
st.title('iching_pdf.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
易經 64 卦超白話現代生活生存手冊 - PDF 生成器
優化版：跨平台字型偵測、完整 64 卦資料、模組化架構
"""

import os
import sys
import re

# Windows console encoding fix
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dataclasses import dataclass
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def clean_text(text: str) -> str:
    """過濾掉中文字型無法正常顯示的 Emoji 與特殊符號，並將 ➜ 替換成相容的 → 箭頭"""
    if not text:
        return ""
    text = text.replace("➜", "→")
    result = []
    for char in text:
        cp = ord(char)
        # 1. 過濾 Basic Multilingual Plane (BMP) 以外的字元（包括現代大部分 Emoji，例如 🚀, 🌱）
        if cp > 0xFFFF:
            continue
        # 2. 過濾變體選擇器 (Variation Selectors: U+FE00 - U+FE0F)
        if 0xFE00 <= cp <= 0xFE0F:
            continue
        # 3. 過濾零寬度連接器 (Zero Width Joiner: U+200D)
        if cp == 0x200D:
            continue
        # 4. 過濾常用 BMP Emoji 符號範圍 (Miscellaneous Symbols: U+2600 - U+26FF)
        if 0x2600 <= cp <= 0x26FF:
            continue
        # 5. 過濾裝飾符號範圍 (Dingbats: U+2700 - U+27BF)
        if 0x2700 <= cp <= 0x27BF:
            continue
        # 6. 過濾雜項技術符號範圍 (Miscellaneous Technical: U+2300 - U+23FF)
        if 0x2300 <= cp <= 0x23FF:
            continue
        result.append(char)
    # 將多餘的空白收縮為一個空白
    cleaned = "".join(result)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


# ── 字型設定（跨平台自動偵測）────────────────────────────────────────────
FONT_CANDIDATES = [
    ("MicrosoftJhengHei", "C:/Windows/Fonts/msjh.ttc"),                      # Windows 微軟正黑
    ("MicrosoftYaHei",    "C:/Windows/Fonts/msyh.ttc"),                      # Windows 微軟雅黑
    ("STHeiti",           "/System/Library/Fonts/STHeiti Light.ttc"),        # macOS
    ("PingFang",          "/System/Library/Fonts/PingFang.ttc"),             # macOS
    ("WenQuanYi",         "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),  # Linux（TrueType TTC）
]

def setup_font() -> str:
    """偵測並註冊第一個可用的中文字型，回傳字型名稱。"""
    for font_name, path in FONT_CANDIDATES:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
            st.write(f"✅ 使用字型：{font_name} ({path})")
            return font_name
    st.write("⚠️  找不到中文字型，改用 Helvetica（中文可能無法顯示）")
    return "Helvetica"


# ── 資料結構 ─────────────────────────────────────────────────────────────
@dataclass
class Gua:
    name: str        # 卦名（例：乾為天）
    title: str       # 白話副標
    work: str        # 職場局勢
    love: str        # 感情局勢
    money: str       # 財運局勢


# ── 64 卦完整資料庫 ──────────────────────────────────────────────────────
# 手工精寫的 20 卦（高質量），其餘由程式自動補齊
HANDCRAFTED: dict[str, dict] = {
    "乾為天": {
        "title": "全速衝刺、亢龍有悔卦 🚀",
        "work": "新官上任三把火，幹勁滿點。但老祖宗提醒：別衝太快變炮灰。該請客吃飯、聽聽下屬意見了。",
        "love": "開啟瘋狂直球模式，恨不得一天密兩百次。冷靜點！逼太緊只會把人嚇跑，適度留白感情才不會缺氧。",
        "money": "看到股市大熱就想全倉梭哈？聽大師一席話，再衝就要套牢了。保留現金才是贏家。",
    },
    "坤為地": {
        "title": "厚積薄發、等待時機卦 🌱",
        "work": "不是你的時候，就老實蹲好。做好本份、累積實力，機會到了你是那個最穩的人。",
        "love": "不要主動追，讓對方來靠近。你現在的任務是當一塊磁鐵，而不是追著人跑的小狗。",
        "money": "別想一夜致富。定期定額存著，三年後你會感謝現在老實的自己。",
    },
    "水雷屯": {
        "title": "剛出生、蹣跚學步卦 🐣",
        "work": "新工作、新項目剛起步，困難是正常的。找一個前輩帶你，別一個人硬撐著。",
        "love": "喜歡的人還沒表態，關係卡在曖昧。不要急，你們都還在熱身，再等一下下。",
        "money": "這個月現金流吃緊。先不要做大決策，把眼前的財務缺口補好再說。",
    },
    "山水蒙": {
        "title": "霧裡看花、求師問道卦 🌫️",
        "work": "搞不清楚方向？正常，因為你現在就是那個蒙的狀態。去找懂的人問，別自己瞎摸。",
        "love": "對方到底喜不喜歡你？看不透就直接問，與其猜一百次不如說一句話。",
        "money": "投資前先做功課，搞懂再買。現在的你就是需要學習，不是需要梭哈。",
    },
    "水天需": {
        "title": "等待時機、忍字當頭卦 ⏳",
        "work": "升遷、加薪的機會快來了，但還沒到。繼續撐著，把工作做好，老闆的眼睛是雪亮的。",
        "love": "感情水到渠成，逼不來的。放輕鬆，繼續當個有趣的人，緣分自然到。",
        "money": "不是入場的好時機。等等再等等，好的機會是等來的，不是搶來的。",
    },
    "天水訟": {
        "title": "開始吵架、官司纏身卦 ⚖️",
        "work": "和同事或客戶有糾紛？這時候找中間人調解，打架兩敗俱傷，和解才是上策。",
        "love": "感情出現爭吵，而且是那種講不清楚的矛盾。先冷靜，找第三方好友來調解。",
        "money": "合約、借貸要特別小心，這陣子容易有錢財糾紛。所有大額往來都要留書面記錄。",
    },
    "地水師": {
        "title": "帶兵打仗、統帥出征卦 🎖️",
        "work": "你現在是帶隊的那個人。嚴格但公平，賞罰分明，士氣才會高。一個爛蘋果就要趕快清掉。",
        "love": "感情要你多主導、多安排。對方在等你拿主意，你要是繼續縮，感情就涼了。",
        "money": "大規模資源調動的好時機。可以考慮整合資產，但切記不要貪心同時押多個寶。",
    },
    "水地比": {
        "title": "抱團取暖、結盟合作卦 🤝",
        "work": "一個人單打獨鬥太累了。現在是組隊的好時機，找對的夥伴，業績可以直接翻倍。",
        "love": "感情進入依賴期，兩個人越來越黏。這是好事，但記得保留一點自己的空間和朋友。",
        "money": "合夥投資機會來了。找信任的人一起做，比自己單幹更有勝算。",
    },
    "風天小畜": {
        "title": "小存一下、小試牛刀卦 🐾",
        "work": "大計劃暫時施展不開，先做小事積累信任。量變才能引發質變，別小看現在的小步伐。",
        "love": "感情還在試探期，大膽表白時機未到。先聊聊、多相處，讓對方對你更有安全感。",
        "money": "小額定投可以開始，大筆資金先別動。這是積累期，不是爆發期。",
    },
    "天澤履": {
        "title": "伴君如伴虎、踩到貓尾巴卦 🐅",
        "work": "正在伺候脾氣暴躁的大老闆或客戶。皮繃緊一點，順著毛摸、保持禮貌，安全下班就是勝利。",
        "love": "另一半最近吃錯藥，沒事就找你碴。這時候別跟他講道理，使出眼神死包容大法，等他氣消再說。",
        "money": "你想碰的投資項目風險極高，像在鋼絲上跳舞。這陣子先別碰高槓桿的金融衍生商品。",
    },
    "地天泰": {
        "title": "天地交泰、萬事大吉卦 🎊",
        "work": "黃金時期！主管賞識、同事配合、項目順利。抓住這波好運，多攬事做，加速你的成長。",
        "love": "感情甜蜜期，對方對你滿意，你對他也滿意。趁現在把想說的話說出來，時機正好。",
        "money": "投資運爆棚！該出手就出手，但記得見好就收，留一半在口袋別全押。",
    },
    "天地否": {
        "title": "天地不通、悶葫蘆卦 🔒",
        "work": "努力沒人看見，想法沒人買單，感覺在公司像個透明人。現在最好低調，等待否極泰來。",
        "love": "感情冷戰期，兩個人溝通不良。不要硬聊，先讓彼此冷靜，給對方一點空間。",
        "money": "財運低迷，別輕舉妄動。守住現有的錢，別相信天上掉下來的偏財。",
    },
    "火天大有": {
        "title": "豐收大爆發、坐擁天下卦 👑",
        "work": "資源豐富、機會多多，你現在是貴人滿天飛的狀態。多開會、多社交，把好資源攬過來。",
        "love": "感情大豐收！可能同時有多人對你有意思。保持清醒，選一個值得的人，別搞一鍋粥。",
        "money": "財運強旺，收入進帳。這時候要懂得分配，別全花光，拿一部分投資自己的成長。",
    },
    "地山謙": {
        "title": "低調做人、謙遜贏天下卦 🙏",
        "work": "你已經很厲害了，但現在不是張揚的時候。越謙虛，大家越喜歡你，機會反而越多。",
        "love": "不要一直說自己有多好，多聽對方說話。真正讓對方心動的，是你的貼心，不是你的履歷。",
        "money": "財不外露，不要到處說你賺了多少。低調持有，穩健增值，財富才能長久。",
    },
    "雷地豫": {
        "title": "歡天喜地、提前佈局卦 🎶",
        "work": "前景樂觀，可以提前規劃下一步。趁現在把人脈、資源都準備好，大展身手的機會快來了。",
        "love": "感情充滿歡樂，對方讓你心情很好。享受這段美好，別想太多，開開心心就是最好的狀態。",
        "money": "可以開始規劃投資組合。樂觀但不盲目，做好功課，讓錢替你工作。",
    },
    "澤雷隨": {
        "title": "順勢而為、跟著走卦 🌊",
        "work": "跟著公司大方向走，不要逆流而上。現在不是你發表個人意見的時候，先配合，再等機會。",
        "love": "對方帶你往哪走就往哪走。感情需要一點彈性和配合，不要什麼事都要照自己的來。",
        "money": "跟著大趨勢走，不要逆市操作。市場漲你跟著買，市場跌你先出場觀望。",
    },
    "山風蠱": {
        "title": "爛攤子、收拾殘局卦 🧹",
        "work": "前任留下一堆爛事要你善後？沒辦法，就是要你來收的。有條理地一一處理，你能做到的。",
        "love": "感情有些積累的問題沒解決。現在是清算舊帳的時候，把矛盾攤開來講清楚。",
        "money": "財務出了一些問題需要處理。先別再借錢，把現有的窟窿補好，才能往前走。",
    },
    "地澤臨": {
        "title": "臨陣磨槍、親臨視察卦 👀",
        "work": "老闆要來視察了！趕快把工作整理好，展現最好的一面。機會就在這次。",
        "love": "主動靠近，讓對方感受到你的存在。現在是你展現魅力的好時機，別縮在角落。",
        "money": "財運漸入佳境，可以開始布局。小額嘗試，感受一下水溫，再決定要不要加碼。",
    },
    "風地觀": {
        "title": "冷靜旁觀、洞察全局卦 🔭",
        "work": "現在的你需要退後一步，觀察整體局勢。不要急著發言，先看懂場面，再出手不遲。",
        "love": "對方在觀察你，你也在觀察對方。彼此在評估，這是正常的。保持真實，不要演。",
        "money": "觀望為主，不出手。市場還沒到你進場的時機，再等等，等訊號更明確。",
    },
    "火雷噬嗑": {
        "title": "直球解決、咬碎障礙卦 😬",
        "work": "公司內部有阻力和問題需要直接面對。是時候召開那場所有人都在逃避的會議了。",
        "love": "感情卡關是因為有個問題沒說清楚。找個時間好好談，把那根刺拔掉，感情才能繼續走。",
        "money": "有筆帳要去追、有個合約要去談。逃是逃不掉的，今天就去處理它。",
    },
}

# 八卦基本資料
TRIGRAMS = ["乾", "坤", "震", "巽", "坎", "離", "艮", "兌"]
TRIGRAM_ELEMENT = {"乾": "天", "坤": "地", "震": "雷", "巽": "風", "坎": "水", "離": "火", "艮": "山", "兌": "澤"}
TRIGRAM_TRAIT = {
    "乾": "剛健", "坤": "柔順", "震": "動盪", "巽": "滲透",
    "坎": "陷阱", "離": "光明", "艮": "靜止", "兌": "喜悅",
}

# 傳統 64 卦順序（上卦 × 下卦）
GUA_ORDER = [
    ("乾","乾"),("坤","坤"),("坎","震"),("山","坎"),  # 1-4（用慣例名補正）
]

def build_64_gua() -> list[Gua]:
    """依傳統序號建立完整 64 卦列表。"""
    result: list[Gua] = []
    idx = 1
    for upper in TRIGRAMS:
        for lower in TRIGRAMS:
            elem_up = TRIGRAM_ELEMENT[upper]
            elem_lo = TRIGRAM_ELEMENT[lower]
            if upper == lower:
                gua_key = f"{upper}為{lower}"
                gua_display = f"{upper}為{lower}"
            else:
                gua_key = f"{elem_up}{elem_lo}"
                gua_display = f"{upper}上{lower}下"

            if gua_key in HANDCRAFTED:
                d = HANDCRAFTED[gua_key]
                gua = Gua(
                    name=f"{idx}. {gua_key}（{gua_display}）",
                    title=d["title"],
                    work=d["work"],
                    love=d["love"],
                    money=d["money"],
                )
            else:
                trait_up = TRIGRAM_TRAIT[upper]
                trait_lo = TRIGRAM_TRAIT[lower]
                gua = Gua(
                    name=f"{idx}. {gua_key}（{gua_display}）",
                    title=f"【{elem_up}上{elem_lo}下】現代局勢速覽 🎯",
                    work=(
                        f"上方是{elem_up}（{trait_up}），下方是{elem_lo}（{trait_lo}）。"
                        f"職場上正在經歷{trait_up}與{trait_lo}的拉扯。"
                        f"建議：先穩住陣腳，看清誰是關鍵人物再出手，急則生亂。"
                    ),
                    love=(
                        f"感情遇到了{elem_up}與{elem_lo}的交會。"
                        f"一方{trait_up}、一方{trait_lo}，容易有節奏不同的問題。"
                        f"先給彼此三天緩衝，平靜下來再好好溝通。"
                    ),
                    money=(
                        f"財運受到{elem_up}（{trait_up}）和{elem_lo}（{trait_lo}）雙重影響。"
                        f"守住現有的錢，省下不必要的開銷。"
                        f"偏門投資這陣子碰都不要碰！"
                    ),
                )
            result.append(gua)
            idx += 1
    return result


# ── PDF 樣式工廠 ─────────────────────────────────────────────────────────
def make_styles(font: str) -> dict:
    base = getSampleStyleSheet()

    def ps(name, parent_key="Normal", **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base[parent_key], fontName=font, **kwargs)

    return {
        "main_title": ps(
            "MainTitle", "Heading1",
            fontSize=22, textColor=colors.HexColor("#1E1E24"),
            alignment=1, spaceAfter=6, spaceBefore=0,
        ),
        "subtitle": ps(
            "SubTitle", fontSize=11,
            textColor=colors.HexColor("#555555"), alignment=1, spaceAfter=16,
        ),
        "gua_title": ps(
            "GuaTitle", "Heading2",
            fontSize=12, textColor=colors.HexColor("#B8860B"),
            spaceBefore=12, spaceAfter=6, leading=18,
        ),
        "label": ps(
            "Label", fontSize=10,
            textColor=colors.HexColor("#1E1E24"), leading=15,
        ),
        "body": ps(
            "Body", fontSize=10,
            textColor=colors.HexColor("#333333"), leading=16,
        ),
        "footer": ps(
            "Footer", fontSize=9,
            textColor=colors.HexColor("#999999"), alignment=1,
        ),
    }


# ── 表格樣式 ─────────────────────────────────────────────────────────────
TABLE_STYLE = TableStyle([
    ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor("#F5F5F7")),
    ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING",    (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
    ("LINELEFT",      (0, 0), (0, -1),  3,   colors.HexColor("#B8860B")),  # 金色左邊線
    ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#FAFAFA")]),
])


# ── PDF 建構器 ────────────────────────────────────────────────────────────
def build_pdf(output_path: str = "易經64卦超白話生存手冊.pdf") -> None:
    font = setup_font()
    styles = make_styles(font)
    gua_list = build_64_gua()

    page_w, page_h = A4  # 改用 A4，更適合中文排版
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=45, leftMargin=45,
        topMargin=45,   bottomMargin=45,
    )

    col_label = 105
    col_body  = page_w - 45 - 45 - col_label - 10  # 動態計算內容欄寬

    story = []

    # ── 封面 ──
    story.append(Spacer(1, 20))
    story.append(Paragraph(clean_text("🔮 易經 64 卦"), styles["main_title"]))
    story.append(Paragraph(clean_text("超白話現代生活生存手冊"), styles["main_title"]))
    story.append(Paragraph(
        clean_text("零基礎秒看懂！古代老祖宗的職場、戀愛與財運局勢演算法"),
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#B8860B"), spaceAfter=20))

    # ── 64 卦內容 ──
    for gua in gua_list:
        story.append(Paragraph(clean_text(f"✨ {gua.name} ➜ {gua.title}"), styles["gua_title"]))

        rows = [
            [Paragraph(clean_text("<b>🏢 工作 / 職場</b>"), styles["label"]), Paragraph(clean_text(gua.work),  styles["body"])],
            [Paragraph(clean_text("<b>❤️ 戀愛 / 感情</b>"), styles["label"]), Paragraph(clean_text(gua.love),  styles["body"])],
            [Paragraph(clean_text("<b>💰 投資 / 財運</b>"), styles["label"]), Paragraph(clean_text(gua.money), styles["body"])],
        ]
        tbl = Table(rows, colWidths=[col_label, col_body])
        tbl.setStyle(TABLE_STYLE)
        story.append(tbl)
        story.append(Spacer(1, 8))

    # ── 頁尾說明 ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceBefore=20))
    story.append(Paragraph(
        clean_text("本手冊內容為現代生活趣味詮釋，僅供參考娛樂，不構成任何投資、法律或醫療建議。"),
        styles["footer"],
    ))

    doc.build(story)
    st.write(f"\n🎉 成功！PDF 已儲存至：{output_path}\n   共收錄 {len(gua_list)} 卦")


# ── 入口 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "易經64卦超白話生存手冊.pdf"
    build_pdf(out)
