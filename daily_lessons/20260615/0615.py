"""
1~100 猜數字遊戲
"""
"""
from ast import Pass
import random
min = 1
max = 100
answer = random.randint(min, max)
guess = 0
while answer != guess:
    guess = int(input(f"請猜{min}~{max}的數字: "))
    if guess < min or guess > max:
        print("範圍錯誤")
    elif guess < answer:
        min = guess + 1
    elif guess > answer:
        max = guess - 1
else:
    print("恭喜猜對了")
"""
"""
讓用戶輸入一個整數，將其數值反向輸出
例: 12345=>54321
"""
"""
while num > 0:
    1. 取最後一位數 ==> num %10
    2. 去掉一位數 ==> num // 1000
    3. 重組數值 ==> rev= rev*10 + last

另一個方法
num= input("")
new_num= ""
for c in num:
    new_num= c + new_num
"""
"""
num=int(input("請輸入一個整數: "))
new_num=0
while num >0:
    new_num=new_num*10+ num % 10
    num=num//10
else:
    print(new_num)
"""
"""
讓用戶輸入一個整數 N, 列出1+2+3+.....>N 的結果
"""
"""
num = int(input("請輸入一個整數: "))
fstr = ""
tot =0
n=0
while True:
    n=n+1
    tot=tot+n
    if n==1:
        fstr=str(n)
    else:
        fstr=fstr+f"+{n}"
 
    if tot >= num:
        break
 
print(f"{fstr}={num}")
"""

"""
輸入一個整數值n，找到第n個質數
"""
"""
num = int(input("請輸入一個整數: "))
n = 1
while num>0: 
    n = n+1
    for i in range (2, int(n**0.5)+1):
        if n%i==0:
            break
    else:
        num=num-1
else:
    print(n)

"""

"""
讓用戶重複輸入任意數量的整數，如用戶輸入空白則停止輸入
列出該數列，及最大值，最小值和平均值

"""
"""
方法一
min_num =  None
max_num =  None
sum_num = 0
num_list = []
while True:
    inp_str = input("請輸入一個整數，或空白結束：")
    if inp_str.strip() == "":
        break
    else:
        num_list.append(int(inp_str))

for n in num_list:
    if min_num is None or n< min_num:
        min_num=n
    if max_num is None or n> max_num:
        max_num=n
    sum_num=sum_num+n   

print("數列:",num_list)
print("最大值:",max_num,"最小值:",min_num,"平均值:",sum_num/len(num_list) )

"""

"""
min_num =  None
max_num =  None
sum_num = 0
num_list = []
while True:
    inp_str = input("請輸入一個整數，或enter結束：")
    if inp_str.strip() == "":
        break
    else:
        num_list.append(int(inp_str))
    
    if min_num == None or num_list[-1] < min_num:
        min_num = num_list[-1]

    if max_num == None or num_list[-1] > max_num:
        max_num = num_list[-1]
    sum_num += num_list[-1]

print("數列:",num_list)
print("最大值:",max_num,"最小值:",min_num,"平均值:",sum_num/len(num_list) )
"""
"""
import random
ls = random.sample(range(1,101), k=10)
print(ls)

ls_odds=[]
ls_evens=[]
for i in ls:
    if i % 2 == 0:
        ls_evens.append(i)
    else:
        ls_odds.append(i)


ls_odds.extend(ls_evens)
print (ls)
print("奇數:",ls_odds,"偶數:",ls_evens)
"""

"""
用亂數隨機產生10個介於1~100的整數值，挑出其中的質數

"""

import random
ls = random.sample(range(1,101), k=10)
print(ls)
ls_primes=[]

for n in ls:
    for i in range (2, int(n**0.5)+1):
        if n%i==0:
            break
    else:
        ls_primes.append(n)

print("質數:",ls_primes)