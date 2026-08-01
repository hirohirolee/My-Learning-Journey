import streamlit as st
st.title('birthday_paradox.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import datetime
import random

def getBirthdays(numberOfBirthdays):
    """回傳一個包含指定數量之隨機日期物件的串列。"""
    birthdays = []
    for i in range(numberOfBirthdays):
        # 年份在這個模擬中不重要，我們只在乎月和日
        startOfYear = datetime.date(2001, 1, 1)
        
        # 取得一年中的隨機一天
        randomNumberOfDays = datetime.timedelta(random.randint(0, 364))
        birthday = startOfYear + randomNumberOfDays
        birthdays.append(birthday)
    return birthdays

def getMatch(birthdays):
    """如果有重複的生日，回傳該日期物件；否則回傳 None。"""
    if len(birthdays) == len(set(birthdays)):
        return None  # 所有生日都不同

    # 比較每一個生日
    for a, birthdayA in enumerate(birthdays):
        for b, birthdayB in enumerate(birthdays[a + 1 :]):
            if birthdayA == birthdayB:
                return birthdayA

def main():
    st.write('''生日悖論 (Birthday Paradox)

生日悖論向我們展示了，在一個看起來人數不多的群體中，
兩個人擁有相同生日的機率其實高得驚人。
這個程式會進行蒙地卡羅模擬 (Monte Carlo simulation) 來探索這個現象。
(背景知識：在一個75人的群體中，擁有相同生日的機率高達99.9%)
''')

    # 詢問使用者要生成多少個生日
    MONTHS = ('1月', '2月', '3月', '4月', '5月', '6月',
              '7月', '8月', '9月', '10月', '11月', '12月')

    while True:
        st.write('你想生成幾個生日？ (最多 100 個)')
        response = st.text_input('> ')
        if response.isdecimal() and (0 < int(response) <= 100):
            numBDays = int(response)
            break

    st.write()
    st.write(f'正在產生 {numBDays} 個隨機生日...')
    birthdays = getBirthdays(numBDays)

    # 顯示生成的生日
    bDayStrings = []
    for i, bd in enumerate(birthdays):
        monthName = MONTHS[bd.month - 1]
        dateText = f'{monthName}{bd.day}日'
        bDayStrings.append(dateText)
    st.write(', '.join(bDayStrings))
    st.write()

    # 檢查是否有重複的生日
    match = getMatch(birthdays)

    st.write('在這個群體中，', end='')
    if match != None:
        monthName = MONTHS[match.month - 1]
        dateText = f'{monthName}{match.day}日'
        st.write(f'有人的生日同樣在 {dateText}。')
    else:
        st.write('沒有人的生日是同一天。')
    st.write()

    # 執行 10 萬次模擬
    st.write(f'現在產生 100,000 次 {numBDays} 個人的群體模擬來測試機率...')
    st.text_input('按 Enter 鍵開始...')

    st.write('開始執行模擬，請稍候...')
    simMatch = 0
    for i in range(100_000):
        # 每 10,000 次模擬回報一次進度
        if i % 10_000 == 0:
            st.write(f'{i:,} 次模擬已完成...')
        birthdays = getBirthdays(numBDays)
        if getMatch(birthdays) != None:
            simMatch = simMatch + 1
    st.write('100,000 次模擬已完成。')

    # 顯示模擬結果
    probability = round(simMatch / 100_000 * 100, 2)
    st.write(f'''
在 100,000 次模擬中，有 {numBDays} 個人的群體裡，
出現相同生日的次數為 {simMatch} 次。
這表示 {numBDays} 個人的群體中，有相同生日的機率約為 {probability}%。
這是不是比你想的還要高呢？
''')

if __name__ == '__main__':
    main()
