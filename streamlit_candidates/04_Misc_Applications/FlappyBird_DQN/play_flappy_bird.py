"""
================================================================================
人類玩家親自遊玩 Flappy Bird 遊戲主程式 (Human Playable Flappy Bird Game)
================================================================================
本程式使用 Gymnasium / flappy-bird-gymnasium 與 Pygame 引擎建構，
支援玩家透過鍵盤【空白鍵 (Spacebar)】控制小鳥進行跳躍與避障。

【控制說明】：
- 【空白鍵 (Spacebar)】: 控制小鳥向上向上撲翅 (Flap, Action = 1)
- 【Esc 鍵 / 關閉視窗】: 退出遊戲
================================================================================
"""

import sys
import time

# 相容性匯入 pygame / pygame-ce
try:
    import pygame
except ImportError:
    print("❌ 尚未安裝 Pygame，請執行: pip install pygame-ce 或 pip install pygame")
    sys.exit(1)

# 設定控制台編碼保護
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def play_flappy_bird_gymnasium() -> bool:
    """
    使用 Gymnasium (flappy-bird-gymnasium) 遊戲環境進行鍵盤互動遊玩
    """
    try:
        import gymnasium as gym
        import flappy_bird_gymnasium

        print("🎮 正在建立 Gymnasium FlappyBird-v0 遊戲視窗 (render_mode='human')...")
        env = gym.make("FlappyBird-v0", render_mode="human", use_lidar=False)
        
        obs, info = env.reset()
        clock = pygame.time.Clock()
        
        score = 0
        high_score = 0
        running = True

        print("✅ 遊戲已啟動！按下【空白鍵 Space】跳躍，按下【Esc】退出。")

        while running:
            # 預設動作: 不跳躍 (0)
            action = 0

            # Pygame 事件迴圈 (Event Loop)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        action = 1  # 玩家按下空白鍵 -> 發送跳躍 (Flap) 動作
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        break

            # 執行環境 Step
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # 累加得分
            if reward > 0:
                score += int(reward)
                high_score = max(score, high_score)

            # 設定 FPS 保持遊戲節奏自然 (30 FPS)
            clock.tick(30)

            # 遊戲結束自動重置 restart
            if done:
                print(f"💀 遊戲結束！本局得分: {score} | 最高得分: {high_score}")
                time.sleep(0.5)
                obs, info = env.reset()
                score = 0

        env.close()
        pygame.quit()
        return True

    except Exception as e:
        print(f"⚠️ Gymnasium 環境初始化提示: {e}")
        return False


def play_flappy_bird_pygame_native() -> None:
    """
    純 Pygame 備援引擎 (當 Gymnasium 模組未安裝或環境缺乏預設套件時發揮作用)
    """
    print("\n🎮 啟動純 Pygame 原生 Flappy Bird 遊戲視窗...")

    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 288, 512
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - Human Playable Engine")
    clock = pygame.time.Clock()

    import random

    # 小鳥參數
    bird_x, bird_y = 50, 250
    bird_velocity = 0
    gravity = 0.4
    jump_strength = -7.5
    bird_radius = 12

    # 水管參數
    pipe_width = 52
    pipe_gap = 100
    pipe_velocity = 3
    pipes = []

    def spawn_pipe():
        gap_y = random.randint(120, SCREEN_HEIGHT - 120)
        return {"x": SCREEN_WIDTH, "top": gap_y - pipe_gap // 2, "bottom": gap_y + pipe_gap // 2, "passed": False}

    pipes.append(spawn_pipe())

    score = 0
    high_score = 0
    running = True

    while running:
        action_jump = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    action_jump = True
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if action_jump:
            bird_velocity = jump_strength

        # 物理運動
        bird_velocity += gravity
        bird_y += bird_velocity

        # 移動水管
        for p in pipes:
            p["x"] -= pipe_velocity

        # 生成新水管
        if pipes[-1]["x"] < SCREEN_WIDTH - 160:
            pipes.append(spawn_pipe())

        # 刪除離開螢幕的水管
        if pipes[0]["x"] < -pipe_width:
            pipes.pop(0)

        # 碰撞檢測與計分
        game_over = False
        if bird_y - bird_radius <= 0 or bird_y + bird_radius >= SCREEN_HEIGHT - 50:
            game_over = True

        for p in pipes:
            if p["x"] < bird_x + bird_radius and p["x"] + pipe_width > bird_x - bird_radius:
                if bird_y - bird_radius < p["top"] or bird_y + bird_radius > p["bottom"]:
                    game_over = True
            
            if not p["passed"] and p["x"] + pipe_width < bird_x:
                p["passed"] = True
                score += 1
                high_score = max(score, high_score)

        # 繪製畫面
        screen.fill((113, 197, 207))  # 天空藍

        # 繪製地面
        pygame.draw.rect(screen, (222, 216, 149), (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
        pygame.draw.rect(screen, (87, 189, 43), (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 12))

        # 繪製水管
        for p in pipes:
            # 上水管
            pygame.draw.rect(screen, (115, 191, 46), (p["x"], 0, pipe_width, p["top"]))
            pygame.draw.rect(screen, (83, 137, 33), (p["x"] - 2, p["top"] - 15, pipe_width + 4, 15))
            # 下水管
            pygame.draw.rect(screen, (115, 191, 46), (p["x"], p["bottom"], pipe_width, SCREEN_HEIGHT - p["bottom"]))
            pygame.draw.rect(screen, (83, 137, 33), (p["x"] - 2, p["bottom"], pipe_width + 4, 15))

        # 繪製小鳥
        pygame.draw.circle(screen, (252, 213, 53), (int(bird_x), int(bird_y)), bird_radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(bird_x + 5), int(bird_y - 4)), 4)
        pygame.draw.circle(screen, (0, 0, 0), (int(bird_x + 6), int(bird_y - 4)), 2)

        # 顯示分數
        font = pygame.font.SysFont("Arial", 22, bold=True)
        score_surface = font.render(f"Score: {score}  Best: {high_score}", True, (255, 255, 255))
        screen.blit(score_surface, (10, 10))

        pygame.display.flip()
        clock.tick(30)

        # 遊戲結束重置
        if game_over:
            print(f"💀 遊戲結束！本局得分: {score} | 最高得分: {high_score}")
            time.sleep(0.5)
            bird_x, bird_y = 50, 250
            bird_velocity = 0
            pipes = [spawn_pipe()]
            score = 0

    pygame.quit()


def main() -> None:
    print("=" * 65)
    print("        🐤 鍵盤親自遊玩 Flappy Bird 遊戲 (Human Mode)        ")
    print("=" * 65)
    print("【玩法說明】: 按下【空白鍵 Space】控制小鳥跳躍避開水管，按下【Esc】退出。\n")

    # 優先試用 Gymnasium 官方環境，若未安裝則自動載入 Pygame 原生引擎
    success = play_flappy_bird_gymnasium()
    if not success:
        play_flappy_bird_pygame_native()


if __name__ == "__main__":
    main()
