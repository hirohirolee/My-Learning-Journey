import streamlit as st

import random
import time

def main():
    st.write("==================================")
    st.write("      歡迎來到腦筋急轉彎遊戲！      ")
    st.write("==================================")
    st.write("輸入 'q' 隨時退出遊戲。")
    st.write("有些題目可能是諧音梗，準備好了嗎？")
    st.write("-" * 34)
    time.sleep(1)

    teasers = [
        {"question": "什麼東西越洗越髒？", "answer": "水"},
        {"question": "什麼人一年只工作一天？", "answer": "聖誕老人"},
        {"question": "什麼門永遠關不上？", "answer": "球門"},
        {"question": "什麼東西打碎了才能用？", "answer": "雞蛋"},
        {"question": "有一頭頭朝北的牛，牠向右轉原地轉三圈，然後向後轉原地轉三圈，接著再往右轉，這時候牠的尾巴朝哪？", "answer": "朝下"},
        {"question": "什麼布剪不斷？", "answer": "瀑布"},
        {"question": "什麼海沒有水？", "answer": "辭海"},
        {"question": "兩對父子去買帽子，為什麼只買了三頂？", "answer": "因為是祖孫三代"},
        {"question": "什麼鼠最愛乾淨？", "answer": "環保署"},
        {"question": "狼來了（猜一水果）？", "answer": "楊桃"},
        {"question": "羊來了（猜一水果）？", "answer": "草莓"},
        {"question": "什麼車寸步難行？", "answer": "風車"},
        {"question": "黑人為什麼喜歡吃白巧克力？", "answer": "怕咬到自己的手指"},
        {"question": "什麼動物最沒有方向感？", "answer": "麋鹿"}
    ]

    random.shuffle(teasers)

    score = 0
    total = 0

    for teaser in teasers:
        st.write(f"\n問題: {teaser['question']}")
        user_input = st.text_input("你的答案: ").strip()

        if user_input.lower() == 'q':
            st.write("\n遊戲結束！")
            break

        if user_input == teaser['answer'] or (teaser['answer'] in user_input and len(user_input) <= len(teaser['answer']) + 2):
            # 允許稍微冗長的答案，例如「是水」
            st.write("答對了！太厲害了！")
            score += 1
        else:
            st.write(f"答錯了！正確答案是: {teaser['answer']}")
        
        total += 1
        time.sleep(0.5)

    st.write("\n" + "=" * 34)
    if total > 0:
        st.write(f"你的總得分是: {score} / {total}")
        if score == total:
            st.write("你是腦筋急轉彎大師！")
        elif score >= total / 2:
            st.write("不錯喔，腦筋轉得挺快的！")
        else:
            st.write("再接再厲！多動動腦筋有益健康！")
    else:
        st.write("這麼快就放棄啦？下次再來挑戰吧！")

if __name__ == '__main__':
    main()
