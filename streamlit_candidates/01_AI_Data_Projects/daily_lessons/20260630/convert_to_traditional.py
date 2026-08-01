import streamlit as st
st.title('convert_to_traditional.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
import csv
import re
from opencc import OpenCC

def convert_dataset_to_traditional():
    cc = OpenCC('s2t') # Simplified to Traditional Chinese converter
    posters_dir = "posters"
    
    # 1. Rename poster files to Traditional Chinese names
    if os.path.exists(posters_dir):
        st.write("Converting poster filenames to Traditional Chinese...")
        files = os.listdir(posters_dir)
        for filename in files:
            if filename.endswith(".jpg") or filename.endswith(".png"):
                # E.g. "1_霸王别姬.jpg" -> "1_霸王別姬.jpg"
                translated = cc.convert(filename)
                if translated != filename:
                    old_path = os.path.join(posters_dir, filename)
                    new_path = os.path.join(posters_dir, translated)
                    try:
                        os.rename(old_path, new_path)
                        st.write(f"  Renamed: {filename} -> {translated}")
                    except Exception as e:
                        st.write(f"  Failed to rename {filename}: {e}")

    # 2. Convert CSV data to Traditional Chinese
    csv_path = "movies.csv"
    if os.path.exists(csv_path):
        st.write("\nConverting movies.csv to Traditional Chinese...")
        rows = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Translate headers
            translated_headers = [cc.convert(h) for h in headers]
            
            for row in reader:
                # Row fields: Index, Poster (Excel Formula), Chinese Title, English Title, Score, Categories, Region, Duration, Release Date, Poster URL, Local Poster Path
                translated_row = []
                for val in row:
                    # Translate simplified Chinese fields
                    translated_val = cc.convert(val)
                    translated_row.append(translated_val)
                rows.append(translated_row)
                
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(translated_headers)
            writer.writerows(rows)
        st.write("Success! movies.csv converted.")

if __name__ == "__main__":
    convert_dataset_to_traditional()
