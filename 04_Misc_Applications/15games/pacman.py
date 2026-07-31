import pygame
import sys
import collections

# 遊戲設定
TILE_SIZE = 30
FPS = 30

# 顏色定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)

# 地圖定義
# 1: 牆壁, 0: 豆子, 2: 大力丸 (目前簡化為豆子或空格), 9: 空格
# 3: 幽靈出生地, 4: 玩家出生地
LEVEL = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 2, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 2, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 0, 1, 1, 9, 1, 9, 1, 1, 0, 1, 1, 1, 1, 1],
    [9, 9, 9, 9, 1, 0, 1, 9, 9, 3, 9, 9, 1, 0, 1, 9, 9, 9, 9],
    [1, 1, 1, 1, 1, 0, 1, 9, 1, 1, 1, 9, 1, 0, 1, 1, 1, 1, 1],
    [9, 9, 9, 9, 9, 0, 9, 9, 1, 9, 1, 9, 9, 0, 9, 9, 9, 9, 9],
    [1, 1, 1, 1, 1, 0, 1, 9, 1, 1, 1, 9, 1, 0, 1, 1, 1, 1, 1],
    [9, 9, 9, 9, 1, 0, 1, 9, 9, 9, 9, 9, 1, 0, 1, 9, 9, 9, 9],
    [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 2, 0, 0, 1, 0, 0, 0, 0, 4, 0, 0, 0, 0, 1, 0, 0, 2, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

ROWS = len(LEVEL)
COLS = len(LEVEL[0])
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE + 50 # 底部留白顯示分數

def get_valid_neighbors(r, c):
    neighbors = []
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and LEVEL[nr][nc] != 1:
            neighbors.append((nr, nc))
    return neighbors

def bfs_path(start, goal):
    """ 使用廣度優先搜尋尋找從 start 到 goal 的最短路徑 (回傳下一步) """
    if start == goal:
        return start
    
    queue = collections.deque([start])
    visited = {start: None}
    
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for nxt in get_valid_neighbors(*current):
            if nxt not in visited:
                visited[nxt] = current
                queue.append(nxt)
                
    if goal not in visited:
        return start # 找不到路徑
        
    # 回推路徑
    curr = goal
    while visited[curr] != start:
        curr = visited[curr]
    return curr

class Pacman:
    def __init__(self, r, c, image):
        self.r = r
        self.c = c
        self.image = pygame.transform.scale(image, (TILE_SIZE-2, TILE_SIZE-2))
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.speed = 0.2
        # 繪圖時的像素座標
        self.x = self.c * TILE_SIZE
        self.y = self.r * TILE_SIZE
        self.score = 0
        self.powered_up = False
        self.power_timer = 0

    def update(self):
        # 嘗試轉換方向 (如果下一個方向是合法的，並且目前在格子的正中央)
        if self.next_direction != (0, 0):
            # 檢查是否到達格子中心點附近
            if abs(self.x - self.c * TILE_SIZE) < 3 and abs(self.y - self.r * TILE_SIZE) < 3:
                nr = self.r + self.next_direction[0]
                nc = self.c + self.next_direction[1]
                # 簡單的地圖邊界處理 (左右穿梭)
                if nc < 0: nc = COLS - 1
                if nc >= COLS: nc = 0
                
                if 0 <= nr < ROWS and LEVEL[nr][nc] != 1:
                    self.direction = self.next_direction
                    self.x = self.c * TILE_SIZE
                    self.y = self.r * TILE_SIZE
                    self.next_direction = (0, 0)
        
        # 根據方向移動
        if self.direction != (0, 0):
            nr = self.r + self.direction[0]
            nc = self.c + self.direction[1]
            
            if nc < 0:
                self.c = COLS - 1
                self.x = self.c * TILE_SIZE
                return
            if nc >= COLS:
                self.c = 0
                self.x = self.c * TILE_SIZE
                return
                
            # 如果前方不是牆壁，就可以移動
            if LEVEL[nr][nc] != 1:
                self.x += self.direction[1] * self.speed * TILE_SIZE
                self.y += self.direction[0] * self.speed * TILE_SIZE
                # 更新所在的格子 (四捨五入)
                self.c = int(round(self.x / TILE_SIZE))
                self.r = int(round(self.y / TILE_SIZE))
            else:
                # 撞到牆壁，將座標貼齊格子
                self.x = self.c * TILE_SIZE
                self.y = self.r * TILE_SIZE

        # 處理吃豆子
        if LEVEL[self.r][self.c] == 0:
            LEVEL[self.r][self.c] = 9
            self.score += 10
        elif LEVEL[self.r][self.c] == 2:
            LEVEL[self.r][self.c] = 9
            self.score += 50
            self.powered_up = True
            self.power_timer = pygame.time.get_ticks()

        # 處理大力丸失效
        if self.powered_up and pygame.time.get_ticks() - self.power_timer > 5000:
            self.powered_up = False

    def draw(self, surface):
        # 依據方向旋轉圖片
        angle = 0
        if self.direction == (0, -1): angle = 180
        elif self.direction == (-1, 0): angle = 90
        elif self.direction == (1, 0): angle = -90
        
        rotated_img = pygame.transform.rotate(self.image, angle)
        surface.blit(rotated_img, (self.x + 1, self.y + 1))

class Ghost:
    def __init__(self, r, c, image):
        self.r = r
        self.c = c
        self.image = pygame.transform.scale(image, (TILE_SIZE-2, TILE_SIZE-2))
        self.x = self.c * TILE_SIZE
        self.y = self.r * TILE_SIZE
        self.speed = 0.15 # 幽靈速度稍慢
        self.move_timer = 0
        self.is_dead = False
        
    def update(self, pacman):
        if self.is_dead:
            return
            
        # 幽靈只在到達網格中心時決定下一步
        if abs(self.x - self.c * TILE_SIZE) < 3 and abs(self.y - self.r * TILE_SIZE) < 3:
            self.x = self.c * TILE_SIZE
            self.y = self.r * TILE_SIZE
            
            # 使用 BFS 尋找往小精靈的路徑
            if pacman.powered_up:
                # 逃跑邏輯：隨機選擇合法的下一步 (不回頭)
                neighbors = get_valid_neighbors(self.r, self.c)
                if neighbors:
                    next_r, next_c = neighbors[0] # 簡易隨機(取第一個)
                    self.r, self.c = next_r, next_c
            else:
                # 追逐邏輯
                next_step = bfs_path((self.r, self.c), (pacman.r, pacman.c))
                if next_step != (self.r, self.c):
                    self.r, self.c = next_step
                    
        # 朝目標格子移動
        target_x = self.c * TILE_SIZE
        target_y = self.r * TILE_SIZE
        if self.x < target_x: self.x += self.speed * TILE_SIZE
        elif self.x > target_x: self.x -= self.speed * TILE_SIZE
        if self.y < target_y: self.y += self.speed * TILE_SIZE
        elif self.y > target_y: self.y -= self.speed * TILE_SIZE

    def draw(self, surface, powered_up):
        if self.is_dead:
            return
        img = self.image
        if powered_up:
            # 幽靈害怕狀態，變成藍色
            img = self.image.copy()
            img.fill(BLUE, special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(img, (self.x + 1, self.y + 1))

def draw_maze(surface):
    for r in range(ROWS):
        for c in range(COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            if LEVEL[r][c] == 1:
                pygame.draw.rect(surface, BLUE, (x, y, TILE_SIZE, TILE_SIZE), 2)
            elif LEVEL[r][c] == 0:
                pygame.draw.circle(surface, WHITE, (x + TILE_SIZE//2, y + TILE_SIZE//2), 3)
            elif LEVEL[r][c] == 2:
                pygame.draw.circle(surface, YELLOW, (x + TILE_SIZE//2, y + TILE_SIZE//2), 8)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Pac-Man")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    try:
        pacman_img = pygame.image.load("assets/pacman.png")
        ghost_img = pygame.image.load("assets/ghost.png")
    except:
        # Fallback 建立純色圖
        pacman_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
        pacman_img.fill(YELLOW)
        ghost_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
        ghost_img.fill(RED)

    # 尋找出生點
    pacman = None
    ghosts = []
    for r in range(ROWS):
        for c in range(COLS):
            if LEVEL[r][c] == 4:
                pacman = Pacman(r, c, pacman_img)
                LEVEL[r][c] = 9
            elif LEVEL[r][c] == 3:
                ghosts.append(Ghost(r, c, ghost_img))
                LEVEL[r][c] = 9

    running = True
    game_over = False
    win = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_over and not win:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    pacman.next_direction = (-1, 0)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    pacman.next_direction = (1, 0)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    pacman.next_direction = (0, -1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    pacman.next_direction = (0, 1)

        if not game_over and not win:
            pacman.update()
            for ghost in ghosts:
                ghost.update(pacman)
                
                # 碰撞偵測
                distance = ((pacman.x - ghost.x)**2 + (pacman.y - ghost.y)**2)**0.5
                if distance < TILE_SIZE - 5 and not ghost.is_dead:
                    if pacman.powered_up:
                        ghost.is_dead = True
                        pacman.score += 200
                    else:
                        game_over = True

            # 檢查是否吃完所有豆子
            remaining_dots = sum(row.count(0) + row.count(2) for row in LEVEL)
            if remaining_dots == 0:
                win = True

        screen.fill(BLACK)
        draw_maze(screen)
        pacman.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen, pacman.powered_up)

        # 繪製介面
        score_text = font.render(f"Score: {pacman.score}", True, WHITE)
        screen.blit(score_text, (10, HEIGHT - 40))

        if game_over:
            go_text = font.render("GAME OVER", True, RED)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2))
        elif win:
            win_text = font.render("YOU WIN!", True, YELLOW)
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
