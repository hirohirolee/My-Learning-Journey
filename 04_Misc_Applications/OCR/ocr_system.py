import os
import re
import sqlite3
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import pandas as pd
from PIL import Image

# ==============================================================================
# 環境與套件準備說明：
# 1. 安裝 Python 套件：
#    pip install customtkinter pytesseract pdf2image pillow pandas openpyxl
#
# 2. 安裝外部依賴系統 (Windows)：
#    - Tesseract-OCR: 下載並安裝 Tesseract，若未加至系統環境變數，請解除下方註解並設定對應路徑。
#      (建議安裝 chi_tra 語言包以支援繁體中文辨識)
#    - Poppler: 處理 PDF 需要。下載 Poppler for Windows，並將其 bin 資料夾加入系統環境變數 PATH。
# ==============================================================================

try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pass # 若未安裝，執行時會有錯誤提示

# 【可選】若 Tesseract-OCR 未加入環境變數，請取消下方註解並設定正確路徑：
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 預設介面設定
ctk.set_appearance_mode("System")  # 支援 Dark/Light 模式
ctk.set_default_color_theme("blue")

class OCRApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("智能單據與文件 OCR 自動化處理系統")
        self.geometry("950x700")
        
        # 初始化資料庫
        self.init_db()
        
        # 建立 Tab 介面
        self.tabview = ctk.CTkTabview(self, width=900, height=650)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab1 = self.tabview.add("財務單據自動報帳")
        self.tab2 = self.tabview.add("歷史文件批次數位化")
        
        self.setup_tab1()
        self.setup_tab2()
        
        # 儲存單據提取結果的列表，用於匯出 Excel
        self.receipt_data = []

    def init_db(self):
        """初始化 SQLite 資料庫"""
        # check_same_thread=False 允許不同執行緒操作資料庫
        self.conn = sqlite3.connect("ocr_documents.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                content TEXT,
                processed_time TEXT
            )
        ''')
        self.conn.commit()

    # ==========================================
    # Tab 1: 財務單據自動報帳處理
    # ==========================================
    def setup_tab1(self):
        self.tab1.grid_columnconfigure(0, weight=1)
        
        # 上方按鈕操作區
        frame_top = ctk.CTkFrame(self.tab1)
        frame_top.pack(fill="x", padx=10, pady=10)
        
        btn_import = ctk.CTkButton(frame_top, text="匯入單據 (圖片/PDF)", command=self.import_receipts, width=150)
        btn_import.pack(side="left", padx=10)
        
        self.btn_export = ctk.CTkButton(frame_top, text="匯出至 Excel", command=self.export_to_excel, state="disabled", width=150)
        self.btn_export.pack(side="left", padx=10)
        
        self.lbl_status1 = ctk.CTkLabel(frame_top, text="狀態：等待輸入...", text_color="gray")
        self.lbl_status1.pack(side="right", padx=10)
        
        self.progress1 = ctk.CTkProgressBar(self.tab1)
        self.progress1.pack(fill="x", padx=10, pady=5)
        self.progress1.set(0)
        
        # 表格顯示區 (使用 tkinter 內建的 ttk.Treeview 搭配 customtkinter 風格)
        frame_table = ctk.CTkFrame(self.tab1)
        frame_table.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 設定 Treeview 樣式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        rowheight=30, 
                        fieldbackground="#2b2b2b")
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))
        
        columns = ("Filename", "Date", "TaxID", "Amount")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings")
        self.tree.heading("Filename", text="檔案名稱")
        self.tree.heading("Date", text="日期 (Date)")
        self.tree.heading("TaxID", text="統一編號 (Tax ID)")
        self.tree.heading("Amount", text="金額 (Amount)")
        
        self.tree.column("Filename", width=300)
        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("TaxID", width=120, anchor="center")
        self.tree.column("Amount", width=100, anchor="e")
        
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def import_receipts(self):
        filepaths = filedialog.askopenfilenames(
            title="選擇單據檔案",
            filetypes=[("支援的檔案", "*.png *.jpg *.jpeg *.pdf")]
        )
        if not filepaths:
            return
            
        self.lbl_status1.configure(text="處理中...")
        self.progress1.set(0)
        self.tree.delete(*self.tree.get_children())
        self.receipt_data.clear()
        self.btn_export.configure(state="disabled")
        
        # 使用 Thread 避免阻塞主視窗 UI
        threading.Thread(target=self.process_receipts_thread, args=(filepaths,), daemon=True).start()

    def process_receipts_thread(self, filepaths):
        total = len(filepaths)
        for i, filepath in enumerate(filepaths):
            try:
                # 呼叫共用的 OCR 方法
                text = self.extract_text(filepath)
                
                # 資訊抽取：使用正則表達式
                # 1. 匹配日期 (例如: 2023-10-01, 2023/10/01, 2023年10月1日)
                date_match = re.search(r'\d{4}\s*[-/年]\s*\d{1,2}\s*[-/月]\s*\d{1,2}\s*日?', text)
                # 2. 匹配台灣 8 碼統編
                tax_id_match = re.search(r'\b\d{8}\b', text)
                # 3. 匹配總計金額 (例如: 總計: $1,200)
                amount_match = re.search(r'(?:總計|合計|金額|NT\$|TWD|TOTAL)\s*[:：]?\s*\$?\s*([0-9,]+)', text, re.IGNORECASE)
                
                date = date_match.group(0).strip() if date_match else "未找到"
                tax_id = tax_id_match.group(0) if tax_id_match else "未找到"
                amount = amount_match.group(1) if amount_match else "未找到"
                
                filename = os.path.basename(filepath)
                
                # 暫存資料以供匯出
                self.receipt_data.append({
                    "檔案名稱": filename, 
                    "日期": date, 
                    "統一編號": tax_id, 
                    "金額": amount
                })
                
                # 更新 UI Treeview (必須透過 .after 確保在主執行緒操作 tkinter)
                self.after(0, self.tree.insert, "", "end", values=(filename, date, tax_id, amount))
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                self.after(0, self.tree.insert, "", "end", values=(os.path.basename(filepath), "錯誤", "錯誤", "錯誤"))
                
            # 更新進度條
            self.after(0, self.progress1.set, (i + 1) / total)
            
        self.after(0, self.finish_receipts_processing)

    def finish_receipts_processing(self):
        self.lbl_status1.configure(text="處理完成")
        if self.receipt_data:
            self.btn_export.configure(state="normal")
            
    def export_to_excel(self):
        if not self.receipt_data:
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 活頁簿", "*.xlsx")],
            title="儲存為 Excel"
        )
        if save_path:
            try:
                df = pd.DataFrame(self.receipt_data)
                df.to_excel(save_path, index=False)
                messagebox.showinfo("成功", f"已成功匯出至:\n{save_path}")
            except Exception as e:
                messagebox.showerror("匯出錯誤", f"匯出失敗:\n{e}")

    # ==========================================
    # Tab 2: 歷史文件批次數位化
    # ==========================================
    def setup_tab2(self):
        # 頂部操作區
        frame_top = ctk.CTkFrame(self.tab2)
        frame_top.pack(fill="x", padx=10, pady=10)
        
        btn_folder = ctk.CTkButton(frame_top, text="選擇資料夾 (批次 OCR)", command=self.import_folder, width=180)
        btn_folder.pack(side="left", padx=10)
        
        self.lbl_status2 = ctk.CTkLabel(frame_top, text="狀態：等待選擇資料夾...", text_color="gray")
        self.lbl_status2.pack(side="left", padx=10)
        
        self.progress2 = ctk.CTkProgressBar(frame_top)
        self.progress2.pack(side="right", padx=10, fill="x", expand=True)
        self.progress2.set(0)
        
        # 搜尋區
        frame_search = ctk.CTkFrame(self.tab2)
        frame_search.pack(fill="x", padx=10, pady=5)
        
        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="輸入關鍵字搜尋文件內文...", width=350)
        self.entry_search.pack(side="left", padx=10, pady=10)
        
        # 綁定 Enter 鍵觸發搜尋
        self.entry_search.bind("<Return>", lambda event: self.search_db())
        
        btn_search = ctk.CTkButton(frame_search, text="搜尋", command=self.search_db, width=100)
        btn_search.pack(side="left", padx=10)
        
        # 顯示結果的文字方塊區
        self.text_results = ctk.CTkTextbox(self.tab2, wrap="word", font=("Arial", 14))
        self.text_results.pack(fill="both", expand=True, padx=10, pady=10)

    def import_folder(self):
        folder_path = filedialog.askdirectory(title="選擇包含掃描檔的資料夾")
        if not folder_path:
            return
            
        self.lbl_status2.configure(text="掃描資料夾中...")
        self.progress2.set(0)
        
        # 啟動背景執行緒處理資料夾
        threading.Thread(target=self.process_folder_thread, args=(folder_path,), daemon=True).start()

    def process_folder_thread(self, folder_path):
        valid_exts = {'.pdf', '.png', '.jpg', '.jpeg'}
        files_to_process = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in valid_exts:
                    files_to_process.append(os.path.join(root, file))
                    
        total = len(files_to_process)
        if total == 0:
            self.after(0, lambda: messagebox.showinfo("提示", "該資料夾內無支援的圖片或 PDF 檔案"))
            self.after(0, lambda: self.lbl_status2.configure(text="狀態：等待選擇資料夾..."))
            return

        success_count = 0
        for i, filepath in enumerate(files_to_process):
            filename = os.path.basename(filepath)
            self.after(0, lambda f=filename: self.lbl_status2.configure(text=f"處理中: {f}"))
            
            try:
                text = self.extract_text(filepath)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 存入資料庫
                self.cursor.execute("INSERT INTO documents (filename, content, processed_time) VALUES (?, ?, ?)", 
                                    (filename, text, now))
                self.conn.commit()
                success_count += 1
            except Exception as e:
                print(f"Error batch processing {filepath}: {e}")
                
            self.after(0, self.progress2.set, (i + 1) / total)
            
        self.after(0, lambda: self.lbl_status2.configure(text="批次處理完成！"))
        self.after(0, lambda: messagebox.showinfo("完成", f"處理完畢！\n共成功 {success_count}/{total} 份文件。"))

    def search_db(self):
        keyword = self.entry_search.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "請輸入關鍵字進行搜尋")
            return
            
        self.text_results.delete("1.0", "end")
        try:
            self.cursor.execute("SELECT filename, content, processed_time FROM documents WHERE content LIKE ?", (f'%{keyword}%',))
            results = self.cursor.fetchall()
            
            if not results:
                self.text_results.insert("end", "未找到符合的結果。\n")
                return
                
            self.text_results.insert("end", f"🔍 找到 {len(results)} 筆結果：\n{'='*60}\n\n")
            for row in results:
                filename, content, ptime = row
                
                # 擷取關鍵字前後文字作為預覽 (Context)
                idx = content.find(keyword)
                start = max(0, idx - 40)
                end = min(len(content), idx + 40)
                preview = content[start:end].replace('\n', ' ')
                
                self.text_results.insert("end", f"📄 檔名：{filename}\n")
                self.text_results.insert("end", f"🕒 處理時間：{ptime}\n")
                self.text_results.insert("end", f"📝 預覽：...{preview}...\n")
                self.text_results.insert("end", "-"*60 + "\n\n")
                
        except Exception as e:
            messagebox.showerror("搜尋錯誤", f"搜尋時發生錯誤: {e}")

    # ==========================================
    # 核心 OCR 邏輯 (共用)
    # ==========================================
    def extract_text(self, filepath):
        """讀取圖片或 PDF 並呼叫 pytesseract 抽取文字"""
        ext = os.path.splitext(filepath)[1].lower()
        
        # 指定辨識語言：英文+繁體中文 (需要有 Tesseract chi_tra 語言包)
        # 若未安裝繁中，可改為 lang='eng' 以免報錯
        lang = 'chi_tra+eng' 
        text = ""
        
        if ext == '.pdf':
            # 將 PDF 轉為圖片 (需依賴 Poppler)
            pages = convert_from_path(filepath)
            for page in pages:
                text += pytesseract.image_to_string(page, lang=lang) + "\n"
        else:
            # 直接讀取圖片
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image, lang=lang)
            
        return text

if __name__ == "__main__":
    try:
        app = OCRApp()
        app.mainloop()
    except Exception as e:
        print(f"啟動應用程式時發生錯誤: {e}")
