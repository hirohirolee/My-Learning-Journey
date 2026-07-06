# Royal Clash - main.py  (part 1 of 4: imports, config, Entity, Towers)
import pygame, math, random, sys, asyncio
pygame.init()

SCREEN_W, SCREEN_H = 480, 800
FPS = 60
RIVER_TOP    = SCREEN_H // 2 - 30
RIVER_BOTTOM = SCREEN_H // 2 + 30
RIVER_MID    = (RIVER_TOP + RIVER_BOTTOM) // 2
BRIDGE_LEFT_X  = SCREEN_W // 4
BRIDGE_RIGHT_X = 3 * SCREEN_W // 4
BRIDGE_W       = 60
AI_HALF_TOP    = 20
AI_HALF_BOTTOM = RIVER_TOP
COLOR_BG          = (60, 120, 40)
COLOR_RIVER       = (100, 180, 220)
COLOR_BRIDGE      = (180, 150, 90)
COLOR_PLAYER      = (50, 120, 220)
COLOR_PLAYER_DARK = (20, 60, 140)
COLOR_AI          = (210, 50, 50)
COLOR_AI_DARK     = (130, 20, 20)
COLOR_HP_GOOD     = (40, 210, 40)
COLOR_HP_MED      = (220, 200, 30)
COLOR_HP_BAD      = (220, 40, 40)
COLOR_ELIXIR      = (190, 60, 200)
COLOR_ELIXIR_BG   = (60, 20, 70)
COLOR_WHITE       = (255, 255, 255)
COLOR_BLACK       = (0, 0, 0)
COLOR_GOLD        = (255, 210, 60)
COLOR_INVALID     = (255, 0, 0)
ELIXIR_MAX        = 10
ELIXIR_START      = 5
ELIXIR_REGEN_RATE = 1.0 / 1.4

CONFIG = {
    "KingTower":     {"hp": 2400, "damage": 80,  "attack_range": 120, "attack_cooldown": 1.2, "width": 60, "height": 60},
    "PrincessTower": {"hp": 1400, "damage": 45,  "attack_range": 160, "attack_cooldown": 0.8, "width": 44, "height": 44},
    "Knight": {"hp": 600,  "damage": 80,  "speed": 90, "attack_range": 28,  "attack_cooldown": 1.0, "radius": 16, "elixir_cost": 3},
    "Archer": {"hp": 250,  "damage": 55,  "speed": 75, "attack_range": 120, "attack_cooldown": 0.9, "radius": 12, "elixir_cost": 3},
    "Giant":  {"hp": 1800, "damage": 120, "speed": 50, "attack_range": 30,  "attack_cooldown": 1.5, "radius": 22, "elixir_cost": 5},
}

# ---- Entity base class ----
class Entity:
    def __init__(self, x, y, hp, team):
        self.x = float(x); self.y = float(y)
        self.hp = hp; self.max_hp = hp
        self.team = team; self.alive = True

    @property
    def color(self):
        return COLOR_PLAYER if self.team == "player" else COLOR_AI

    @property
    def dark_color(self):
        return COLOR_PLAYER_DARK if self.team == "player" else COLOR_AI_DARK

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False

    def hp_fraction(self):
        return max(0.0, self.hp / self.max_hp) if self.max_hp else 0.0

    def hp_bar_color(self):
        f = self.hp_fraction()
        if f > 0.6: return COLOR_HP_GOOD
        if f > 0.3: return COLOR_HP_MED
        return COLOR_HP_BAD

    def draw_hp_bar(self, surface, bar_x, bar_y, bar_w=40, bar_h=5):
        pygame.draw.rect(surface, COLOR_BLACK, (bar_x, bar_y, bar_w, bar_h))
        filled = int(bar_w * self.hp_fraction())
        if filled > 0:
            pygame.draw.rect(surface, self.hp_bar_color(), (bar_x, bar_y, filled, bar_h))
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, bar_y, bar_w, bar_h), 1)


