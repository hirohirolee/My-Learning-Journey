import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- 開取檔案選擇器
def on_select_click():
    dbna = filedialog.askopenfile()
    # ---
    dbLabel["text"] = dbna.name if dbna else ""
    print(dbLabel["text"])
# --- 連接指定資料庫
def on_connect_click():
    if dbLabel["text"] == "":
        return 
    # ---
    try:
        dbconn = sqlite3.connect(dbLabel["text"])
        messagebox.showinfo("訊息", "資料庫連接成功!")
    except sqlite3.Error as ex:
        messagebox.showerror("錯誤", "資料庫連接失敗!")
    finally:
        if dbconn:
            dbconn.close()
# --- 執行輸入的SQL指令
def on_run_click():
    sqlStr = sqlEditor.get("1.0", "end-1c").strip()
    # ---
    if sqlStr == "":
        return
    # ---
    dbconn = sqlite3.connect(dbLabel["text"])
    cursor = dbconn.cursor()
    cursor.execute(sqlStr)
    columns = [col[0] for col in cursor.description]
    results = cursor.fetchall()
    # ---
    cursor.close()
    dbconn.close()
    # ---
    update_bottom_Panel(columns, results)

def clear_bottom_Panel():
    for widget in bottomPanel.winfo_children():
        widget.destroy()

def update_bottom_Panel(columns, results):
    clear_bottom_Panel() 
    # --- 沒有資料內容時
    if len(results) == 0:
        errLabel = tk.Label(bottomPanel, text="查無相關資料內容!", font=("Arial", 14))
        errLabel.pack(side="top", fill="both", expand=True)
        return
    # --- 有資料內容時
    table = ttk.Treeview(bottomPanel, columns=columns, show="headings")
    table.tag_configure("odd"   , background="#FFFFFF")
    table.tag_configure("even"  , background="#EFEFEF")
    # --- 編排欄位表頭
    for col in columns:
        table.heading(col, text=col)
    # --- 編排明細資料
    for ndx, row in enumerate(results):
        table.insert("", "end", values=row, tags="odd" if ndx % 2 == 0 else "even")
    # --- 處理垂直卷軸
    yBar = tk.Scrollbar(bottomPanel, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=yBar.set)
    yBar.pack(side="right", fill="y")
    # --- 處理水平卷軸
    xBar = tk.Scrollbar(bottomPanel, orient="horizontal", command=table.xview)
    table.configure(xscrollcommand=xBar.set)
    xBar.pack(side="bottom", fill="x")
    # ---
    table.pack(side="top", fill="both", expand=True)

# ---
rootWin = tk.Tk()
# --- 繪製主視窗
win_w = 1024
win_h = 768
scr_w   = rootWin.winfo_screenwidth()
scr_h   = rootWin.winfo_screenheight()
win_x   = (scr_w - win_w) // 2
win_y   = (scr_h - win_h) // 2
# ---
rootWin.title("SQLite Manager")
rootWin.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
# rootWin.resizable(width=False, height=False)
# --- 產生toolBar
toolPanel = tk.Frame(rootWin, relief="raised", bd=2)
toolPanel.pack(side="top", fill="x", padx=3, pady=3)
# --- 產生檔案選擇鈕
selBtn = tk.Button(toolPanel, text="選檔案", font=("Arial", 14), command=on_select_click)
selBtn.pack(side="left", fill="y", ipadx=5, pady=3)
# --- 產生檔案標籤
dbLabel = tk.Label(toolPanel, text="D:/Sam/northwind.db", font=("Arial", 14), relief="solid", 
                   bd=1, anchor="w", bg="#FFFFFF")
dbLabel.pack(side="left", fill="both", expand=True, padx=5, pady=3)
# --- 產生連線按鈕
conBtn = tk.Button(toolPanel, text="連接", font=("Arial", 14), command=on_connect_click)
conBtn.pack(side="left", fill="y", ipadx=5, pady=3)
# --- 產生SQL 編輯Panel
sqlPanel = tk.LabelFrame(rootWin, text="SQL 指令", font=("Arial", 14))
sqlPanel.pack(side="top", fill="x", padx=3, pady=3, ipady=3)
# --- 產生SQL指令編輯Editor
sqlEditor = tk.Text(sqlPanel, font=("Arial", 14), height=10)
sqlEditor.pack(side="top", fill="both", padx=3)
sqlEditor.insert("1.0", "SELECT * FROM Customers WHERE CustomerID LIKE '%A'")
# --- 產生執行按鈕
runBtn = tk.Button(sqlPanel, text="執行", font=("Arial", 14), command=on_run_click)
runBtn.pack(side="top", pady=3, ipadx=10)
# --- 產生結果Panel
bottomPanel = tk.LabelFrame(rootWin, text="執行結果", font=("Arial", 14))
bottomPanel.pack(side="top", fill="both", expand=True, padx=3, pady=3, ipady=3)
# --- 顯示視窗
rootWin.mainloop()