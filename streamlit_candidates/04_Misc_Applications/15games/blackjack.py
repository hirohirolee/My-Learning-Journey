import streamlit as st
st.title('blackjack.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import random
import sys

# 定義花色符號
HEARTS = chr(9829)
DIAMONDS = chr(9830)
SPADES = chr(9824)
CLUBS = chr(9827)

def main():
    st.write('''二十一點 (Blackjack)
    
規則：
  試著讓手中的牌點數總和盡可能接近 21 點，但不能超過 21 點。
  J、Q、K 算作 10 點。
  A 可以算作 1 點或 11 點。
  莊家必須在點數小於 17 點時繼續拿牌。
''')

    money = 5000
    while True: # 主遊戲迴圈
        if money <= 0:
            st.write("你已經破產了！")
            st.write("很高興與你遊玩，再見！")
            sys.exit()
            
        st.write(f'你目前擁有 {money} 元。')
        bet = getBet(money)
        if bet == 'QUIT':
            break

        deck = getDeck()
        dealerHand = [deck.pop(), deck.pop()]
        playerHand = [deck.pop(), deck.pop()]

        st.write('賭注:', bet)
        
        while True: # 玩家回合迴圈
            displayHands(playerHand, dealerHand, False)
            st.write()

            if getHandValue(playerHand) > 21:
                break

            move = getMove(playerHand, money - bet)
            
            if move == 'D':
                additionalBet = bet
                bet += additionalBet
                st.write(f"你加倍了賭注，現在賭注為 {bet}。")
                playerHand.append(deck.pop())
                break
            elif move == 'H':
                playerHand.append(deck.pop())
            elif move == 'S':
                break

        # 處理莊家回合及結算
        if getHandValue(playerHand) <= 21:
            while getHandValue(dealerHand) < 17:
                st.write('莊家拿牌...')
                dealerHand.append(deck.pop())
                displayHands(playerHand, dealerHand, False)

            displayHands(playerHand, dealerHand, True)

            playerValue = getHandValue(playerHand)
            dealerValue = getHandValue(dealerHand)

            if dealerValue > 21:
                st.write(f'莊家爆牌了！你贏了 {bet} 元！')
                money += bet
            elif playerValue > dealerValue:
                st.write(f'你贏了 {bet} 元！')
                money += bet
            elif playerValue < dealerValue:
                st.write('莊家輸了，莊家點數較大！') # typo correction
                st.write('莊家贏了！')
                money -= bet
            else:
                st.write('平手，退回賭注。')

        else:
            displayHands(playerHand, dealerHand, False)
            st.write('你爆牌了！')
            money -= bet

        st.write()
        st.text_input('按下 Enter 繼續...')
        st.write('\n\n')

def getBet(maxBet):
    """詢問玩家下注金額。"""
    while True:
        st.write(f'你想下注多少？ (1-{maxBet}，或輸入 QUIT 離開)')
        bet = st.text_input('> ').upper().strip()
        if bet == 'QUIT':
            return 'QUIT'

        if not bet.isdecimal():
            continue

        bet = int(bet)
        if 1 <= bet <= maxBet:
            return bet

def getDeck():
    """回傳一副洗好的牌。每個牌是一個 (數字, 花色) 的 tuple。"""
    deck = []
    for suit in (HEARTS, DIAMONDS, SPADES, CLUBS):
        for rank in range(2, 11):
            deck.append((str(rank), suit))
        for rank in ('J', 'Q', 'K', 'A'):
            deck.append((rank, suit))
    random.shuffle(deck)
    return deck

def displayHands(playerHand, dealerHand, showDealerHand):
    """顯示玩家和莊家的牌。如果 showDealerHand 為 False，隱藏莊家的第一張牌。"""
    st.write()
    if showDealerHand:
        st.write('莊家的牌:', getHandValue(dealerHand))
        displayCards(dealerHand)
    else:
        st.write('莊家的牌: ???')
        # 顯示隱藏牌
        displayCards([dealerHand[0], ('?', '?')])

    st.write('你的牌:', getHandValue(playerHand))
    displayCards(playerHand)

def getHandValue(cards):
    """計算並回傳牌的總點數。"""
    value = 0
    numberOfAces = 0

    for card in cards:
        rank = card[0]
        if rank == 'A':
            numberOfAces += 1
        elif rank in ('K', 'Q', 'J'):
            value += 10
        elif rank != '?':
            value += int(rank)

    # 加上 A 的點數 (1 或 11)
    value += numberOfAces # 先當作 1 點
    for i in range(numberOfAces):
        # 如果加上 10 點不會爆牌，就當作 11 點
        if value + 10 <= 21:
            value += 10

    return value

def displayCards(cards):
    """以 ASCII 藝術顯示卡牌。"""
    rows = ['', '', '', '', '']
    for i, card in enumerate(cards):
        rows[0] += ' ___  '
        if card[0] == '?': # 隱藏的牌
            rows[1] += '|## | '
            rows[2] += '|###| '
            rows[3] += '|_##| '
        else:
            rank, suit = card
            rows[1] += f'|{rank.ljust(2)} | '
            rows[2] += f'| {suit} | '
            rows[3] += f'|_{rank.rjust(2, "_")}| '

    for row in rows:
        st.write(row)

def getMove(playerHand, money):
    """詢問玩家的動作：拿牌、停牌或雙倍下注。"""
    while True:
        moves = ['(H) 拿牌', '(S) 停牌']
        
        # 只有在第一回合且有足夠的錢時才可以雙倍下注
        if len(playerHand) == 2 and money > 0:
            moves.append('(D) 雙倍下注')
            
        movePrompt = ', '.join(moves) + '> '
        move = st.text_input(movePrompt).upper()
        if move in ('H', 'S'):
            return move
        if move == 'D' and '(D) 雙倍下注' in moves:
            return move

if __name__ == '__main__':
    main()
