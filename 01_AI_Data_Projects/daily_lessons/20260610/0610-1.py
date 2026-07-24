"""
count = 3  # 初始狀態

while count > 0:
    print(f"倒數 {count}...")
    count = count - 1  # 關鍵：每次減 1，讓條件慢慢接近結束

print("發射！🚀")

"""
"""
# 外層迴圈控制被乘數 (i)
for i in range(2, 4):  # 我們先印 2 和 3 就好
    # 內層迴圈控制乘數 (j)
    for j in range(1, 10):
        print(f"{i} x {j} = {i*j}")
    print("----------------")  # 當某一排印完後，印一條分隔線
"""

correct_password = "1234"  # 正確密碼
input_count = 0            # 紀錄輸入了幾次
max_tries = 3              # 最多只能試 3 次

while input_count < max_tries:
    guess = input("請輸入 4 位數密碼: ")
    input_count = input_count + 1  # 輸入次數加 1
    
    if guess == correct_password:
        print("密碼正確！歡迎登入。")
        break  # 密碼對了，直接打破迴圈，不用再猜了！
    else:
        remaining = max_tries - input_count
        print(f"密碼錯誤！你還剩下 {remaining} 次機會。")

# 離開迴圈後，檢查是不是因為失敗次數到了才出來的
if input_count == max_tries and guess != correct_password:
    print("帳號已被鎖定，請臨櫃辦理！")