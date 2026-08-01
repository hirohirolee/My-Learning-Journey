"""
DQNAgent 演算法核心 (Deep Q-Network Agent)
===========================================
包含：
1. 雙網路 (Policy Network & Target Network) 管理與定期同步
2. Epsilon-Greedy 探索與利用策略
3. 根據 Bellman 方程進行小批次 (Batch) 梯度下降更新與 Loss 計算 (詳細數學/物理意義註解)
"""

import random
import sys
from typing import Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from model import DeepQNetwork
from replay_buffer import ReplayBuffer

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class DQNAgent:
    """
    DQN 代理人類別
    """

    def __init__(
        self,
        state_dim: Tuple[int, int, int] = (4, 84, 84),
        action_dim: int = 2,
        lr: float = 1e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay_steps: int = 100000,
        target_update_freq: int = 1000,
        device: Optional[torch.device] = None
    ) -> None:
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay_steps = epsilon_decay_steps
        self.target_update_freq = target_update_freq
        self.total_steps = 0

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device

        print(f"[DQNAgent] 正在使用運算裝置: {self.device}")

        # 1. 建立 Policy Network
        self.policy_net = DeepQNetwork(in_channels=state_dim[0], action_dim=action_dim).to(self.device)

        # 2. 建立 Target Network
        self.target_net = DeepQNetwork(in_channels=state_dim[0], action_dim=action_dim).to(self.device)

        # 同步權重
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.lr)
        self.loss_fn = nn.SmoothL1Loss()  # Huber Loss

    def select_action(self, state: np.ndarray, evaluate: bool = False) -> int:
        if not evaluate and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
            action = q_values.argmax(dim=1).item()
        return action

    def update_epsilon(self) -> None:
        if self.total_steps < self.epsilon_decay_steps:
            decay_ratio = self.total_steps / self.epsilon_decay_steps
            self.epsilon = self.epsilon_start - decay_ratio * (self.epsilon_start - self.epsilon_end)
        else:
            self.epsilon = self.epsilon_end

    def train_step(self, replay_buffer: ReplayBuffer, batch_size: int = 32) -> Optional[float]:
        if len(replay_buffer) < batch_size:
            return None

        self.total_steps += 1
        self.update_epsilon()

        states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size, self.device)

        # =========================================================================
        # 核心 RL 計算區塊：Bellman 方程 (Bellman Optimality Equation)
        # =========================================================================

        # 【步驟 1】：計算目前策略網路對選定動作的預測 Q 值 Q(s_i, a_i; θ_policy)
        # 物理意義：模型目前估算在狀態 s 下執行特定動作 a，未來能夠獲得的累積折扣回報。
        # 數學公式：Q_current = Policy_Net(states).gather(action_index)
        current_q_values = self.policy_net(states).gather(1, actions)

        # 【步驟 2】：計算 Bellman 目標值 (TD Target)
        # 物理意義：根據獎勵與下一個狀態的估值計算「真正期望的地面真值 (Ground Truth Target)」。
        # 數學公式：y_i = r_i + (1 - done_i) * γ * max_{a'} Q_target(s'_i, a'; θ_target)
        with torch.no_grad():
            next_q_values = self.target_net(next_states)
            max_next_q_values, _ = next_q_values.max(dim=1, keepdim=True)
            target_q_values = rewards + (1.0 - dones) * self.gamma * max_next_q_values

        # 【步驟 3】：計算 Temporal Difference (TD) Error 及其 Loss
        # 物理意義：計算當前 Q 預測值與 Bellman 目標值之間的偏離程度 (TD 誤差)。
        # 數學公式：Loss = SmoothL1Loss(Q_current, TD_Target)
        loss = self.loss_fn(current_q_values, target_q_values)

        # 【步驟 4】：反向傳播與梯度更新 (Backpropagation & Gradient Descent)
        # 物理意義：使用梯度下降法調整 Policy Network 的參數 θ_policy，使 Q 預估值逐漸收斂至 Bellman 最優解。
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        # =========================================================================

        # 硬更新 Target Network
        if self.total_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    def save_model(self, filepath: str) -> None:
        torch.save({
            "policy_net_state_dict": self.policy_net.state_dict(),
            "target_net_state_dict": self.target_net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "total_steps": self.total_steps,
            "epsilon": self.epsilon
        }, filepath)
        print(f"[Checkpoint] 已儲存模型至: {filepath}")

    def load_model(self, filepath: str) -> None:
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint["policy_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.total_steps = checkpoint.get("total_steps", 0)
        self.epsilon = checkpoint.get("epsilon", self.epsilon_end)
        print(f"[Checkpoint] 已載入模型: {filepath}")
