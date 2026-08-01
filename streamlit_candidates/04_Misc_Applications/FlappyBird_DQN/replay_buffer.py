"""
經驗回放池 (Experience Replay Buffer)
=====================================
打破 RL 訓練中連續樣本的時間相關性 (Temporal Correlation)，
提升神經網路訓練的獨立同分布 (i.i.d.) 假設條件與穩定度。
"""

from collections import deque
import random
from typing import Tuple
import numpy as np
import torch


class ReplayBuffer:
    """
    固定容量之環形經驗回放池
    """

    def __init__(self, capacity: int = 10000) -> None:
        """
        初始化經驗池

        :param capacity: 最大容量限制
        """
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ) -> None:
        """
        存入單一 transition (s, a, r, s', done)

        :param state: 目前狀態 (4, 84, 84)
        :param action: 執行的動作 (int)
        :param reward: 獲得的回報 (float)
        :param next_state: 下一狀態 (4, 84, 84)
        :param done: 遊戲是否結束 (bool)
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(
        self,
        batch_size: int,
        device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        從經驗池中隨機抽樣小批次 (Mini-batch) 資料並轉換為 PyTorch Tensor

        :param batch_size: 批次大小
        :param device: 運算裝置 (CPU 或 CUDA)
        :return: (states, actions, rewards, next_states, dones) Tensors
        """
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # 轉為 PyTorch Tensors 並傳送至指定運算裝置 (CPU/GPU)
        states_tensor = torch.FloatTensor(np.array(states)).to(device)
        actions_tensor = torch.LongTensor(actions).unsqueeze(1).to(device)
        rewards_tensor = torch.FloatTensor(rewards).unsqueeze(1).to(device)
        next_states_tensor = torch.FloatTensor(np.array(next_states)).to(device)
        dones_tensor = torch.FloatTensor(np.array(dones, dtype=np.float32)).unsqueeze(1).to(device)

        return states_tensor, actions_tensor, rewards_tensor, next_states_tensor, dones_tensor

    def __len__(self) -> int:
        """回傳目前經驗池中的資料總筆數"""
        return len(self.buffer)