# ---- Tower classes ----
# DESIGN CHOICE: King Tower is ALWAYS active from game start (simpler MVP).
class Tower(Entity):
    def __init__(self, x, y, kind, team):
        cfg = CONFIG[kind]
        super().__init__(x, y, cfg["hp"], team)
        self.kind = kind
        self.damage = cfg["damage"]
        self.attack_range = cfg["attack_range"]
        self.attack_cooldown = cfg["attack_cooldown"]
        self.width = cfg["width"]; self.height = cfg["height"]
        self.attack_timer = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)

    def update(self, dt, enemies):
        if not self.alive: return
        self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attack_timer == 0.0:
            target = self._nearest_in_range(enemies)
            if target:
                target.take_damage(self.damage)
                self.attack_timer = self.attack_cooldown

    def _nearest_in_range(self, enemies):
        best, bd = None, float("inf")
        for e in enemies:
            if not e.alive: continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d <= self.attack_range and d < bd:
                best, bd = e, d
        return best

    def draw(self, surface):
        if not self.alive: return
        r = self.rect
        pygame.draw.rect(surface, self.dark_color, r.inflate(4, 4))
        pygame.draw.rect(surface, self.color, r)
        for i in range(3):
            bx = r.left + 6 + i * (r.width // 3)
            pygame.draw.rect(surface, self.dark_color, (bx, r.top - 6, 10, 8))
        f = pygame.font.SysFont(None, 16)
        lbl = f.render("K" if self.kind == "KingTower" else "P", True, COLOR_WHITE)
        surface.blit(lbl, (self.x - lbl.get_width()//2, self.y - lbl.get_height()//2))
        bw = self.width
        self.draw_hp_bar(surface, self.x - bw//2, r.top - 10, bw, 6)


class KingTower(Tower):
    def __init__(self, x, y, team): super().__init__(x, y, "KingTower", team)

class PrincessTower(Tower):
    def __init__(self, x, y, team): super().__init__(x, y, "PrincessTower", team)

# ---- Unit classes ----
# Each unit: scans for targets, moves toward them, attacks in range, separates from allies.
class Unit(Entity):
    AGGRO_RANGE = 200  # pixels -- radius for automatic target lock

    def __init__(self, x, y, kind, team):
        cfg = CONFIG[kind]
        super().__init__(x, y, cfg["hp"], team)
        self.kind = kind
        self.damage = cfg["damage"]; self.speed = cfg["speed"]
        self.attack_range = cfg["attack_range"]
        self.attack_cooldown = cfg["attack_cooldown"]
        self.radius = cfg["radius"]
        self.attack_timer = 0.0
        self.target = None  # current Entity target
        # --- Lane system ---
        # Lane is decided at spawn by X position so units use the nearest bridge.
        # 0 = left lane  (bridge at BRIDGE_LEFT_X)
        # 1 = right lane (bridge at BRIDGE_RIGHT_X)
        self.lane      = 0 if x <= SCREEN_W // 2 else 1
        self.waypoints = self._build_waypoints(team)   # river-crossing checkpoints
        self.wp_idx    = 0                              # index of next waypoint

    def _find_target(self, enemy_units, enemy_towers):
        # Base priority: nearest unit in aggro range, else nearest tower
        best_u = self._nearest_alive(enemy_units)
        if best_u and math.hypot(best_u.x - self.x, best_u.y - self.y) <= self.AGGRO_RANGE:
            return best_u
        return self._nearest_alive(enemy_towers)

    def _nearest_alive(self, entities):
        best, bd = None, float("inf")
        for e in entities:
            if not e.alive: continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < bd: best, bd = e, d
        return best

    def _build_waypoints(self, team):
        """
        Two waypoints guide each unit through the correct bridge lane before
        it enters enemy territory.  Once both are consumed the unit navigates
        freely toward its target (normal behaviour).

        Player units move upward  (y decreasing) -> approach river bottom, exit top.
        AI units    move downward (y increasing) -> approach river top,    exit bottom.
        """
        bx = BRIDGE_LEFT_X if self.lane == 0 else BRIDGE_RIGHT_X
        if team == "player":
            return [(bx, RIVER_BOTTOM - 15), (bx, RIVER_TOP + 15)]
        else:
            return [(bx, RIVER_TOP  + 15),   (bx, RIVER_BOTTOM - 15)]

    def update(self, dt, enemy_units, enemy_towers, all_units, all_towers=None):
        if not self.alive: return
        # Guard: clear dead target so re-acquire fires below (None-error guard)
        if self.target is not None and not self.target.alive:
            self.target = None
        self.target = self._find_target(enemy_units, enemy_towers)
        self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.target is not None:
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist <= self.attack_range:
                if self.attack_timer == 0.0:
                    self.target.take_damage(self.damage)
                    self.attack_timer = self.attack_cooldown
            else:
                # Not in attack range: follow lane waypoints first, then target.
                if self.wp_idx < len(self.waypoints):
                    wx, wy = self.waypoints[self.wp_idx]
                    if math.hypot(wx - self.x, wy - self.y) < 25:  # waypoint reached
                        self.wp_idx += 1
                    else:
                        self._move_toward(wx, wy, dt)
                else:
                    # All waypoints consumed: head straight for target.
                    self._move_toward(self.target.x, self.target.y, dt)
        # Tower avoidance and unit separation applied every frame regardless of state.
        if all_towers:
            self._avoid_towers(all_towers, dt)
        self._separate(all_units)

    def _move_toward(self, tx, ty, dt):
        # Division-by-zero guard: skip if already at target position
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.5: return
        self.x += (dx / dist) * self.speed * dt
        self.y += (dy / dist) * self.speed * dt

    def _separate(self, all_units):
        # Soft push-back so units do not fully overlap each other
        for other in all_units:
            if other is self or not other.alive: continue
            dx, dy = self.x - other.x, self.y - other.y
            dist = math.hypot(dx, dy)
            min_d = self.radius + other.radius
            if 0.1 < dist < min_d:  # zero-dist guard included
                ov = (min_d - dist) / 2.0
                self.x += (dx / dist) * ov
                self.y += (dy / dist) * ov

    def _avoid_towers(self, towers, dt):
        """
        Closest-point-on-rect steering: pushes the unit away from any live tower
        bounding box that is within AVOIDANCE_DIST pixels of the unit centre,
        EXCEPT the unit's current attack target (so we can still walk up to strike).

        Tune AVOIDANCE_DIST and AVOIDANCE_SPEED to adjust how wide a berth units give.
        """
        AVOIDANCE_DIST  = self.radius + 40   # activation radius beyond rect edge (px)
        AVOIDANCE_SPEED = self.speed * 1.5   # max lateral push (pixels / second)
        for t in towers:
            if not t.alive or t is self.target:
                continue  # never push away from the tower we are currently attacking
            r = t.rect
            # Closest point on the tower rect to this unit's centre
            cx = max(r.left, min(self.x, r.right))
            cy = max(r.top,  min(self.y, r.bottom))
            dx, dy = self.x - cx, self.y - cy
            dist = math.hypot(dx, dy)
            if 0.1 < dist < AVOIDANCE_DIST:       # zero-dist guard included
                strength = (AVOIDANCE_DIST - dist) / AVOIDANCE_DIST  # 0 -> 1
                self.x  += (dx / dist) * AVOIDANCE_SPEED * strength * dt
                self.y  += (dy / dist) * AVOIDANCE_SPEED * strength * dt

    def draw(self, surface):
        if not self.alive: return
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self.dark_color, (ix+2, iy+2), self.radius)
        pygame.draw.circle(surface, self.color, (ix, iy), self.radius)
        pygame.draw.circle(surface, COLOR_WHITE, (ix, iy), self.radius, 2)
        f = pygame.font.SysFont(None, int(self.radius * 1.6))
        lbl = f.render(self.kind[0], True, COLOR_WHITE)
        surface.blit(lbl, (ix - lbl.get_width()//2, iy - lbl.get_height()//2))
        bw = self.radius * 2 + 4
        self.draw_hp_bar(surface, ix - bw//2, iy - self.radius - 12, bw, 5)


class Knight(Unit):
    # Melee -- targets nearest unit then nearest tower
    def __init__(self, x, y, team): super().__init__(x, y, "Knight", team)

class Archer(Unit):
    # Ranged -- same priority as Knight but attacks from a distance
    def __init__(self, x, y, team): super().__init__(x, y, "Archer", team)

class Giant(Unit):
    # Tanky slow unit -- TOWERS ONLY, ignores enemy units
    def __init__(self, x, y, team): super().__init__(x, y, "Giant", team)
    def _find_target(self, enemy_units, enemy_towers):
        return self._nearest_alive(enemy_towers)  # towers only

# ---- AI Controller ----
class AIController:
    # Probabilistic AI: 70% deploy chance if affordable, prefers Giant at elixir>=5
    DECISION_INTERVAL = 2.0

    def __init__(self): self.timer = self.DECISION_INTERVAL

    def update(self, dt, ai_elixir, spawn_callback, ai_towers):
        self.timer -= dt
        if self.timer > 0: return ai_elixir
        self.timer = self.DECISION_INTERVAL
        cards = [(Knight, CONFIG["Knight"]["elixir_cost"]),
                 (Archer, CONFIG["Archer"]["elixir_cost"]),
                 (Giant,  CONFIG["Giant"]["elixir_cost"])]
        affordable = [(c, co) for c, co in cards if ai_elixir >= co]
        if not affordable: return ai_elixir
        if random.random() > 0.70: return ai_elixir  # 30% chance to hold
        if ai_elixir >= CONFIG["Giant"]["elixir_cost"] and random.random() < 0.50:
            chosen_cls, chosen_cost = Giant, CONFIG["Giant"]["elixir_cost"]
        else:
            chosen_cls, chosen_cost = random.choice(affordable)
        sx, sy = self._random_spawn(ai_towers)
        spawn_callback(chosen_cls, sx, sy, "ai")
        return ai_elixir - chosen_cost

    def _random_spawn(self, ai_towers, attempts=20):
        for _ in range(attempts):
            x = random.randint(30, SCREEN_W - 30)
            y = random.randint(AI_HALF_TOP + 20, AI_HALF_BOTTOM - 20)
            if all(not t.alive or not t.rect.inflate(20,20).collidepoint(x,y) for t in ai_towers):
                return x, y
        return SCREEN_W // 2, (AI_HALF_TOP + AI_HALF_BOTTOM) // 2


# ---- UI / HUD helpers ----
FONT_LARGE = FONT_MED = FONT_SMALL = FONT_TINY = None

def init_fonts():
    global FONT_LARGE, FONT_MED, FONT_SMALL, FONT_TINY
    FONT_LARGE = pygame.font.SysFont(None, 72)
    FONT_MED   = pygame.font.SysFont(None, 36)
    FONT_SMALL = pygame.font.SysFont(None, 24)
    FONT_TINY  = pygame.font.SysFont(None, 18)

def draw_background(surface):
    surface.fill(COLOR_BG)
    pygame.draw.rect(surface, COLOR_RIVER, (0, RIVER_TOP, SCREEN_W, RIVER_BOTTOM - RIVER_TOP))
    for bx in (BRIDGE_LEFT_X, BRIDGE_RIGHT_X):
        pygame.draw.rect(surface, COLOR_BRIDGE, (bx - BRIDGE_W//2, RIVER_TOP, BRIDGE_W, RIVER_BOTTOM - RIVER_TOP))
    pygame.draw.line(surface, COLOR_WHITE, (0, RIVER_MID), (SCREEN_W, RIVER_MID), 1)
    for gy in range(0, SCREEN_H, 80):
        pygame.draw.line(surface, (50, 110, 35), (0, gy), (SCREEN_W, gy), 1)
    for gx in range(0, SCREEN_W, 80):
        pygame.draw.line(surface, (50, 110, 35), (gx, 0), (gx, SCREEN_H), 1)

def draw_elixir_bar(surface, elixir, x, y):
    bar_w, bar_h = 240, 20
    pip_w = bar_w // ELIXIR_MAX
    pygame.draw.rect(surface, COLOR_ELIXIR_BG, (x, y, bar_w, bar_h), border_radius=4)
    for i in range(ELIXIR_MAX):
        col = COLOR_ELIXIR if i < int(elixir) else ((120,40,130) if i < elixir else (40,15,45))
        pygame.draw.rect(surface, col, pygame.Rect(x + i*pip_w+1, y+1, pip_w-2, bar_h-2), border_radius=2)
    pygame.draw.rect(surface, COLOR_WHITE, (x, y, bar_w, bar_h), 2, border_radius=4)
    t = FONT_TINY.render("Elixir: {}/{}".format(int(elixir), ELIXIR_MAX), True, COLOR_WHITE)
    surface.blit(t, (x + bar_w + 6, y + 3))

def draw_card_buttons(surface, cards_config, selected_idx, player_elixir, flash_invalid):
    card_w, card_h = 90, 80
    total_w = len(cards_config)*card_w + (len(cards_config)-1)*10
    sx = (SCREEN_W - total_w)//2
    base_y = SCREEN_H - card_h - 10
    for i, (name, cls, cost) in enumerate(cards_config):
        cx = sx + i*(card_w+10)
        aff = player_elixir >= cost
        sel = (i == selected_idx)
        pygame.draw.rect(surface, (40,60,100) if aff else (40,40,50), (cx, base_y, card_w, card_h), border_radius=6)
        if sel:
            pygame.draw.rect(surface, COLOR_GOLD, (cx-3, base_y-3, card_w+6, card_h+6), 3, border_radius=8)
        elif not aff:
            gs = pygame.Surface((card_w, card_h), pygame.SRCALPHA); gs.fill((0,0,0,120))
            surface.blit(gs, (cx, base_y))
        pygame.draw.circle(surface, COLOR_PLAYER if aff else (80,80,100), (cx+card_w//2, base_y+28), 18)
        lbl = FONT_TINY.render(name[0], True, COLOR_WHITE)
        surface.blit(lbl, (cx+card_w//2-lbl.get_width()//2, base_y+28-lbl.get_height()//2))
        nt = FONT_TINY.render(name, True, COLOR_WHITE if aff else (120,120,130))
        surface.blit(nt, (cx+card_w//2-nt.get_width()//2, base_y+52))
        ct = FONT_SMALL.render(str(cost), True, COLOR_ELIXIR if aff else (100,60,110))
        surface.blit(ct, (cx+card_w-18, base_y+4))
    if flash_invalid:
        w = FONT_SMALL.render("Invalid placement!", True, COLOR_INVALID)
        surface.blit(w, (SCREEN_W//2-w.get_width()//2, RIVER_BOTTOM+10))

def draw_hud(surface, pel, ael, cards, sel, flash, elapsed):
    hs = pygame.Surface((SCREEN_W, 110), pygame.SRCALPHA); hs.fill((10,10,20,180))
    surface.blit(hs, (0, SCREEN_H-110))
    draw_elixir_bar(surface, pel, 10, SCREEN_H-108)
    draw_elixir_bar(surface, ael, 10, 4)
    draw_card_buttons(surface, cards, sel, pel, flash)
    mm, ss = int(elapsed)//60, int(elapsed)%60
    t = FONT_MED.render("{:02d}:{:02d}".format(mm, ss), True, COLOR_WHITE)
    surface.blit(t, (SCREEN_W//2-t.get_width()//2, 6))

def draw_game_over(surface, player_won):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); ov.fill((0,0,0,160))
    surface.blit(ov, (0,0))
    msg = "VICTORY!" if player_won else "DEFEAT"
    col = COLOR_GOLD if player_won else COLOR_INVALID
    tm = FONT_LARGE.render(msg, True, col)
    surface.blit(tm, (SCREEN_W//2-tm.get_width()//2, SCREEN_H//2-tm.get_height()//2-40))
    ts = FONT_MED.render("Press R to Restart", True, COLOR_WHITE)
    surface.blit(ts, (SCREEN_W//2-ts.get_width()//2, SCREEN_H//2+20))

# ---- Game State Manager ----
# State machine: PLAYING -> GAME_OVER (R to reset back to PLAYING)
STATE_PLAYING   = "PLAYING"
STATE_GAME_OVER = "GAME_OVER"

class GameState:
    CARDS = [
        ("Knight", Knight, CONFIG["Knight"]["elixir_cost"]),
        ("Archer", Archer, CONFIG["Archer"]["elixir_cost"]),
        ("Giant",  Giant,  CONFIG["Giant"]["elixir_cost"]),
    ]

    def __init__(self): self.reset()

    def reset(self):
        self.state         = STATE_PLAYING
        self.player_elixir = float(ELIXIR_START)
        self.ai_elixir     = float(ELIXIR_START)
        self.elapsed_time  = 0.0
        self.selected_card = 0
        self.flash_invalid = False
        self.flash_timer   = 0.0
        self.player_won    = False
        pw, ph = SCREEN_W, SCREEN_H
        self.player_king    = KingTower(pw//2, ph-60, "player")
        self.player_tower_l = PrincessTower(pw//4, ph-160, "player")
        self.player_tower_r = PrincessTower(3*pw//4, ph-160, "player")
        self.ai_king        = KingTower(pw//2, 60, "ai")
        self.ai_tower_l     = PrincessTower(pw//4, 160, "ai")
        self.ai_tower_r     = PrincessTower(3*pw//4, 160, "ai")
        self.player_towers  = [self.player_king, self.player_tower_l, self.player_tower_r]
        self.ai_towers      = [self.ai_king, self.ai_tower_l, self.ai_tower_r]
        self.player_units   = []
        self.ai_units       = []
        self.ai_controller  = AIController()

    def spawn_unit(self, unit_cls, x, y, team):
        u = unit_cls(x, y, team)
        (self.player_units if team == "player" else self.ai_units).append(u)

    def _regen_elixir(self, dt):
        # Guard: clamp to [0, ELIXIR_MAX] -- no negative, no overflow
        self.player_elixir = min(ELIXIR_MAX, self.player_elixir + ELIXIR_REGEN_RATE * dt)
        self.ai_elixir     = min(ELIXIR_MAX, self.ai_elixir     + ELIXIR_REGEN_RATE * dt)

    def handle_event(self, event):
        if self.state == STATE_GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.selected_card = event.key - pygame.K_1
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._try_deploy(*pygame.mouse.get_pos())
        if event.type == pygame.MOUSEWHEEL:
            self.selected_card = (self.selected_card - event.y) % len(self.CARDS)

    def _try_deploy(self, mx, my):
        # Invalid: above river, in HUD, on a tower bounding box
        if my <= RIVER_BOTTOM:
            self._show_invalid(); return
        if my >= SCREEN_H - 110:
            return
        for t in self.player_towers + self.ai_towers:
            if t.alive and t.rect.inflate(10,10).collidepoint(mx, my):
                self._show_invalid(); return
        name, unit_cls, cost = self.CARDS[self.selected_card]
        if self.player_elixir < cost:
            self._show_invalid(); return
        self.player_elixir -= cost
        self.player_elixir = max(0.0, self.player_elixir)  # belt-and-suspenders guard
        self.spawn_unit(unit_cls, float(mx), float(my), "player")

    def _show_invalid(self):
        self.flash_invalid = True; self.flash_timer = 1.2

    def update(self, dt):
        if self.state != STATE_PLAYING: return
        self.elapsed_time += dt
        if self.flash_invalid:
            self.flash_timer -= dt
            if self.flash_timer <= 0: self.flash_invalid = False; self.flash_timer = 0.0
        self._regen_elixir(dt)
        # AI update
        self.ai_elixir = self.ai_controller.update(dt, self.ai_elixir, self.spawn_unit, self.ai_towers)
        self.ai_elixir = max(0.0, min(ELIXIR_MAX, self.ai_elixir))  # clamp guard
        # Tower updates: each attacks the opposing side's units + towers
        for t in self.player_towers: t.update(dt, self.ai_units + self.ai_towers)
        for t in self.ai_towers:     t.update(dt, self.player_units + self.player_towers)
        # Unit updates (use snapshots so mid-loop kills do not affect iteration)
        pu, au = self.player_units[:], self.ai_units[:]
        # Build one combined alive-tower list to share with every unit's avoidance pass.
        all_alive_towers = [t for t in self.player_towers + self.ai_towers if t.alive]
        for u in pu: u.update(dt, au, [t for t in self.ai_towers     if t.alive], pu, all_alive_towers)
        for u in au: u.update(dt, pu, [t for t in self.player_towers if t.alive], au, all_alive_towers)
        # Purge dead entities immediately after update
        self.player_units = [u for u in self.player_units if u.alive]
        self.ai_units     = [u for u in self.ai_units     if u.alive]
        # Win condition
        if not self.ai_king.alive:     self.player_won = True;  self.state = STATE_GAME_OVER
        elif not self.player_king.alive: self.player_won = False; self.state = STATE_GAME_OVER

    def draw(self, surface):
        draw_background(surface)
        for t in self.player_towers + self.ai_towers: t.draw(surface)
        for u in self.ai_units:    u.draw(surface)
        for u in self.player_units: u.draw(surface)
        draw_hud(surface, self.player_elixir, self.ai_elixir,
                 self.CARDS, self.selected_card, self.flash_invalid, self.elapsed_time)
        if self.state == STATE_GAME_OVER:
            draw_game_over(surface, self.player_won)

# ---- Main game loop (async for Pygbag / WebAssembly) ----
# Pygbag requires an async main so the browser event loop can yield each frame.
async def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Royal Clash")
    clock = pygame.time.Clock()
    init_fonts()
    game = GameState()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds per frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; break
            game.handle_event(event)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
        await asyncio.sleep(0)  # yield control to browser event loop each frame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
