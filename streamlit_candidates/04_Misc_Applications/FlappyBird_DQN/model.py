"""
DQN 神經網路模型 (Nature CNN Architecture)
=========================================
參考 DeepMind 2015 Nature 論文之 3 層 Conv 加上全連接層架構。
輸入: 連續 4 幀堆疊畫面 (Batch_Size, 4, 84, 84)
輸出: 各個動作的預估 Q 值 (Batch_Size, action_dim)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DeepQNetwork(nn.Module):
    """
    Nature CNN Deep Q-Network 模型
    """

    def __init__(self, in_channels: int = 4, action_dim: int = 2) -> None:
        """
        初始化神經網路層

        :param in_channels: 輸入影像特徵通道數 (預設為 4 幀堆疊)
        :param action_dim: 動作數量 (Flappy Bird 為 2: 不跳/跳)
        """
        super(DeepQNetwork, self).__init__()

        # 卷積神經網路特徵提取器 (Feature Extractor)
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        # 計算展平後的向量維度: (64, 7, 7) -> 3136
        self.fc_input_dim = 64 * 7 * 7

        # 全連接層 (Fully Connected Layers) 估算 Q 值
        self.fc1 = nn.Linear(self.fc_input_dim, 512)
        self.fc2 = nn.Linear(512, action_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向傳播 (Forward Pass)

        :param x: 狀態 Tensor，形狀 (Batch, 4, 84, 84)
        :return: 動作 Q 值 Tensor，形狀 (Batch, action_dim)
        """
        # 第一層卷積: (Batch, 4, 84, 84) -> (Batch, 32, 20, 20)
        x = F.relu(self.conv1(x))
        
        # 第二層卷積: (Batch, 32, 20, 20) -> (Batch, 64, 9, 9)
        x = F.relu(self.conv2(x))
        
        # 第三層卷積: (Batch, 64, 9, 9) -> (Batch, 64, 7, 7)
        x = F.relu(self.conv3(x))

        # 展平矩陣 (Flatten): (Batch, 64 * 7 * 7) -> (Batch, 3136)
        x = x.view(x.size(0), -1)

        # 全連接隱藏層: (Batch, 3136) -> (Batch, 512)
        x = F.relu(self.fc1(x))

        # 輸出層: (Batch, 512) -> (Batch, action_dim)
        q_values = self.fc2(x)
        return q_values
