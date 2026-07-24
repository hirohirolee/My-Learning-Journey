# na = input("請輸入姓名 : ")  # 這是被註解掉的程式碼，原本用來從主控台輸入姓名
# print("Hello, ", na)  # 這是被註解掉的程式碼，原本用來在主控台輸出 Hello 訊息

from tkinter import RAISED  # 從 tkinter 模組中匯入 RAISED 常數，用於設定元件的浮凸外框樣式
import tkinter as tk   # 匯入 tkinter 模組，並命名為別名 tk，以便後續簡寫呼叫
topwin = tk.Tk() # 建立 tkinter 的主視窗物件，視窗程式的核心元件
#設定視窗的標題
topwin.title("python AI IN 2026")  # 設定主視窗上方標題列所顯示的文字
#設定視窗大小和位置
topwin.geometry("600x300+50+50")  # 設定主視窗寬度為 600、高度為 300 像素，並將視窗左上角定位在螢幕 (x=50, y=50) 的位置
#-------按鈕點擊執行的功能
def onClick():  # 定義按鈕點擊時觸發的事件處理函式 onClick
    #取出用戶輸入的資料，並去掉前後的空白
    na = editor01.get().strip()  # 從輸入框 editor01 中取得使用者輸入的字串，並呼叫 strip() 去除頭尾的空白字元
    #--
    if na:  # 檢查變數 na 是否非空值（即使用者確實有輸入名字）
        label02["text"] = "Hello, " + na + " nice to meet you!!"  # 如果有輸入名字，動態更改 label02 標籤的顯示文字為問候語
    else:  # 如果變數 na 是空值（使用者沒輸入任何內容）
        label02["text"] = "你沒有輸入名字耶"  # 動態將 label02 標籤的顯示文字更改為提示訊息
#-------
#建立一個上方的容器
panel01 = tk.Frame(topwin, height=10, relief=tk.RAISED, bd=2)  # 建立一個 Frame 容器元件，設定高度、外框樣式為 RAISED，以及邊框寬度為 2 像素
panel01.pack(side="top",fill="x")  # 將 panel01 容器放置在主視窗頂部，並在水平方向 (x 軸) 填滿視窗
#建立欄位標題
label01=tk.Label(panel01,text="姓名 : ",font=("Arial",20), anchor="e",width=10)  # 建立標籤元件 label01 顯示「姓名 : 」，設定字型 Arial 大小 20、文字靠右對齊 (east) 且元件寬度為 10
label01.pack(side="left")  # 將 label01 標籤放置在容器 panel01 的左側
#建立欄位編輯器
editor01=tk.Entry(panel01, font=("Arial",20))  # 建立單行文字輸入框元件 editor01，並設定字型與大小為 Arial 20
editor01.pack(side="left", fill="x", padx=3, expand=True)  # 將輸入框放置在 panel01 的左側，在水平方向填滿，左右保留 3 像素間距，並允許隨著視窗縮放自動擴展
#建立顯示結果的標籤
label02=tk.Label(topwin, text="請先輸入您的大名",font=("Arial",20), anchor="center")  # 建立標籤元件 label02 來顯示結果，預設文字為「請先輸入您的大名」，字型 Arial 20，文字置中對齊
label02.pack(side="top",fill="both",padx=3,pady=3,expand=True)  # 將 label02 標籤放置在主視窗中，並在水平與垂直方向填滿所有剩餘空間，內縮邊距 3 像素，且設定隨著視窗縮放自動擴展
#建立功能按鈕
button01=tk.Button(topwin,text="Click", font=("Arial",20), command=onClick)  # 建立按鈕元件 button01，顯示文字為 "Click"，字型 Arial 20，並指定當按鈕被點擊時執行 onClick 函式
button01.pack(side="bottom", ipadx=10, ipady=5)  # 將按鈕元件放置在視窗的最下方，並設定按鈕內部水平內邊距為 10 像素、垂直內邊距為 5 像素

topwin.mainloop() # 啟動 Tkinter 的事件監聽循環，讓視窗保持顯示狀態並等待使用者點擊或輸入等事件動作