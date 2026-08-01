"""
訓練與評估主迴圈 (Training & Evaluation Main Loop)
===================================================
1. 環境 initialization 與預熱 (Warmup) 經驗池
2. Epsilon-Greedy 探索訓練 (快速 Epsilon 衰減)
3. 訓練日誌記錄與週期性模型 Save Checkpoint
4. 即時可視化展示 AI Agent 自動遊玩畫面 (Render Mode)
"""

import argparse
import os
import sys
import time
from typing import Optional
import numpy as np

from env_wrapper import FlappyBirdEnvWrapper
from replay_buffer import ReplayBuffer
from agent import DQNAgent

# 設定 stdout 編碼保護 (防止 Windows CP950 控制台拋出 UnicodeEncodeError)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def train(
    env_name: str = "FlappyBird-rgb-v0",
    max_episodes: int = 500,
    max_steps_per_episode: int = 2000,
    batch_size: int = 32,
    buffer_capacity: int = 20000,
    warmup_steps: int = 1000,
    lr: float = 1e-4,
    gamma: float = 0.99,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.01,
    epsilon_decay_steps: int = 15000,
    target_update_freq: int = 500,
    save_dir: str = "checkpoints"
) -> None:
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "flappy_bird_dqn_best.pth")

    print(f"[Init] 正在初始化遊戲環境: {env_name} ...")
    env = FlappyBirdEnvWrapper(env_name=env_name, frame_stack_num=4, screen_size=(84, 84))
    replay_buffer = ReplayBuffer(capacity=buffer_capacity)

    agent = DQNAgent(
        state_dim=(4, 84, 84),
        action_dim=2,
        lr=lr,
        gamma=gamma,
        epsilon_start=epsilon_start,
        epsilon_end=epsilon_end,
        epsilon_decay_steps=epsilon_decay_steps,
        target_update_freq=target_update_freq
    )

    print(f"[Warmup] 正在進行經驗池預熱，先隨機收集 {warmup_steps} 筆經驗...")
    state = env.reset()
    for step in range(warmup_steps):
        action = np.random.randint(0, 2)
        next_state, reward, done, _ = env.step(action)
        replay_buffer.push(state, action, reward, next_state, done)
        if done:
            state = env.reset()
        else:
            state = next_state
    print("[Warmup] 經驗池預熱完成，開始正式訓練！\n")

    best_reward = -float("inf")
    recent_rewards = []

    for episode in range(1, max_episodes + 1):
        state = env.reset()
        episode_reward = 0.0
        episode_losses = []
        start_time = time.time()

        for step in range(max_steps_per_episode):
            action = agent.select_action(state, evaluate=False)
            next_state, reward, done, _ = env.step(action)
            replay_buffer.push(state, action, reward, next_state, done)

            loss = agent.train_step(replay_buffer, batch_size=batch_size)
            if loss is not None:
                episode_losses.append(loss)

            state = next_state
            episode_reward += reward

            if done:
                break

        recent_rewards.append(episode_reward)
        if len(recent_rewards) > 100:
            recent_rewards.pop(0)

        avg_reward_100 = np.mean(recent_rewards)
        avg_loss = np.mean(episode_losses) if episode_losses else 0.0
        elapsed = time.time() - start_time

        if episode % 10 == 0 or episode == 1:
            print(
                f"Episode [{episode}/{max_episodes}] | "
                f"Reward: {episode_reward:.1f} | "
                f"100-Avg Reward: {avg_reward_100:.2f} | "
                f"Loss: {avg_loss:.4f} | "
                f"Epsilon: {agent.epsilon:.3f} | "
                f"Total Steps: {agent.total_steps} | "
                f"Time: {elapsed:.2f}s"
            )

        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save_model(save_path)

    env.close()
    print(f"\n[Complete] 訓練完成！最高回合獎勵: {best_reward:.1f}，最佳模型已儲存至: {save_path}")


def evaluate(
    env_name: str = "FlappyBird-rgb-v0",
    checkpoint_path: str = "checkpoints/flappy_bird_dqn_best.pth",
    num_episodes: int = 5
) -> None:
    if not os.path.exists(checkpoint_path):
        print(f"[Error] 找不到模型 Checkpoint 檔案: {checkpoint_path}")
        return

    print(f"[Eval] 正在初始化評估環境與載入模型: {checkpoint_path}")
    env = FlappyBirdEnvWrapper(env_name=env_name, frame_stack_num=4, screen_size=(84, 84))
    agent = DQNAgent(state_dim=(4, 84, 84), action_dim=2)
    agent.load_model(checkpoint_path)

    for ep in range(1, num_episodes + 1):
        state = env.reset()
        episode_reward = 0.0
        steps = 0
        while True:
            action = agent.select_action(state, evaluate=True)
            next_state, reward, done, _ = env.step(action)
            state = next_state
            episode_reward += reward
            steps += 1
            if done:
                break

        print(f"[Evaluation] Episode {ep}: Total Reward = {episode_reward:.1f}, Total Steps = {steps}")

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep Q-Network (DQN) Flappy Bird Agent")
    parser.add_argument("--mode", type=str, default="train", choices=["train", "eval", "render"], help="模式: train (訓練), eval (背景評估), render (開視窗即時觀看 AI 遊玩)")
    parser.add_argument("--env", type=str, default="FlappyBird-rgb-v0", help="Gym 環境名稱")
    parser.add_argument("--episodes", type=int, default=500, help="訓練/評估回合數")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/flappy_bird_dqn_best.pth", help="模型 Checkpoint 路徑")

    args = parser.parse_args()

    if args.mode == "train":
        train(env_name=args.env, max_episodes=args.episodes)
    elif args.mode == "render":
        from watch_ai_play import watch_ai_play
        watch_ai_play(checkpoint_path=args.checkpoint, num_episodes=args.episodes)
    else:
        evaluate(env_name=args.env, checkpoint_path=args.checkpoint, num_episodes=args.episodes)
