import streamlit as st
st.title('dl_predictor.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import torch
import torch.nn as nn
from typing import Tuple

class LSTM_Predictor(nn.Module):
    """
    日線級別 LSTM 預測模型
    用於捕捉中長期趨勢與動能
    """
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(LSTM_Predictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM 層
        self.lstm = nn.LSTM(
            input_size=input_size, 
            hidden_size=hidden_size, 
            num_layers=num_layers, 
            batch_first=True, 
            dropout=dropout if num_layers > 1 else 0
        )
        
        # 全連接層 (分類輸出：0看跌, 1看漲)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, sequence_length, features)
        # 初始化隱藏狀態與細胞狀態
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # 前向傳播 LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # 取最後一個時間點的輸出
        out = out[:, -1, :]
        out = self.fc(out)
        return out


class CNN_LSTM_HighFreq_Predictor(nn.Module):
    """
    1分鐘當沖高頻模型 (1D-CNN + LSTM)
    CNN 負責抓取微觀 K 線型態特徵
    LSTM 負責延續時間序列的動能與主力吃貨方向
    """
    def __init__(self, input_size: int, cnn_out_channels: int = 32, hidden_size: int = 64):
        super(CNN_LSTM_HighFreq_Predictor, self).__init__()
        
        # 1D-CNN 特徵萃取層 (用來抓取 K 線組合型態)
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=input_size, out_channels=cnn_out_channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        
        # LSTM 序列建模層
        self.lstm = nn.LSTM(
            input_size=cnn_out_channels, 
            hidden_size=hidden_size, 
            num_layers=1, 
            batch_first=True
        )
        
        # 預測輸出層
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, sequence_length, features)
        # CNN 的輸入需要是 (batch_size, channels, sequence_length)
        x = x.transpose(1, 2)
        
        # 通過 CNN 抓型態特徵
        cnn_out = self.cnn(x)
        
        # 轉回 (batch_size, sequence_length, channels) 給 LSTM
        cnn_out = cnn_out.transpose(1, 2)
        
        # 通過 LSTM 抓動能
        lstm_out, _ = self.lstm(cnn_out)
        
        # 取最後一個時間步輸出進行分類
        out = self.fc(lstm_out[:, -1, :])
        return out
