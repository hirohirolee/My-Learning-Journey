
"""
讓用戶輸入一串英文字
讓輸入的內容中，將每一個英文字母向右3個字母，例如A=>D, g=>j, z=>c

步驟:
1. 讓用戶輸入一串英文字
2. 知道文字在哪個位置
3. 將文字向右移動3個位置
4. 可能會超出範圍,所以要考慮到==>把值%(len(base))
5. 還要考慮到大小寫




"""
"""
base = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 定義大寫英文字母表作為基準值
offset = 3  # 設定偏移量（向右移動 3 個字母）

# 讓使用者輸入字串，並透過 .upper() 強制轉換為大寫
orgstr = input("請輸入一段大寫英文字: ").upper()
newstr = ""  # 初始化用來儲存加密後新字串的變數

# 逐一處理輸入字串中的每個字元
for c in orgstr:
    if c not in base:
        # 如果字元不是英文字母（例如空格、標點符號），則直接保留原字元
        newstr = newstr + c
    else:
        # 尋找目前字元在字母表中的索引位置
        ndx = base.index(c)
        # 將索引值加上偏移量
        ndx = ndx + offset
        # 如果超出字母表長度範圍，則減去字母表長度以循環回開頭
        if ndx >= len(base):
            ndx = ndx - len(base)
        # 將偏移後的新字元加入新字串中
        newstr = newstr + base[ndx]

# 輸出結果
print("原字串: ", orgstr)
print("新字串: ", newstr)
"""

"""
import random  # 匯入隨機模組以打亂字母表

base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"  # 定義大小寫英文字母表作為基準值
random.seed(10)  # 設定隨機數種子為 10，確保每次執行程式時隨機打亂的字母順序皆相同（具可重現性）

# 從 base 中不重複抽樣 len(base) 個字元，相當於將字母表完全隨機打亂（洗牌）
base = random.sample(base, len(base))
print(base)  # 印出打亂後作為加密對照表的列表

offset = 3  # 設定偏移量（在打亂的字母表中向右移動 3 個位置）

# 讓使用者輸入字串
orgstr = input("請輸入一段英文字: ")
newstr = ""  # 初始化用來儲存加密後新字串的變數

# 逐一處理輸入字串中的每個字元
for c in orgstr:
    if c not in base:
        # 如果字元不是英文字母（例如空格、數字、標點符號），則直接保留原字元
        newstr = newstr + c
    else:
        # 尋找目前字元在打亂後的對照表中的索引位置
        ndx = base.index(c)
        # 將索引值加上偏移量
        ndx = ndx + offset
        # 如果超出對照表長度範圍（52），則減去長度以循環回開頭
        if ndx >= len(base):
            ndx = ndx - len(base)
        # 將偏移後的新字元加入新字串中
        newstr = newstr + base[ndx]

# 輸出結果
print("原字串: ", orgstr)
print("新字串: ", newstr)

"""


"""
座位編排
依照下列用戶姓名,讓用戶輸入每排座位人數(2~7)，依照輸入每排座位人數將座位表排出
輸出格式(假設3人一排):
    Name        Name       Name
----------  ---------- ----------   
1234567890  1234567890  1234567890

users = ("Aaric", "Abbot", "Ace", "Ackerley", "Adam", "Adney", 
         "Bab", "Bamboo", "Ben", "Bunny", "Betty", "Baha", 
         "Cindy", "Candy", "Cathy", "Cakra", "Carin", "Caroline",
         "Deny", "Dacy", "Danna", "Debbi", "Devon", "Diza","Dob")

"""
"""
users = ("Aaric", "Abbot", "Ace", "Ackerley", "Adam", "Adney", 
         "Bab", "Bamboo", "Ben", "Bunny", "Betty", "Baha", 
         "Cindy", "Candy", "Cathy", "Cakra", "Carin", "Caroline",
         "Deny", "Dacy", "Danna", "Debbi", "Devon", "Diza","Dob")

num = int(input("請輸入每排座位人數(2~7): ")) 
title1 = "   Name   " * num
title2 = "----------   " * num
print(title1)
print(title2)

for i in range(len(users)):
    if i > 0 and i % num == 0:
        print()
    print(f"{users[i]:10s}", end="")

"""
"""
讓用戶輸入一個整數，直到輸入的整數為3的倍數才停止輸入

"""

"""

方法一: 

val = 1
while val % 3 > 0:
    val = int(input("請輸入一個整數: "))

"""
"""

方法二:

while True:
    val = int(input("請輸入一個整數: "))
    if val % 3 == 0:
        break

"""
"""

讓用戶輸入一個整數，如果該整數不是質數則要求繼續書入，直到輸入的整數為質數才停止輸入

"""
"""
while True:  # 進入無限迴圈，直到輸入的整數為質數才會結束程式
    val = int(input("請輸入一個整數: "))  # 接收使用者輸入，並轉換為整數
    
    # 處理小於或等於 1 的數字
    # 質數的定義必須大於 1，且若為負數在進行開根號 (val ** 0.5) 時會產生數學錯誤
    if val <= 1:
        print("該整數不是質數")
        continue  # 跳過本次迴圈的剩餘部分，重新要求使用者輸入
        
    f = False  # 宣告一個旗標 (Flag)，預設為 False，代表尚未找到除了 1 和自己以外的因數
    
    # 從 2 開始，檢查到該數的平方根（包含整數部分）
    # 因為如果一個數有因數，其中一個因數必定小於或等於其平方根，這樣做能大幅減少檢查次數、提升效能
    for i in range(2, int(val ** 0.5) + 1):
        if val % i == 0:  # 如果可以被整除，代表它不是質數
            f = True  # 將旗標設為 True，標記為「不是質數」
            break  # 已找到因數，直接跳出 for 迴圈，不需要再往下檢查了
            
    if f:  # 如果旗標為 True，表示該數不是質數
        print("該整數不是質數")  # 印出提示，且會繼續 while 迴圈重新要求輸入
    else:  # 如果旗標維持 False，表示該數是質數
        print("該整數為質數")
        break  # 跳出 while 迴圈，結束整個程式

    """
    """
    猜數字遊戲1~100
    

    """