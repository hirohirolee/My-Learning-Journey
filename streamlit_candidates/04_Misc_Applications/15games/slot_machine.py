import streamlit as st

import random
import time
import sys

# 老虎機的圖案
SYMBOLS = ['🍒', '🍋', '🍉', '🔔', '💎', '7️⃣']

# 獎金賠率
PAYOUTS = {
    '7️⃣': 50,
    '💎': 20,
    '🔔': 10,
    '🍉': 5,
    '🍋': 3,
    '🍒': 2
}

def print_slow(text, delay=0.03):
    """緩慢印出文字增加期待感"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    st.write()

def spin_slots():
    """隨機轉動三次老虎機並回傳結果"""
    return [random.choice(SYMBOLS) for _ in range(3)]

def check_win(slots):
    """檢查玩家是否中獎及計算賠率"""
    if slots[0] == slots[1] == slots[2]:
        # 三個圖案都一樣
        symbol = slots[0]
        return PAYOUTS[symbol]
    elif slots[0] == slots[1] or slots[1] == slots[2] or slots[0] == slots[2]:
        # 兩個圖案一樣，退回本金或給予小獎勵
        return 1.5
    else:
        # 都沒中
        return 0

def main():
    st.write("==================================")
    st.write("      吃角子老虎機 (Slot Machine)     ")
    st.write("==================================")
    print_slow("歡迎來到幸運賭場！試試你的手氣吧！")
    st.write("中獎規則：")
    st.write(" - 3 個圖案相同：獲得高額獎金！(7️⃣ 最高 50 倍)")
    st.write(" - 2 個圖案相同：獲得 1.5 倍獎金！")
    st.write(" - 都不相同：銘謝惠顧")
    st.write("-" * 34)

    balance = 1000

    while balance > 0:
        st.write(f"\n目前餘額: ${balance}")
        
        while True:
            bet_input = st.text_input("請輸入您的下注金額 (或輸入 'q' 退出): ").strip()
            if bet_input.lower() == 'q':
                st.write(f"遊戲結束。您帶著 ${balance} 離開了賭場！")
                sys.exit()
                
            if bet_input.isdigit():
                bet = int(bet_input)
                if bet > balance:
                    st.write("餘額不足！請重新輸入。")
                elif bet <= 0:
                    st.write("下注金額必須大於 0。")
                else:
                    break
            else:
                st.write("請輸入有效的數字。")

        balance -= bet
        print_slow("\n🎰 轉動中...", 0.1)
        time.sleep(0.5)

        slots = spin_slots()
        
        # 動態顯示轉動過程
        st.write(f"  [ {slots[0]} | ? | ? ]")
        time.sleep(0.5)
        st.write(f"  [ {slots[0]} | {slots[1]} | ? ]")
        time.sleep(0.5)
        st.write(f"  [ {slots[0]} | {slots[1]} | {slots[2]} ]\n")

        multiplier = check_win(slots)
        winnings = int(bet * multiplier)

        if winnings > bet:
            if slots[0] == slots[1] == slots[2]:
                print_slow("🎉 JACKPOT！大獎！🎉", 0.05)
            st.write(f"恭喜中獎！您贏得了 ${winnings}！")
        elif winnings > 0:
            st.write(f"不錯喔！您拿回了 ${winnings}！")
        else:
            st.write("很遺憾，這次沒中獎。再接再厲！")

        balance += winnings

    st.write("\n您的餘額已經歸零，被保全請出了賭場。遊戲結束！")

if __name__ == '__main__':
    main()
