"""
================================================================================
觀看 AI Agent 親自遊玩 Flappy Bird (AI Real-time Visual Demonstration)
================================================================================
本程式載入訓練完成之 DQN 模型檢查點 (checkpoints/flappy_bird_dqn_best.pth)，
採用與訓練時 100% 完全一致的環境與影像預處理管道 (FlappyBirdEnvWrapper)，
並開起 Pygame 視窗即時展示 AI 代理人即時預測 Q 值與控制小鳥進行遊戲！

【控制說明】：
- 按下【Esc 鍵】或【點擊視窗 X】: 退出展示
================================================================================
"""

import os
import sys
import time
import numpy as np
import torch
import cv2

try:
    import pygame
except ImportError:
    print("❌ 請先安裝 pygame: pip install pygame-ce 或 pip install pygame")
    sys.exit(1)

from agent import DQNAgent
from env_wrapper import FlappyBirdEnvWrapper

# 設定控制台編碼保護
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def watch_ai_play(checkpoint_path: str = "checkpoints/flappy_bird_dqn_best.pth", num_episodes: int = 5) -> None:
    if not os.path.exists(checkpoint_path):
        print(f"❌ 找不到模型 Checkpoint 檔案: {checkpoint_path}")
        print("💡 請先執行訓練命令: python train.py --mode train --episodes 1000")
        return

    print("=" * 65)
    print("      🤖 正在啟動 Pygame GUI 視窗展示 AI Agent 自行遊玩...      ")
    print("=" * 65)
    print(f"📦 載入模型權重: {os.path.abspath(checkpoint_path)}\n")

    # 1. 建立與訓練時 100% 一致的環境 Wrapper
    wrapper = FlappyBirdEnvWrapper(env_name="FlappyBird-rgb-v0", frame_stack_num=4, screen_size=(84, 84))

    # 2. 載入 DQN Agent
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = DQNAgent(state_dim=(4, 84, 84), action_dim=2, device=device)
    agent.load_model(checkpoint_path)
    agent.policy_net.eval()

    # 3. 初始化 Pygame 視窗 (288x512)
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 288, 512
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DQN Agent Autonomous Play - Flappy Bird")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 16, bold=True)
    big_font = pygame.font.SysFont("Arial", 22, bold=True)

    for ep in range(1, num_episodes + 1):
        state = wrapper.reset()
        score = 0
        steps = 0
        running = True
        q_val_display = (0.0, 0.0)

        print(f"▶️ 開始播放 Episode {ep}/{num_episodes} ...")

        while running:
            # Pygame 事件處理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    wrapper.close()
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    wrapper.close()
                    pygame.quit()
                    return

            # AI 神經網路推論決策 (evaluate=True 關閉隨機探索)
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            with torch.no_grad():
                q_values = agent.policy_net(state_tensor)[0]
                action = q_values.argmax().item()
                q_val_display = (q_values[0].item(), q_values[1].item())

            action_name = "FLAP 🚀" if action == 1 else "HOLD 🪂"

            # 執行環境 Step
            next_state, reward, done, info = wrapper.step(action)
            state = next_state
            steps += 1

            # 正確提取穿越水管之得分
            if isinstance(info, dict) and 'score' in info:
                score = info['score']
            elif reward >= 5.0:
                score += 1

            # 取得環境渲染畫面並繪製至 Pygame 視窗
            if hasattr(wrapper.env, "_render"):
                bgr_frame = wrapper.env._render()
                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                surf = pygame.surfarray.make_surface(np.transpose(rgb_frame, (1, 0, 2)))
                screen.blit(surf, (0, 0))
            else:
                screen.fill((113, 197, 207))

            # 資訊數據看板 Overlay
            info_bg = pygame.Surface((SCREEN_WIDTH, 75))
            info_bg.set_alpha(200)
            info_bg.fill((20, 20, 20))
            screen.blit(info_bg, (0, 0))

            txt_title = font.render(f"🤖 AI Agent | Ep: {ep}/{num_episodes}", True, (255, 215, 0))
            txt_action = font.render(f"Action: {action_name}", True, (50, 255, 50) if action == 1 else (200, 200, 200))
            txt_qval = font.render(f"Q(Hold): {q_val_display[0]:.2f}  Q(Flap): {q_val_display[1]:.2f}", True, (200, 200, 255))
            txt_score = big_font.render(f"Pipes Passed: {score}  (Steps: {steps})", True, (255, 255, 255))

            screen.blit(txt_title, (10, 5))
            screen.blit(txt_action, (150, 5))
            screen.blit(txt_qval, (10, 25))
            screen.blit(txt_score, (10, 47))

            pygame.display.flip()
            clock.tick(30)

            if done:
                print(f"💀 Episode {ep} 結束 | 成功穿過水管數: {score} | 總步數: {steps}")
                time.sleep(0.8)
                break

    wrapper.close()
    pygame.quit()
    print("\n🎉 展示播放完畢！")


if __name__ == "__main__":
    watch_ai_play()
