import random
"""
def XOR_Coder(data:str | bytes, key:str):
    encode_mode = isinstance(data, str)
    # ---
    if encode_mode:
        data = data.encode("utf-8")
    # ---
    key = key.encode("utf-8")
    # ---
    newdata = bytearray()
    for ndx, value in enumerate(data):
        ndx = ndx % len(key)
        newdata.append(value ^ key[ndx])
    # ---
    if encode_mode:
        return bytes(newdata)
    else:
        return newdata.decode("utf-8")

orgStr = "NCHU中興大學"
key    = "".join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))
encStr = XOR_Coder(orgStr, key)
decStr = XOR_Coder(encStr, key)
# ----
print("加密金鑰:", key)
print("原始資料:", orgStr)
print("加密資料:", encStr)
print("解密資料:", decStr)
"""


"""
利用遞迴函式執行 1 + 3 + 5 + 7 ...總和值
"""
def rec_odd(num: int) -> int:
    if num == 1:
        return 1
    else:
        if num % 2 == 0:
            num = num -1
        # ---
        return num + rec_odd(num - 2)
# print(rec_odd(6))


"""
給予一個資料夾路徑，印出其下所有子階資料夾
"""
from pathlib import Path

def show_folders(pa):
    # 取出目前資料夾所有內容
    parent = Path(pa)
    print("目前位置:", parent)
    # 依序將資料夾內資料讀出
    for item in parent.iterdir():
        # 檢查是否為資料夾
        if item.is_dir():
            # 讀取下一層資料內容
            show_folders(item)

# show_folders("C:\\Users\\admin\\Downloads")

"""
讀取資料利用lambda 依指定欄位編號排序
"""
import sqlite3
connect = sqlite3.connect("data.db")
cursor  = connect.cursor()
cursor.execute("SELECT * FROM MOCK_DATA")
results = cursor.fetchall()
cursor.close()
connect.close()
# ---
sorter = lambda col : results.sort(key = lambda x: x[col])
# ---
sorter(4)
for row in results:
    print(row)