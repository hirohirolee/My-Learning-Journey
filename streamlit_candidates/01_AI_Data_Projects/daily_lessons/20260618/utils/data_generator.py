import streamlit as st
st.title('data_generator.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import numpy as np
from sklearn.datasets import make_circles, make_moons, make_blobs


def generate_data(
    n_samples=200, noise=0.05, seed=42, dataset_type="Concentric Circles"
):
    if dataset_type in ["Concentric Circles", "同心圓"]:
        X, y = make_circles(
            n_samples=n_samples, noise=noise, factor=0.7, random_state=seed
        )
    elif dataset_type in ["Moons", "月牙形"]:
        X, y = make_moons(n_samples=n_samples, noise=noise, random_state=seed)
    elif dataset_type in ["Blobs", "群聚"]:
        X, y = make_blobs(
            n_samples=n_samples, centers=2, cluster_std=noise, random_state=seed
        )
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    return X, y


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 generate_data"):
        try:
            res = generate_data() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
