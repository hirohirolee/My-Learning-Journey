import random
import time
import sys

# 摩斯密碼對照表
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
    ' ': '/'
}

MORSE_TO_TEXT = {v: k for k, v in MORSE_CODE_DICT.items()}

def print_slow(text, delay=0.03):
    """模擬終端機打字效果"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def caesar_encrypt(text, shift=3):
    """凱撒加密"""
    result = ""
    for char in text.upper():
        if 'A' <= char <= 'Z':
            result += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
        else:
            result += char
    return result

def caesar_decrypt(text, shift=3):
    """凱撒解密"""
    return caesar_encrypt(text, -shift)

def morse_encrypt(text):
    """摩斯密碼加密"""
    return " ".join(MORSE_CODE_DICT.get(char.upper(), char) for char in text)

def morse_decrypt(morse_code):
    """摩斯密碼解密"""
    words = morse_code.split(" ")
    result = ""
    for word in words:
        if word == '/':
            result += ' '
        elif word in MORSE_TO_TEXT:
            result += MORSE_TO_TEXT[word]
        else:
            result += '?'
    return result

def a1z26_encrypt(text):
    """A1Z26 數字替換加密 (A=1, B=2...)"""
    result = []
    for char in text.upper():
        if 'A' <= char <= 'Z':
            result.append(str(ord(char) - ord('A') + 1))
        elif char == ' ':
            result.append("-")
        else:
            result.append(char)
    return " ".join(result)

def a1z26_decrypt(code_str):
    """A1Z26 數字替換解密"""
    tokens = code_str.split(" ")
    result = ""
    for token in tokens:
        if token == "-":
            result += " "
        elif token.isdigit():
            num = int(token)
            if 1 <= num <= 26:
                result += chr(ord('A') + num - 1)
            else:
                result += "?"
        else:
            result += token
    return result

def reverse_encrypt(text):
    """文字倒序加密"""
    return text[::-1].upper()

def reverse_decrypt(text):
    """文字倒序解密"""
    return text[::-1].upper()

# ----------------- 模式一：特務解密大挑戰 -----------------
def mode_single_player():
    print("\n" + "=" * 50)
    print("      🕵️  【特務任務：暗號解密大挑戰】 🕵️")
    print("=" * 50)
    print_slow(" headquarters: 警報！敵方特務正在傳送祕密情報！")
    print_slow(" 你的任務是破解 intercept 到的加密通訊內容！\n")
    time.sleep(1)

    levels = [
        {
            "level": 1,
            "title": "關卡 1：倒序鏡像通訊 (Reverse Cipher)",
            "plain": "SECRET AGENT",
            "encrypt_func": lambda s: reverse_encrypt(s),
            "hint": "提示：訊息被前後反轉了！試著從後面往前讀。",
            "score": 100
        },
        {
            "level": 2,
            "title": "關卡 2：凱撒偏移密碼 (Caesar Cipher - Shift 3)",
            "plain": "MISSION SUCCESS",
            "encrypt_func": lambda s: caesar_encrypt(s, 3),
            "hint": "提示：每個字母都向後移動了 3 個位置 (A -> D, B -> E)。",
            "score": 150
        },
        {
            "level": 3,
            "title": "關卡 3：數字位置密碼 (A1Z26 Cipher)",
            "plain": "TOP SECRET",
            "encrypt_func": lambda s: a1z26_encrypt(s),
            "hint": "提示：英文字母對應數字序號 (A=1, B=2, ..., Z=26)。",
            "score": 200
        },
        {
            "level": 4,
            "title": "關卡 4：古典摩斯電碼 (Morse Code)",
            "plain": "CODE RED",
            "encrypt_func": lambda s: morse_encrypt(s),
            "hint": "提示：. 代表短音(滴)，- 代表長音(答)。(如: C = -.-. , O = ---)",
            "score": 250
        },
        {
            "level": 5,
            "title": "關卡 5：終極雙層加密 (Caesar Shift 5 + Reverse)",
            "plain": "OPERATION SHADOW",
            "encrypt_func": lambda s: reverse_encrypt(caesar_encrypt(s, 5)),
            "hint": "提示：這是一套雙重加密！訊息先經過凱撒位移 5 個字母，再被前後倒序！",
            "score": 300
        }
    ]

    total_score = 0
    max_possible_score = sum(l["score"] for l in levels)

    for stage in levels:
        print("\n" + "-" * 50)
        print(f"🔒 [{stage['title']}]")
        cipher_text = stage["encrypt_func"](stage["plain"])
        print(f"📡 擷取到的加密訊號： 【 {cipher_text} 】")
        
        attempts = 3
        stage_passed = False

        while attempts > 0:
            print(f"\n請輸入解密後的明文 (剩餘嘗試次數: {attempts})")
            print("選單指令: [H] 取得提示 (扣除 30 分) | [Q] 放棄任務")
            ans = input("Your Answer > ").strip().upper()

            if ans == 'Q':
                print("⚠️ 任務已終止。")
                return

            if ans == 'H':
                print(f"💡 {stage['hint']}")
                continue

            if ans == stage["plain"].upper():
                print_slow("🎉 答對了！密碼破解成功！解密通道建立完成！", 0.02)
                earned = stage["score"] - (3 - attempts) * 20
                earned = max( earned, 50 )
                total_score += earned
                print(f"✨ 本關獲得積分: {earned} 分 (累計總分: {total_score})")
                stage_passed = True
                time.sleep(1)
                break
            else:
                attempts -= 1
                if attempts > 0:
                    print("❌ 解密失敗！訊號雜訊過高，請再試一次。")

        if not stage_passed:
            print(f"\n💥 關卡失敗！正確明文為：【 {stage['plain']} 】")
            print_slow("任務在中途被敵方發現，緊急撤退！")
            break

    print("\n" + "=" * 50)
    print("              🏆 任務結算報告 🏆")
    print("=" * 50)
    print(f"最終獲得總分：{total_score} / {max_possible_score} 分")

    if total_score == max_possible_score:
        rank = "🥇 傳奇解密大師 (Legendary Cryptographer)"
    elif total_score >= max_possible_score * 0.7:
        rank = "🥈 高級情報特務 (Senior Intelligence Agent)"
    elif total_score >= max_possible_score * 0.4:
        rank = "🥉 正式通訊特務 (Cipher Agent)"
    else:
        rank = "🔰 實習解密員 (Trainee)"

    print(f"獲頒特務階級：{rank}")
    print("=" * 50)

# ----------------- 模式二：祕密通訊工具箱 -----------------
def mode_encoder_decoder_studio():
    print("\n" + "=" * 50)
    print("      📡 【祕密通訊發射台 / 加解密工具箱】 📡")
    print("=" * 50)
    
    while True:
        print("\n請選擇操作功能：")
        print("1. 凱撒密碼 (Caesar Cipher)")
        print("2. 摩斯密碼 (Morse Code)")
        print("3. A1Z26 數字密碼 (A1Z26 Cipher)")
        print("4. 倒序鏡像密碼 (Reverse Cipher)")
        print("0. 返回主選單")
        
        choice = input("請選擇 (0-4): ").strip()
        
        if choice == '0':
            break
        elif choice not in ['1', '2', '3', '4']:
            print("無效選擇，請重新輸入。")
            continue
            
        action = input("要進行 (E)加密 還是 (D)解密？: ").strip().upper()
        if action not in ['E', 'D']:
            print("輸入錯誤，請輸入 E 或 D。")
            continue
            
        msg = input("請輸入訊息內文 (僅支援英文字母與數字): ").strip()
        
        if choice == '1':
            shift = int(input("請輸入凱撒位移數 (例如 3): ").strip() or "3")
            result = caesar_encrypt(msg, shift) if action == 'E' else caesar_decrypt(msg, shift)
        elif choice == '2':
            result = morse_encrypt(msg) if action == 'E' else morse_decrypt(msg)
        elif choice == '3':
            result = a1z26_encrypt(msg) if action == 'E' else a1z26_decrypt(msg)
        elif choice == '4':
            result = reverse_encrypt(msg) if action == 'E' else reverse_decrypt(msg)
            
        print("\n" + "★" * 40)
        print(f"轉換結果： 【 {result} 】")
        print("★" * 40)

# ----------------- 模式三：雙人對決暗語遊戲 -----------------
def mode_two_player():
    print("\n" + "=" * 50)
    print("      ⚔️  【雙人特務密碼對決】 ⚔️")
    print("=" * 50)
    print("規則：玩家A 輸入祕密訊息並選擇加密法；玩家B 試圖解開密碼！")
    print("-" * 50)
    
    print("\n[玩家 A 操作區] (請勿讓玩家 B 看螢幕)")
    secret_msg = input("請輸入祕密文字 (英文字母): ").strip().upper()
    
    print("\n選擇加密方式：")
    print("1. 凱撒密碼 (Shift 3)")
    print("2. 摩斯密碼")
    print("3. A1Z26 數字密碼")
    print("4. 倒序密碼")
    c_type = input("選擇法 (1-4): ").strip()
    
    if c_type == '1':
        encrypted = caesar_encrypt(secret_msg, 3)
    elif c_type == '2':
        encrypted = morse_encrypt(secret_msg)
    elif c_type == '3':
        encrypted = a1z26_encrypt(secret_msg)
    else:
        encrypted = reverse_encrypt(secret_msg)
        
    print("\n" * 30) # 清空螢幕畫面
    print("=" * 50)
    print("[玩家 B 挑戰區]")
    print(f"📡 玩家 A 傳送給你的加密訊息為： 【 {encrypted} 】")
    
    start_time = time.time()
    guess = input("請輸入你解出的原文字串: ").strip().upper()
    end_time = time.time()
    
    elapsed = round(end_time - start_time, 1)
    if guess == secret_msg:
        print(f"\n🎉 恭喜玩家 B 解密成功！花費時間: {elapsed} 秒")
    else:
        print(f"\n❌ 解密失敗！正確訊息應為：【 {secret_msg} 】")

# ----------------- 主選單 -----------------
def main():
    while True:
        print("\n" + "=" * 50)
        print("      🔐  祕密通訊特務解密遊戲  🔐")
        print("         (Secret Communication Game)")
        print("=" * 50)
        print("1. 🕵️ 單人模式：特務解密大挑戰 (闖關遊戲)")
        print("2. 📡 通訊發射台：加解密工具箱 (DIY 祕密訊息)")
        print("3. ⚔️ 雙人模式：特務密碼對決 (P1出題 P2解題)")
        print("4. ❓ 遊戲規則與密碼學介紹")
        print("0. 🚪 離開遊戲")
        print("=" * 50)
        
        choice = input("請輸入選項 (0-4): ").strip()
        
        if choice == '1':
            mode_single_player()
        elif choice == '2':
            mode_encoder_decoder_studio()
        elif choice == '3':
            mode_two_player()
        elif choice == '4':
            print("\n📖 【密碼學簡介】")
            print("1. 凱撒密碼 (Caesar Cipher): 將字母按字母表向後位移一定位數。")
            print("2. 摩斯密碼 (Morse Code): 用點(.)與劃(-)代表字元，常用於無線電電報通訊。")
            print("3. A1Z26 密碼: 將字母依序編號 (A=1, B=2, ..., Z=26)。")
            print("4. 倒序密碼: 將字串左右鏡像顛倒。")
            input("\n按下 Enter 鍵返回選單...")
        elif choice == '0':
            print("感謝遊玩！通訊關閉。")
            break
        else:
            print("無效選項，請重新選擇。")

if __name__ == '__main__':
    main()
