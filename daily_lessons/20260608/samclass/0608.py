"""
img_num = 1j
print (img_num*img_num)

"""

"""
輸入一個五位整數，將其轉為國字大寫輸出
國字大寫:零 壹 貳 參 肆 伍 陸 柒 捌 玖

"""
"""
input_num = input("請輸入一個五位整數:")

# 國字大寫對照字串
chinese_digits = "零壹貳參肆伍陸柒捌玖"

# 因為剛好是「五位數」，所以我們可以直接用固定位置 [0] ~ [4] 取得每個數字
# 並將它們轉成整數 (0~9)
n1 = int(input_num[0])
n2 = int(input_num[1])
n3 = int(input_num[2])
n4 = int(input_num[3])
n5 = int(input_num[4])

# 分別找出對應的國字大寫，然後加起來印出
print(chinese_digits[n1] + chinese_digits[n2] + chinese_digits[n3] + chinese_digits[n4] + chinese_digits[n5])

"""

"""
輸入一個電話號碼，將其數值轉為國字大寫輸出
例如: 0912345678 -> 零玖壹貳參肆伍陸柒捌

"""

"""
input_num = input("請輸入一個電話號碼: ")

# 利用 method chaining (方法鏈) 把所有 replace 接在一起，程式碼會更精簡
output = (input_num.replace("0", "〇")
                   .replace("1", "一")
                   .replace("2", "二")
                   .replace("3", "三")
                   .replace("4", "四")
                   .replace("5", "五")
                   .replace("6", "六")
                   .replace("7", "七")
                   .replace("8", "八")
                   .replace("9", "九"))

print(output)

"""

"""
輸入一個身分證字號，驗證其有效性
找出資料在文字中的位置
x ="ABCDEFGH"
print (x.index("B"))

"""

"""
input_id = input("請輸入身分證字號:")

# 我們稍微調整字母順序，讓每個字母的代號剛好等於它的「位置索引 + 10」！
# A在位置0 -> 10, B在位置1 -> 11 ... Z在位置23 -> 33
x = "ABCDEFGHJKLMNPQRSTUVXYWZ"

# 1. 取得第一個字母的代號 (例如 A 是 10，B 是 11)
val = x.index(input_id[0]) + 10

# 2. 拆成十位數與個位數
v1 = val // 10
v2 = val % 10

# 3. 取得後面的 9 個數字並轉為整數
n1 = int(input_id[1])
n2 = int(input_id[2])
n3 = int(input_id[3])
n4 = int(input_id[4])
n5 = int(input_id[5])
n6 = int(input_id[6])
n7 = int(input_id[7])
n8 = int(input_id[8])
n9 = int(input_id[9])

# 4. 計算加權總和
total = v1 * 1 + v2 * 9 + n1 * 8 + n2 * 7 + n3 * 6 + n4 * 5 + n5 * 4 + n6 * 3 + n7 * 2 + n8 * 1 + n9 * 1

# 5. 檢查是否整除
if total % 10 == 0:
    print("有效")
else:
    print("無效")

"""
"""
base = "ABCDEFGHJKLMNPQRSTUVXYWZIO"
id = input("請輸入身分證字號:").upper()
prefix = base.index(id[0]) + 10
id = str(prefix)+id[1:]
tot_num = (int(id[0])*1+int(id[1])*9+int(id[2])*8+int(id[3])*7+int(id[4])*6+int(id[5])*5+int(id[6])*4+int(id[7])*3+int(id[8])*2+int(id[9])*1+int(id[10])*1)    

if tot_num % 10 >0:
    print("無效id")
else:
    print("有效id")
"""

base = "ABCDEFGHJKLMNPQRSTUVXYWZIO"
user_id = input("請輸入身分證字號:").upper()

# 1. 將第一個字母換成對應的兩個數字
letter_code = base.index(user_id[0]) + 10  # 字母轉換 
# 2. 將轉換後的數字與後面的字串合併
full_id = str(letter_code) + user_id[1:]  # 變成 11 位字串 

# 3. 把每一位數乘上權重 (這就是最直白、不加修飾的寫法)
n0 = int(full_id[0]) * 1
n1 = int(full_id[1]) * 9
n2 = int(full_id[2]) * 8
n3 = int(full_id[3]) * 7
n4 = int(full_id[4]) * 6
n5 = int(full_id[5]) * 5
n6 = int(full_id[6]) * 4
n7 = int(full_id[7]) * 3
n8 = int(full_id[8]) * 2
n9 = int(full_id[9]) * 1
n10 = int(full_id[10]) * 1

# 4. 加總
total = n0 + n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8 + n9 + n10

# 5. 判斷餘數 
if total % 10 == 0:
    print("有效id")
else:
    print("無效id")

