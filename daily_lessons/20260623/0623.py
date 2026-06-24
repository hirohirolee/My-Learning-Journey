"""
建立一個函式，傳入圓的半徑，回傳圓面積
圓周率用3.14
"""
def carea1(r: float)->float:
    area = r * r * 3.14
    return area
# c1 = carea1()
# print(c1)

"""
建立一個函式，傳入圓的半徑&圓周率，回傳圓面積
圓周率內定值用3.14
"""
def carea2(r: float, pi:float=3.14) -> float:
    return r * r * pi
# print(carea2(10, 3.14159))
# print(carea2(10))


"""
建立一個函式，傳入圓的半徑、圓周率及圓心角，回傳扇形/圓面積
圓周率內定值3.14，圓心角內定值360
"""
def carea3(r:float, pi:float=3.14, deg:int=360) -> float:
    area = carea2(r, pi)
    area = area * deg / 360
    return area
# print(carea3(r=10, deg=90))


"""
建立一個函式，傳入圓的半徑、圓周率及圓心角，回傳扇形/圓面積 & 周長
圓周率內定值3.14，圓心角內定值360
"""
def carea4(r:float, pi:float=3.14, deg:int=360)->tuple :
    area = carea3(r, pi, deg)
    peri = 2 * r * pi * deg / 360
    if deg < 360:
        peri = peri + 2 * r
    # ---
    return area, peri
# print(carea4(r=10, deg=90))

"""
如何將文字的日期格式，轉為時間
"""
from datetime import datetime

def S2D(dt:str, fm:str="%Y/%m/%d"):
    return datetime.strptime(dt, fm)

def D2S(dt:datetime, fm:str="%Y/%m/%d"):
    return dt.strftime(fm)

"""
讓用戶輸入個時間00:00:00 ~ 23:59:59，
計算二個時間之間的間隔秒數
"""
def get_time_different_seconds(ftm:str, etm:str, fm="%Y/%m/%d %H:%M:%S") -> int:
    # 將文字轉為時間格式
    ftm = S2D(ftm, fm) 
    etm = S2D(etm, fm)
    # 計算秒差
    return int((etm - ftm).seconds)

# print(get_time_different_seconds("00:00:00", "00:00:10", fm="%H:%M:%S"))

"""
建立一個函數，沒有傳入值，會傳回4份，樸克牌的發牌結果
♠、♥、♦、♣
"""
import random
def get_poker()-> list:
    # 產生所有的牌
    all_ls = [f"{c}-{p}" for c in "♠♥♦♣" for p in ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")]
    # 搗亂所有的順序
    all_ls = random.sample(all_ls, k=len(all_ls))
    # 分成四份
    return [all_ls[i:i+13] for i in range(0, len(all_ls), 13)]

# print(get_poker())

x = chr(ord("A") ^ ord("0"))
print("A", "/", ord("A"), "/", bin(ord("A"))[2:].zfill(8))
print("0", "/", ord("0"), "/", bin(ord("0"))[2:].zfill(8))
print(x  , "/", ord(x)  , "/", bin(ord(x))[2:].zfill(8))

