"""
環境預處理與連續幀堆疊 (Environment & Frame Preprocessing Wrapper)
==================================================================
1. 灰階轉換 (Grayscale Conversion: BGR -> Gray)
2. 畫面縮放 (Resize to 84x84)
3. 數值正規化 (Normalization [0.0, 1.0])
4. 連續 4 幀堆疊 (Frame Stacking) -> 讓模型能感知速度與鳥的飛行軌跡
5. 相容性設計：內建純 OpenCV/NumPy Flappy Bird 模擬器 (相容所有作業系統與 Python 版本)
"""

from collections import deque
import random
import sys
from typing import Tuple, Any, List
import numpy as np
import cv2

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class SimpleFlappyBirdSimulator:
    """
    純 OpenCV/NumPy 實作之 Flappy Bird 環境模擬器
    優化中空 corridor 保持與跳躍導向，協助 DQN 代理人快速學會飛過水管
    """

    def __init__(self, width: int = 288, height: int = 512) -> None:
        self.width = width
        self.height = height
        self.gravity = 0.6
        self.flap_strength = -7.5
        self.pipe_speed = 3.5
        self.pipe_width = 50
        self.pipe_gap = 135
        self.bird_radius = 12
        self.reset()

    def reset(self) -> np.ndarray:
        self.bird_x = 60.0
        self.bird_y = float(self.height // 2 - 20)
        self.bird_vy = -4.0  # 給予初始向上飛翔動量
        self.pipes: List[dict] = []
        self._spawn_pipe(x=self.width + 40)
        self._spawn_pipe(x=self.width + 40 + 190)
        self.score = 0
        return self._render()

    def _spawn_pipe(self, x: float) -> None:
        min_h = 70
        max_h = self.height - 150 - self.pipe_gap
        top_h = float(random.randint(min_h, max_h))
        self.pipes.append({'x': x, 'top_h': top_h, 'passed': False})

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        if action == 1:
            self.bird_vy = self.flap_strength

        self.bird_vy += self.gravity
        self.bird_y += self.bird_vy

        reward = 0.1  # 存活微幅正向獎勵
        done = False

        # 掉落地面或撞擊天花板
        if self.bird_y - self.bird_radius <= 0 or self.bird_y + self.bird_radius >= self.height - 30:
            done = True
            reward = -10.0

        # 低於 70% 畫面高度給予輕微下墜警告，引導向上跳躍
        if self.bird_y > self.height * 0.70:
            reward -= 0.2

        for pipe in self.pipes:
            pipe['x'] -= self.pipe_speed

            if not done:
                in_x_range = (self.bird_x + self.bird_radius > pipe['x']) and (self.bird_x - self.bird_radius < pipe['x'] + self.pipe_width)
                if in_x_range:
                    hit_top = self.bird_y - self.bird_radius < pipe['top_h']
                    hit_bottom = self.bird_y + self.bird_radius > pipe['top_h'] + self.pipe_gap
                    if hit_top or hit_bottom:
                        done = True
                        reward = -10.0

            if not pipe['passed'] and pipe['x'] + self.pipe_width < self.bird_x:
                pipe['passed'] = True
                reward = 15.0  # 成功通過水管給予高額 +15 獎勵
                self.score += 1

        if self.pipes and self.pipes[0]['x'] < -self.pipe_width:
            self.pipes.pop(0)
            last_x = self.pipes[-1]['x']
            self._spawn_pipe(x=last_x + 190)

        frame = self._render()
        return frame, reward, done, {'score': self.score}

    def _render(self) -> np.ndarray:
        img = np.full((self.height, self.width, 3), (112, 197, 206), dtype=np.uint8)

        for pipe in self.pipes:
            px = int(pipe['x'])
            pw = self.pipe_width
            top_h = int(pipe['top_h'])
            gap = self.pipe_gap

            cv2.rectangle(img, (px, 0), (px + pw, top_h), (115, 191, 46), -1)
            cv2.rectangle(img, (px - 2, top_h - 15), (px + pw + 2, top_h), (80, 140, 30), -1)

            bottom_y = top_h + gap
            cv2.rectangle(img, (px, bottom_y), (px + pw, self.height - 30), (115, 191, 46), -1)
            cv2.rectangle(img, (px - 2, bottom_y), (px + pw + 2, bottom_y + 15), (80, 140, 30), -1)

        cv2.rectangle(img, (0, self.height - 30), (self.width, self.height), (222, 216, 149), -1)

        bx = int(self.bird_x)
        by = int(self.bird_y)
        cv2.circle(img, (bx, by), self.bird_radius, (250, 200, 50), -1)
        cv2.circle(img, (bx + 4, by - 3), 3, (255, 255, 255), -1)
        cv2.circle(img, (bx + 5, by - 3), 1, (0, 0, 0), -1)

        return img

    def close(self) -> None:
        pass


class FlappyBirdEnvWrapper:
    """
    Flappy Bird 環境預處理包裝器
    """

    def __init__(self, env_name: str = "FlappyBird-rgb-v0", frame_stack_num: int = 4, screen_size: Tuple[int, int] = (84, 84)) -> None:
        self.env_name = env_name
        self.frame_stack_num = frame_stack_num
        self.screen_size = screen_size
        self.frames = deque(maxlen=frame_stack_num)
        self.env = self._make_env(env_name)

    def _make_env(self, env_name: str) -> Any:
        try:
            import flappy_bird_gym
            env = flappy_bird_gym.make(env_name)
            print(f"[Env] 成功載入系統 flappy-bird-gym 環境: {env_name}")
            return env
        except Exception:
            try:
                import gymnasium as gym
                env = gym.make(env_name, render_mode="rgb_array")
                print(f"[Env] 成功載入 Gymnasium 環境: {env_name}")
                return env
            except Exception:
                print("[Env] 使用純 OpenCV/NumPy Flappy Bird 模擬環境 (完整相容 Python 3.14+)")
                return SimpleFlappyBirdSimulator()

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            return np.zeros(self.screen_size, dtype=np.float32)

        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        else:
            gray = frame

        resized = cv2.resize(gray, self.screen_size, interpolation=cv2.INTER_AREA)
        normalized = resized.astype(np.float32) / 255.0
        return normalized

    def reset(self) -> np.ndarray:
        obs = self.env.reset()
        if isinstance(obs, tuple):
            frame = obs[0]
        else:
            frame = obs

        processed_frame = self.preprocess_frame(frame)
        self.frames.clear()
        for _ in range(self.frame_stack_num):
            self.frames.append(processed_frame)

        return np.stack(self.frames, axis=0)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        step_result = self.env.step(action)
        if len(step_result) == 5:
            frame, reward, terminated, truncated, info = step_result
            done = terminated or truncated
        else:
            frame, reward, done, info = step_result

        processed_frame = self.preprocess_frame(frame)
        self.frames.append(processed_frame)

        next_state = np.stack(self.frames, axis=0)
        return next_state, float(reward), bool(done), info

    def close(self) -> None:
        if hasattr(self.env, "close"):
            self.env.close()
