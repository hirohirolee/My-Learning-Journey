"""
讓用戶輸入一個整數秒，所以計算是?天?時?分?秒
輸出格式: xxxxx秒= x天x時x分x秒

#---取得資料
tot_secs = input ("請輸入秒數:")
#---資料轉型
tot_secs = int(tot_secs)
#---取不足分的秒數
rem_secs = tot_secs % 60
#---計算總分鐘數
tot_mins = int((tot_secs - rem_secs) / 60)
#---取不足時的分鐘數
rem_mins = tot_mins % 60
#---計算總小時數
tot_hours = int((tot_mins - rem_mins) / 60)
#---取不足天的小時數
rem_hours = tot_hours % 24
#---計算總天數
tot_days = int((tot_hours - rem_hours) / 24)
#結果輸出
print (tot_secs, "秒 =", tot_days, "天", rem_hours, "時", rem_mins, "分", rem_secs, "秒")

"""
"""
台幣幣值有 2000, 1000, 500, 200, 100, 50, 20, 10, 5, 1
讓用戶輸入一個金額，計算每一種幣值所需數量
輸出必須對齊如下:
2000元: 0張 =xxxxx元
1000元: 0張 =xxxxx元
500元: 0張 =xxxxx元
200元: 0張 =xxxxx元
100元: 0張 =xxxxx元
50元: 0枚 =xxxxx元
10元: 0枚 =xxxxx元
5元: 0枚 =xxxxx元
1元: 0枚 =xxxxx元 


"""
#---取得資料
money = int(input("請輸入金額:"))
#---計算2000元
tw2000 = money //2000
#---扣掉2000元後剩餘金額
rem2000 = money %2000
#---計算1000元
tw1000 = rem2000 //1000
#---扣掉1000元後剩餘金額
rem1000 = rem2000 %1000
#---計算500元
tw500 = rem1000//500
#---扣掉500元後剩餘金額
rem500 = rem1000 %500
#---計算200元
tw200 = rem500//200
#---扣掉200元後剩餘金額
rem200 = rem500 %200
#---計算100元
tw100 = rem200//100
#---扣掉100元後剩餘金額
rem100 = rem200 %100
#---計算50元
tw50 = rem100//50
#---扣掉50元後剩餘金額
rem50 = rem100 %50
#---計算10元
tw10 = rem50//10
#---扣掉10元後剩餘金額
rem10 = rem50 %10
#---計算5元
tw5 = rem10//5
#---扣掉5元後剩餘金額
rem5 = rem10 %5
#---計算1元
tw1 = rem5//1
#---扣掉1元後剩餘金額
rem1 = rem5 %1
#---結果輸出

print(f"{2000:4d} 元,{tw2000:4d} 張, {2000 * tw2000:7d} 元")
print(f"{1000:4d} 元,{tw1000:4d} 張, {1000 * tw1000:7d} 元")
print(f"{500:4d} 元,{tw500:4d} 張, {500 * tw500:7d} 元")
print(f"{200:4d} 元,{tw200:4d} 張, {200 * tw200:7d} 元")
print(f"{100:4d} 元,{tw100:4d} 張, {100 * tw100:7d} 元")
print(f"{50:4d} 元,{tw50:4d} 枚, {50 * tw50:7d} 元")
print(f"{10:4d} 元,{tw10:4d} 枚, {10 * tw10:7d} 元")
print(f"{5:4d} 元,{tw5:4d} 枚, {5 * tw5:7d} 元")
print(f"{1:4d} 元,{tw1:4d} 枚, {1 * tw1:7d} 元")

tot_qty = tw2000 + tw1000 + tw500 + tw200 + tw100 + tw50 + tw10 + tw5 + tw1
tot_amt = 2000 * tw2000 + 1000 * tw1000 + 500 * tw500 + 200 * tw200 + 100 * tw100 + 50 * tw50 + 10 * tw10 + 5 * tw5 + 1 * tw1

print("------- --------  ----------")
print(f"合計     {tot_qty:4d} 張 = {money:7d} 元")

"""
回家功課  

小計    總共幾個    總金額多少元

"""