import streamlit as st
st.title('0604.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
BMI=體重(公斤)/身高(公尺)的平方

讓用戶輸入體重公斤及身高公分，輸出BMI數值至小數第二位及對應標準
輸出格式: 
BMI: XXX(kg) / (#.## x #.##)  = ####.## 

"""
"""
k = int(st.text_input("請輸入體重(公斤):"))
g = int(st.text_input("請輸入身高(公分):")) 
BMI = k / (g * g)

st.write(f"BMI={k:4.1f} / ({g:3.2f} x {g:3.2f}) = {BMI:6.2f}")

"""
"""
承上題 男性標準值:22~28  女性標準值:18~25
請依據BMI 輸出，過輕，適中，偏重
格式:
BMI=###.# / (#.##X #.##) = ####.## (標準體重)

"""
"""
k = float(st.text_input("請輸入體重(公斤):"))
g = float(st.text_input("請輸入身高(公分):")) / 100  # 直接轉為公尺
ged = st.text_input("請輸入性別(M:男性/F:女性): ")
BMI = k / (g * g)

st.write(f"BMI={k:4.1f} / ({g:3.2f} x {g:3.2f}) = {BMI:6.2f}")

if ged=="M":
    if BMI <22:
        st.write("體重過輕")
    elif BMI >=22 and BMI <25:
        st.write("標準體重")
    elif BMI >=25 and BMI <28:
        st.write("體重過重")
    else:
        st.write("肥胖")

elif ged=="F":
    if BMI <18:
        st.write("體重過輕")
    elif BMI >=18 and BMI <25:
        st.write("標準體重")
    elif BMI >=25 and BMI <27:
        st.write("體重過重")
    else:
        st.write("體重過重")

"""
"""
某停車場前15分鐘免費，第一小時40元，之後每30分鐘20元，當日最高不超過100元
請輸入停車時間(分鐘)，計算應收費金額
輸出格式
停車時間       計算金額     應付金額
--------     ---------    ----------
12345678     12345678     12345678  

"""
"""
min = int(st.text_input("請輸入停車時間(分鐘): "))



# 1. 計算金額 (依照規則計算，不考慮上限 100 元)
if min <= 15:
    calc_fee = 0
elif min <= 60:
    calc_fee = 40
else:
    extra_min = min - 60
    # math.ceil() 可以直接做「無條件進位」，把不足 30 分鐘的算作 1 個單位
    intervals = extra_min // 30
    calc_fee = 40 + intervals * 20

# 2. 應付金額 (當日最高不超過 100 元)
if calc_fee > 200:
    pay_fee = 200
else:
    pay_fee = calc_fee

# 3. 輸出格式化結果 (對齊欄位寬度)
st.write("停車時間       計算金額     應付金額")
st.write("--------     ---------    ----------")
st.write(f"{min:<8d}     {calc_fee:<9d}    {pay_fee:<10d}")

"""
"""
tot_min = int(st.text_input("請輸入停車總分鐘數(分鐘): "))
tot_amt = pay_amt = 0

if tot_min>15:
    tot_amt = (tot_min//30)*20
    if tot_min % 30 > 0:
        tot_amt =tot_amt + 20

    if tot_amt<40:
        pay_amt = 40
    elif tot_amt>180:
        pay_amt=180
    else:
        pay_amt=tot_amt

st.write("停車時間       計算金額     應付金額")
st.write("--------     ---------    ----------")
st.write(f"{tot_min:8d}     {tot_amt:9d}    {pay_amt:10d}")

"""
"""
min_val = int(st.text_input("請輸入停車時間(分鐘): "))

# 1. 扣除車證免費時間 (4小時 = 240分鐘)
free_min = 240
actual_min = min_val - free_min

# 確保時間不會小於 0
if actual_min < 0:
    actual_min = 0

# 2. 計算金額
if actual_min <= 15:
    calc_fee = 0
elif actual_min <= 60:
    calc_fee = 40
else:
    # 扣除前 60 分鐘後的剩餘時間
    extra_min = actual_min - 60
    
    # 手動實作無條件進位：
    # 如果餘數 > 0，單位數就要 +1
    intervals = extra_min // 30
    if extra_min % 30 > 0:
        intervals += 1
        
    calc_fee = 40 + intervals * 20

# 3. 設定最高上限 100 元
if calc_fee > 100:
    pay_fee = 100
else:
    pay_fee = calc_fee

# 4. 輸出結果
st.write(f"停車時間: {min_val} 分鐘")
st.write(f"實際計算時間: {actual_min} 分鐘")
st.write("----------------------------")
st.write("停車時間     計算金額    應付金額")
st.write(f"{min_val:<8d}     {calc_fee:<9d}    {pay_fee:<10d}")"""


"""



"""
"""
夏季費率 (Summer Rates):

0 ~ 120 度: 1.63 元/度

121 ~ 330 度 (區間長度 210): 2.38 元/度

331 ~ 500 度 (區間長度 170): 3.52 元/度

501 ~ 700 度 (區間長度 200): 4.80 元/度

701 ~ 1000 度 (區間長度 300): 5.66 元/度

1001 度以上: 6.41 元/度

非夏季費率 (Non-Summer Rates):

0 ~ 120 度: 1.63 元/度

121 ~ 330 度: 2.10 元/度

331 ~ 500 度: 2.89 元/度

501 ~ 700 度: 3.94 元/度

701 ~ 1000 度: 4.60 元/度

1001 度以上: 5.03 元/度

格式:
區間         度數  單價   金額
----------   ----  ----  ---------
1234~1234    1234  1.23   123456789.123

"""

tot_val = int(st.text_input("請輸入總用電度數: "))
is_summ = st.text_input("是否為夏季電費(Y/N): ")
# --- 分配 0~120 應計價度數
if   tot_val <= 120:
    v_120 = tot_val
else:
    v_120 = 120
# --- 分配 121~330 應計價度數
tot_val = tot_val - v_120
if tot_val <= (330-120):
    v_330 = tot_val
else:
    v_330 = (330 - 120)
# --- 分配 331~500 應計價度數
tot_val = tot_val - v_330
if tot_val <= (500-330):
    v_500 = tot_val
else:
    v_500 = (500 - 330)
# --- 分配 501~700 應計價度數
tot_val = tot_val - v_500
if tot_val <= (700-500):
    v_700 = tot_val
else:
    v_700 = (700 - 500)
# --- 分配 701~1000 應計價度數
tot_val = tot_val - v_700
if tot_val <= (1000-700):
    v_1000 = tot_val
else:
    v_1000 = (1000 - 700)
# --- 分配 1001 以上應計價度數
tot_val = tot_val - v_1000
v_1001 = tot_val
# --- 處裡單價
if is_summ == "Y":
    unp_120  = 1.63
    unp_330  = 2.38
    unp_500  = 3.52
    unp_700  = 4.80
    unp_1000 = 5.66
    unp_1001 = 6.41
else:
    unp_120  = 1.63
    unp_330  = 2.10
    unp_500  = 2.89
    unp_700  = 3.94
    unp_1000 = 4.60
    unp_1001 = 5.03
# ----
tot_amt = v_120  * unp_120  + \
          v_330  * unp_330  + \
          v_500  * unp_500  + \
          v_700  * unp_700  + \
          v_1000 * unp_1000 + \
          v_1001 * unp_1001 

    
st.write("區間        度數  單價 金額")
st.write("----------- ---- ---- ----------")
st.write(f"{0   :4d} ~ {120 :4d} {v_120 :4d} {unp_120 :3.2f} {v_120  * unp_120 :9.1f}")
st.write(f"{121 :4d} ~ {330 :4d} {v_330 :4d} {unp_330 :3.2f} {v_330  * unp_330 :9.1f}")
st.write(f"{331 :4d} ~ {500 :4d} {v_500 :4d} {unp_500 :3.2f} {v_500  * unp_500 :9.1f}")
st.write(f"{501 :4d} ~ {700 :4d} {v_700 :4d} {unp_700 :3.2f} {v_700  * unp_700 :9.1f}")
st.write(f"{701 :4d} ~ {1000:4d} {v_1000:4d} {unp_1000:3.2f} {v_1000 * unp_1000:9.1f}")
st.write(f"{1001:4d} ~ 以上 {v_1001:4d} {unp_1001:3.2f} {v_1001 * unp_1001:9.1f}")

"""

tot_val = int(st.text_input("請輸入總用電度數: "))
is_summer = st.text_input("是否為夏季 (Y/N): ")
# 1. 根據是否為夏季，設定各區間單價
if is_summer == "Y" or is_summer == "y":
    r1, r2, r3, r4, r5, r6 = 1.63, 2.38, 3.52, 4.80, 5.66, 6.41
else:
    r1, r2, r3, r4, r5, r6 = 1.63, 2.10, 2.89, 3.94, 4.60, 5.03

# 2. 計算各區間內佔用的度數
w1 = w2 = w3 = w4 = w5 = w6 = 0

if tot_val <= 120:
    w1 = tot_val
elif tot_val <= 330:
    w1 = 120
    w2 = tot_val - 120
elif tot_val <= 500:
    w1 = 120
    w2 = 210
    w3 = tot_val - 330
elif tot_val <= 700:
    w1 = 120
    w2 = 210
    w3 = 170
    w4 = tot_val - 500
elif tot_val <= 1000:
    w1 = 120
    w2 = 210
    w3 = 170
    w4 = 200
    w5 = tot_val - 700
else:
    w1 = 120
    w2 = 210
    w3 = 170
    w4 = 200
    w5 = 300
    w6 = tot_val - 1000

# 3. 計算各區間金額
fee1 = w1 * r1
fee2 = w2 * r2
fee3 = w3 * r3
fee4 = w4 * r4
fee5 = w5 * r5
fee6 = w6 * r6

# 4. 格式化輸出對齊的表格
st.write("區間         度數  單價   金額")
st.write("----------   ----  ----  ---------")

if w1 > 0:
    st.write(f"{'0~120':<10}   {w1:<4.0f}  {r1:<4.2f}  {fee1:<9.3f}")
if w2 > 0:
    st.write(f"{'121~330':<10}   {w2:<4.0f}  {r2:<4.2f}  {fee2:<9.3f}")
if w3 > 0:
    st.write(f"{'331~500':<10}   {w3:<4.0f}  {r3:<4.2f}  {fee3:<9.3f}")
if w4 > 0:
    st.write(f"{'501~700':<10}   {w4:<4.0f}  {r4:<4.2f}  {fee4:<9.3f}")
if w5 > 0:
    st.write(f"{'701~1000':<10}   {w5:<4.0f}  {r5:<4.2f}  {fee5:<9.3f}")
if w6 > 0:
    st.write(f"{'1001~':<10}   {w6:<4.0f}  {r6:<4.2f}  {fee6:<9.3f}")

"""