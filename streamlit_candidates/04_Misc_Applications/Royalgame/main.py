import streamlit as st
st.title('main.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

# Royal Clash - Epic 1v1 RTS Battle (Phase 3 "Beyond Clash Royale" Ultimate Edition)
# Run: python main.py
# Controls:
# - 1~0, -, = or Scroll/Click to select Cards (12 Cards Total!)
# - Left Click on your half (or anywhere for spells) to deploy
# - H: Activate Hero Commander Ultimate Skill (Zero Elixir!)
# - C: Cycle Hero Commander (Paladin King / Archmage / Mecha Overlord)
# - E: Claim Roguelike Tactical Evolution Perk (When available!)
# - D: Toggle Deck Mode (Master 12-Card View vs Pro 4+1 Cycling Hand)
# - M: Cycle Game Mode (Classic / 3X Infinite Elixir / Survival Horde)
# - T: Cycle Arena Theme (Royal Forest / Inferno Volcano / Frozen Glacier)
# - R: Restart Game

import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()

# ── Screen & Setup ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 480, 800
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Royal Clash — Phase 3 Beyond Clash Royale")
clock = pygame.time.Clock()

# Fonts
FONT_TITLE = pygame.font.SysFont("impact", 44)
FONT_LARGE = pygame.font.SysFont("impact", 26)
FONT_MED   = pygame.font.SysFont("arial", 15, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 11, bold=True)

# ── Constants & Arena Themes ────────────────────────────────────────────────
RIVER_TOP    = SCREEN_H // 2 - 30
RIVER_BOTTOM = SCREEN_H // 2 + 30
RIVER_MID    = SCREEN_H // 2
BRIDGE_LEFT_X  = SCREEN_W // 4
BRIDGE_RIGHT_X = 3 * SCREEN_W // 4
BRIDGE_W       = 60
AI_HALF_TOP    = 20
AI_HALF_BOTTOM = RIVER_TOP

ELIXIR_MAX        = 10.0
ELIXIR_START      = 5.0
ELIXIR_REGEN_RATE = 1.0 / 1.4

THEMES = [
    {
        "name": "🌲 Forest Arena",
        "bg": (20, 54, 33), "river": (30, 111, 159), "bridge": (168, 136, 80),
        "night_bg": (10, 24, 18), "night_river": (15, 60, 90)
    },
    {
        "name": "🌋 Volcano Arena",
        "bg": (39, 14, 14), "river": (220, 38, 38), "bridge": (63, 63, 70),
        "night_bg": (20, 6, 6), "night_river": (180, 20, 20)
    },
    {
        "name": "❄️ Glacier Arena",
        "bg": (30, 41, 59), "river": (2, 132, 199), "bridge": (203, 213, 225),
        "night_bg": (15, 23, 35), "night_river": (2, 80, 140)
    }
]

# Colors
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_GOLD  = (250, 204, 21)
C_RED   = (239, 68, 68)
C_BLUE  = (59, 130, 246)
C_CYAN  = (56, 189, 248)
C_PURPLE= (217, 70, 239)
C_SPELL = (255, 120, 31)
C_FREEZE= (186, 230, 253)
C_RAGE  = (244, 63, 94)
C_HEAL  = (74, 222, 128)
C_INVULN= (253, 224, 71)

# ── 12-Card Master Configuration ────────────────────────────────────────────
CONFIG = {
    "KingTower":     {"hp": 3000, "damage": 95,  "range": 135, "cooldown": 1.1, "w": 64, "h": 64},
    "PrincessTower": {"hp": 1700, "damage": 58,  "range": 165, "cooldown": 0.8, "w": 46, "h": 46},
    "Knight":   {"hp": 700,  "damage": 85,  "speed": 90,  "range": 28,  "cooldown": 1.0, "radius": 16, "cost": 3},
    "Archer":   {"hp": 270,  "damage": 55,  "speed": 75,  "range": 130, "cooldown": 0.9, "radius": 12, "cost": 3},
    "Giant":    {"hp": 2200, "damage": 130, "speed": 45,  "range": 32,  "cooldown": 1.5, "radius": 22, "cost": 5},
    "Wizard":   {"hp": 350,  "damage": 95,  "speed": 68,  "range": 115, "cooldown": 1.4, "radius": 14, "cost": 4, "splash": 55},
    "Skeleton": {"hp": 65,   "damage": 45,  "speed": 110, "range": 22,  "cooldown": 0.7, "radius": 9,  "cost": 3, "swarm": 4},
    "Valkyrie": {"hp": 1150, "damage": 110, "speed": 70,  "range": 35,  "cooldown": 1.2, "radius": 18, "cost": 4, "whirlwind": 50},
    "Prince":   {"hp": 1300, "damage": 180, "speed": 75,  "range": 30,  "cooldown": 1.4, "radius": 18, "cost": 5, "charge_mult": 2.5},
    "Cannon":   {"hp": 900,  "damage": 75,  "range": 155, "cooldown": 0.7, "radius": 20, "cost": 3, "is_building": True, "lifetime": 30.0},
    "Fireball": {"damage": 260, "radius": 75, "cost": 4, "is_spell": True},
    "Freeze":   {"radius": 85, "duration": 3.5, "cost": 3, "is_spell": True},
    # 2 Legendary Cards:
    "InfDragon":{"hp": 950,  "damage": 35,  "speed": 65,  "range": 105, "cooldown": 0.3, "radius": 18, "cost": 4, "is_air": True},
    "MegaKnight":{"hp": 2500, "damage": 145, "speed": 60,  "range": 34,  "cooldown": 1.5, "radius": 24, "cost": 6, "splash": 60},
}

# ── VFX Classes ─────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, radius, life):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.radius = float(radius)
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.radius = max(0.2, self.radius * (1 - 1.5 * dt))
        self.life -= dt
        return self.life > 0

    def draw(self, surf, ox=0, oy=0):
        if self.radius <= 0.5 or self.life <= 0: return
        pygame.draw.circle(surf, self.color, (int(self.x + ox), int(self.y + oy)), int(self.radius))

class FloatingText:
    def __init__(self, x, y, text, color, is_big=False, life=0.8):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.is_big = is_big
        self.life = life
        self.max_life = life
        self.vy = -45

    def update(self, dt):
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0: return
        font = FONT_LARGE if self.is_big else FONT_MED
        txt_surf = font.render(self.text, True, self.color)
        alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        alpha_surf.fill((255, 255, 255, alpha))
        txt_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        rect = txt_surf.get_rect(center=(int(self.x + ox), int(self.y + oy)))
        surf.blit(txt_surf, rect)

class Projectile:
    def __init__(self, x, y, tx, ty, speed, damage, splash_radius, team, kind, target_entity=None, source_entity=None):
        self.x, self.y = x, y
        self.tx, self.ty = tx, ty
        self.speed = speed
        self.damage = damage
        self.splash_radius = splash_radius
        self.team = team
        self.kind = kind
        self.target_entity = target_entity
        self.source_entity = source_entity
        self.alive = True

    def update(self, dt, enemies, particles, floating_texts):
        if not self.alive: return
        if self.target_entity and self.target_entity.alive:
            self.tx, self.ty = self.target_entity.x, self.target_entity.y
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step or dist < 10:
            self.x, self.y = self.tx, self.ty
            self.explode(enemies, particles, floating_texts)
            self.alive = False
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            if random.random() < 0.6:
                col = C_SPELL if self.kind in ("fireball", "meteor") else C_WHITE
                particles.append(Particle(self.x, self.y, random.uniform(-15,15), random.uniform(-15,15), col, 4 if self.kind != "arrow" else 2, 0.25))

    def explode(self, enemies, particles, floating_texts):
        if self.kind in ("fireball", "meteor") or self.splash_radius > 0:
            sr = max(self.splash_radius, 40)
            for e in enemies:
                if not e.alive: continue
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d <= sr:
                    dmg = self.damage if d <= sr * 0.6 else int(self.damage * 0.7)
                    e.take_damage(dmg, floating_texts, particles, self.source_entity)
            cnt = 28 if self.kind == "meteor" else 16
            for _ in range(cnt):
                ang = random.uniform(0, math.pi * 2)
                spd = random.uniform(30, 150)
                col = random.choice([C_GOLD, C_SPELL, C_RED])
                particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, col, random.uniform(4, 9), 0.5))
        else:
            if self.target_entity and self.target_entity.alive:
                self.target_entity.take_damage(self.damage, floating_texts, particles, self.source_entity)
            elif enemies:
                best = min(enemies, key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)
                if best and math.hypot(best.x - self.x, best.y - self.y) <= 40:
                    best.take_damage(self.damage, floating_texts, particles, self.source_entity)

    def draw(self, surf, ox=0, oy=0):
        if not self.alive: return
        pos = (int(self.x + ox), int(self.y + oy))
        if self.kind == "meteor":
            pygame.draw.circle(surf, C_GOLD, pos, 14)
            pygame.draw.circle(surf, C_SPELL, pos, 10)
        elif self.kind == "fireball":
            pygame.draw.circle(surf, C_SPELL, pos, 8)
            pygame.draw.circle(surf, C_GOLD, pos, 5)
        elif self.kind == "arrow":
            pygame.draw.circle(surf, C_WHITE, pos, 3)
        else:
            pygame.draw.circle(surf, C_BLACK, pos, 5)
            pygame.draw.circle(surf, C_GOLD, pos, 3)

# ── Battlefield Runes ───────────────────────────────────────────────────────
class Rune:
    def __init__(self, x, y, kind):
        self.x, self.y = x, y
        self.kind = kind
        self.radius = 18
        self.alive = True
        self.time = 0

    def update(self, dt, all_units, particles, floating_texts):
        if not self.alive: return
        self.time += dt
        if random.random() < 0.4:
            col = C_RAGE if self.kind == "rage" else C_HEAL
            particles.append(Particle(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), 0, -20, col, 3, 0.4))
        for u in all_units:
            if not u.alive: continue
            if math.hypot(u.x - self.x, u.y - self.y) <= self.radius + u.radius:
                self.alive = False
                col = C_RAGE if self.kind == "rage" else C_HEAL
                msg = "⚡ RAGE +50%!" if self.kind == "rage" else "💖 HEAL +350!"
                floating_texts.append(FloatingText(self.x, self.y - 15, msg, col, True, 1.2))
                for ally in all_units:
                    if ally.alive and ally.team == u.team and math.hypot(ally.x - self.x, ally.y - self.y) <= 90:
                        if self.kind == "rage": ally.rage_timer = max(ally.rage_timer, 6.0)
                        else: ally.hp = min(ally.max_hp, ally.hp + 350); floating_texts.append(FloatingText(ally.x, ally.y - 20, "+350", C_HEAL, False))
                for _ in range(25):
                    ang = random.uniform(0, math.pi*2); spd = random.uniform(40, 120)
                    particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, col, 5, 0.6))
                break

    def draw(self, surf, ox=0, oy=0):
        if not self.alive: return
        pos = (int(self.x + ox), int(self.y + oy))
        col = C_RAGE if self.kind == "rage" else C_HEAL
        r = int(self.radius + 3 * math.sin(self.time * 6))
        pygame.draw.circle(surf, col, pos, r, 2)
        pygame.draw.circle(surf, C_WHITE if int(self.time*4)%2==0 else col, pos, int(self.radius*0.6))

# ── Base Entity (With Stats & Perks) ────────────────────────────────────────
class Entity:
    def __init__(self, x, y, hp, team):
        self.x, self.y = x, y
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.team = team
        self.alive = True
        self.freeze_timer = 0.0
        self.rage_timer = 0.0
        self.invuln_timer = 0.0
        
        # Post-Game MVP Analytics
        self.damage_dealt = 0
        self.kills = 0
        self.kind_name = "Unit"

    @property
    def color(self):
        if self.invuln_timer > 0: return C_INVULN
        if self.freeze_timer > 0: return C_FREEZE
        return (59, 130, 246) if self.team == "player" else (239, 68, 68)

    @property
    def dark_color(self):
        return (29, 78, 216) if self.team == "player" else (185, 28, 28)

    def take_damage(self, amt, floating_texts=None, particles=None, source_entity=None):
        if not self.alive or self.invuln_timer > 0: return
        self.hp = max(0.0, self.hp - amt)
        if source_entity:
            source_entity.damage_dealt += int(amt)
            # Vampiric Aura Perk check
            if hasattr(source_entity, "has_vampiric") and source_entity.has_vampiric:
                source_entity.hp = min(source_entity.max_hp, source_entity.hp + amt * 0.25)
                
        if self.hp <= 0:
            self.alive = False
            if source_entity: source_entity.kills += 1
            if particles:
                for _ in range(14):
                    ang = random.uniform(0, math.pi * 2); spd = random.uniform(20, 80)
                    particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, self.color, random.uniform(3, 7), 0.4))
            # Explosive Demise Perk check
            if hasattr(self, "has_explosive") and self.has_explosive and particles:
                for _ in range(20):
                    ang = random.uniform(0, math.pi * 2); spd = random.uniform(30, 100)
                    particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, C_SPELL, 5, 0.4))
        if floating_texts:
            col = C_GOLD if amt > 120 else C_WHITE
            floating_texts.append(FloatingText(self.x + random.randint(-10,10), self.y - 20, f"-{int(amt)}", col, amt > 120))
        if particles and random.random() < 0.7:
            particles.append(Particle(self.x, self.y, random.uniform(-30,30), random.uniform(-30,30), C_GOLD, 4, 0.2))

    def draw_hp_bar(self, surf, bx, by, bw=40, bh=5):
        pygame.draw.rect(surf, C_BLACK, (bx, by, bw, bh))
        frac = max(0, self.hp / self.max_hp) if self.max_hp > 0 else 0
        filled = int(bw * frac)
        if filled > 0:
            col = (34, 197, 94) if frac > 0.6 else ((234, 179, 8) if frac > 0.3 else C_RED)
            pygame.draw.rect(surf, col, (bx, by, filled, bh))
        pygame.draw.rect(surf, C_WHITE, (bx, by, bw, bh), 1)

# ── Towers & Buildings ──────────────────────────────────────────────────────
class Tower(Entity):
    def __init__(self, x, y, kind, team):
        c = CONFIG[kind]
        super().__init__(x, y, c["hp"], team)
        self.kind = kind
        self.kind_name = kind
        self.damage = c["damage"]
        self.attack_range = c["range"]
        self.attack_cooldown = c["cooldown"]
        self.width, self.height = c["w"], c["h"]
        self.attack_timer = 0.0
        self.has_twin = False

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)

    def update(self, dt, enemies, projectiles, particles=None):
        if not self.alive: return
        if self.invuln_timer > 0: self.invuln_timer -= dt
        if self.freeze_timer > 0: self.freeze_timer -= dt; return
        if self.rage_timer > 0:   self.rage_timer -= dt
        
        cd_mult = 0.65 if self.rage_timer > 0 else 1.0
        self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attack_timer == 0.0:
            target = min((e for e in enemies if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= self.attack_range),
                         key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)
            if target:
                kind = "cannon" if self.kind == "KingTower" else "arrow"
                spd = 450 if kind == "cannon" else 500
                projectiles.append(Projectile(self.x, self.y, target.x, target.y, spd, self.damage, 0, self.team, kind, target, self))
                if self.has_twin and self.kind == "PrincessTower":
                    projectiles.append(Projectile(self.x+10, self.y, target.x, target.y, spd*1.05, self.damage, 0, self.team, kind, target, self))
                self.attack_timer = self.attack_cooldown * cd_mult

    def draw(self, surf, ox=0, oy=0):
        if not self.alive: return
        r = self.rect.move(ox, oy)
        pygame.draw.rect(surf, self.dark_color, r.inflate(4, 4), border_radius=6)
        pygame.draw.rect(surf, self.color, r, border_radius=6)
        if self.invuln_timer > 0 or self.rage_timer > 0:
            pygame.draw.rect(surf, C_INVULN if self.invuln_timer>0 else C_RAGE, r.inflate(8, 8), 2, border_radius=8)
        lbl = FONT_MED.render("K" if self.kind == "KingTower" else "P", True, C_WHITE)
        surf.blit(lbl, lbl.get_rect(center=r.center))
        self.draw_hp_bar(surf, r.left, r.top - 10, r.width, 6)

class KingTower(Tower):
    def __init__(self, x, y, team): super().__init__(x, y, "KingTower", team)
class PrincessTower(Tower):
    def __init__(self, x, y, team): super().__init__(x, y, "PrincessTower", team)

class CannonBuilding(Entity):
    def __init__(self, x, y, team):
        c = CONFIG["Cannon"]
        super().__init__(x, y, c["hp"], team)
        self.kind = "Cannon"
        self.kind_name = "Cannon"
        self.damage = c["damage"]
        self.attack_range = c["range"]
        self.attack_cooldown = c["cooldown"]
        self.radius = c["radius"]
        self.lifetime = c["lifetime"]
        self.attack_timer = 0.0

    @property
    def rect(self): return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self, dt, enemies, projectiles, particles=None):
        if not self.alive: return
        self.hp -= self.max_hp * (dt / self.lifetime)
        if self.hp <= 0: self.alive = False; return
        if self.invuln_timer > 0: self.invuln_timer -= dt
        if self.freeze_timer > 0: self.freeze_timer -= dt; return
        if self.rage_timer > 0:   self.rage_timer -= dt
        
        cd_mult = 0.65 if self.rage_timer > 0 else 1.0
        self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attack_timer == 0.0:
            target = min((e for e in enemies if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= self.attack_range),
                         key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)
            if target:
                projectiles.append(Projectile(self.x, self.y, target.x, target.y, 500, self.damage, 0, self.team, "cannon", target, self))
                self.attack_timer = self.attack_cooldown * cd_mult

    def draw(self, surf, ox=0, oy=0):
        if not self.alive: return
        pos = (int(self.x + ox), int(self.y + oy))
        pygame.draw.circle(surf, (71, 85, 105), pos, self.radius + 2)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        if self.rage_timer > 0: pygame.draw.circle(surf, C_RAGE, pos, self.radius + 4, 2)
        lbl = FONT_SMALL.render("CAN", True, C_WHITE)
        surf.blit(lbl, lbl.get_rect(center=pos))
        self.draw_hp_bar(surf, pos[0] - 18, pos[1] - self.radius - 10, 36, 5)

# ── Units & Legendaries ─────────────────────────────────────────────────────
class Unit(Entity):
    AGGRO_RANGE = 220.0
    def __init__(self, x, y, kind, team):
        c = CONFIG[kind]
        super().__init__(x, y, c["hp"], team)
        self.kind = kind
        self.kind_name = kind
        self.damage = c["damage"]
        self.speed = c["speed"]
        self.attack_range = c["range"]
        self.attack_cooldown = c["cooldown"]
        self.radius = c["radius"]
        self.splash_radius = c.get("splash", 0)
        self.whirlwind_radius = c.get("whirlwind", 0)
        self.charge_mult = c.get("charge_mult", 1.0)
        self.is_air = c.get("is_air", False)
        
        self.attack_timer = 0.0
        self.target = None
        self.lane = 0 if x <= SCREEN_W // 2 else 1
        self.waypoints = self._build_waypoints(team)
        self.wp_idx = 0
        
        # Prince Charge
        self.move_timer = 0.0
        self.is_charging = False
        # Inferno Dragon Laser
        self.laser_time = 0.0
        self.laser_target = None
        # Mega Knight Spawning Leap
        self.is_spawning = (kind == "MegaKnight")
        self.spawn_timer = 0.6 if self.is_spawning else 0.0

    def _build_waypoints(self, team):
        bx = BRIDGE_LEFT_X if self.lane == 0 else BRIDGE_RIGHT_X
        return [[bx, RIVER_BOTTOM - 15], [bx, RIVER_TOP + 15]] if team == "player" else [[bx, RIVER_TOP + 15], [bx, RIVER_BOTTOM - 15]]

    def _find_target(self, enemy_units, enemy_towers):
        u = min((e for e in enemy_units if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= self.AGGRO_RANGE),
                key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)
        if u: return u
        return min((e for e in enemy_towers if e.alive), key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)

    def update(self, dt, enemy_units, enemy_towers, all_units, all_towers, projectiles, floating_texts, particles):
        if not self.alive: return
        if self.invuln_timer > 0: self.invuln_timer -= dt
        
        # Mega Knight Leap Landing
        if self.is_spawning:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.is_spawning = False
                floating_texts.append(FloatingText(self.x, self.y - 20, "💥 MEGA LANDING!", C_GOLD, True, 1.2))
                for e in list(enemy_units) + list(enemy_towers):
                    if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= 85:
                        e.take_damage(180, floating_texts, particles, self)
                        e.freeze_timer = max(e.freeze_timer, 1.5)
                for _ in range(30):
                    ang = random.uniform(0, math.pi*2); spd = random.uniform(40, 130)
                    particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, C_GOLD, 6, 0.5))
            return

        if self.freeze_timer > 0:
            self.freeze_timer -= dt; self.is_charging = False; self.move_timer = 0.0; self.laser_time = 0.0
            return
        if self.rage_timer > 0: self.rage_timer -= dt
        
        spd_mult = (1.5 if self.rage_timer > 0 else 1.0) * (1.6 if self.is_charging else 1.0)
        cd_mult  = 0.65 if self.rage_timer > 0 else 1.0

        if self.target and not self.target.alive: self.target = None; self.laser_time = 0.0; self.laser_target = None
        self.target = self._find_target(enemy_units, enemy_towers)
        self.attack_timer = max(0.0, self.attack_timer - dt)

        moved = False
        if self.target:
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist <= self.attack_range:
                if self.kind == "InfDragon":
                    if self.laser_target != self.target: self.laser_target = self.target; self.laser_time = 0.0
                    self.laser_time += dt
                if self.attack_timer == 0.0:
                    self._perform_attack(projectiles, floating_texts, particles, enemy_units, enemy_towers)
                    self.attack_timer = self.attack_cooldown * cd_mult
                    self.is_charging = False; self.move_timer = 0.0
            else:
                moved = True; self.laser_time = 0.0; self.laser_target = None
                if self.is_air:
                    self._move_toward(self.target.x, self.target.y, dt * spd_mult)
                elif self.wp_idx < len(self.waypoints):
                    wx, wy = self.waypoints[self.wp_idx]
                    if math.hypot(wx - self.x, wy - self.y) < 25: self.wp_idx += 1
                    else: self._move_toward(wx, wy, dt * spd_mult)
                else:
                    self._move_toward(self.target.x, self.target.y, dt * spd_mult)

        if moved and self.kind == "Prince":
            self.move_timer += dt
            if self.move_timer >= 0.8 and not self.is_charging:
                self.is_charging = True; floating_texts.append(FloatingText(self.x, self.y - 15, "⚡ CHARGE!", C_GOLD, True))
            if self.is_charging and random.random() < 0.6:
                particles.append(Particle(self.x, self.y, random.uniform(-20,20), random.uniform(-20,20), C_GOLD, 5, 0.3))
        elif not moved:
            self.is_charging = False; self.move_timer = 0.0

        if not self.is_air and all_towers: self._avoid_towers(all_towers, dt * spd_mult)
        self._separate(all_units)

    def _perform_attack(self, projectiles, floating_texts, particles, enemy_units, enemy_towers):
        if not self.target or not self.target.alive: return
        dmg = int(self.damage * (self.charge_mult if self.is_charging else 1.0))
        
        if self.kind == "InfDragon":
            # Escalating laser damage
            mult = 1.0 + min(8.0, self.laser_time * 3.0)
            dmg = int(self.damage * mult)
            self.target.take_damage(dmg, floating_texts, particles, self)
            particles.append(Particle(self.target.x, self.target.y, random.uniform(-20,20), random.uniform(-20,20), C_SPELL, 4, 0.2))
        elif self.kind == "Archer":
            projectiles.append(Projectile(self.x, self.y, self.target.x, self.target.y, 480, dmg, 0, self.team, "arrow", self.target, self))
            if hasattr(self, "has_twin") and self.has_twin:
                projectiles.append(Projectile(self.x+8, self.y, self.target.x, self.target.y, 500, dmg, 0, self.team, "arrow", self.target, self))
        elif self.kind == "Wizard":
            projectiles.append(Projectile(self.x, self.y, self.target.x, self.target.y, 420, dmg, self.splash_radius, self.team, "fireball", self.target, self))
        elif self.kind in ("Valkyrie", "MegaKnight"):
            rad = self.whirlwind_radius if self.kind == "Valkyrie" else self.splash_radius
            for e in list(enemy_units) + list(enemy_towers):
                if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= rad:
                    e.take_damage(dmg, floating_texts, particles, self)
            for _ in range(20):
                ang = random.uniform(0, math.pi * 2)
                particles.append(Particle(self.x, self.y, math.cos(ang)*110, math.sin(ang)*110, C_GOLD, 4, 0.25))
        else:
            self.target.take_damage(dmg, floating_texts, particles, self)
            if self.is_charging:
                for _ in range(15):
                    ang = random.uniform(0, math.pi * 2)
                    particles.append(Particle(self.target.x, self.target.y, math.cos(ang)*140, math.sin(ang)*140, C_GOLD, 6, 0.4))

    def _move_toward(self, tx, ty, dt_speed):
        dx, dy = tx - self.x, ty - self.y; d = math.hypot(dx, dy)
        if d < 0.5: return
        self.x += (dx / d) * self.speed * dt_speed; self.y += (dy / d) * self.speed * dt_speed

    def _separate(self, all_units):
        for o in all_units:
            if o is self or not o.alive or (self.is_air != o.is_air): continue
            dx, dy = self.x - o.x, self.y - o.y; d = math.hypot(dx, dy); mn = self.radius + o.radius
            if 0.1 < d < mn: ov = (mn - d) / 2; self.x += (dx / d) * ov; self.y += (dy / d) * ov

    def _avoid_towers(self, towers, dt_speed):
        adist, aspeed = self.radius + 40, self.speed * 1.5
        for t in towers:
            if not t.alive or t is self.target: continue
            r = t.rect; cx = max(r.left, min(self.x, r.right)); cy = max(r.top, min(self.y, r.bottom))
            dx, dy = self.x - cx, self.y - cy; d = math.hypot(dx, dy)
            if 0.1 < d < adist: str_ = (adist - d) / adist; self.x += (dx / d) * aspeed * str_ * dt_speed; self.y += (dy / d) * aspeed * str_ * dt_speed

    def draw(self, surf, ox=0, oy=0):
        if not self.alive: return
        pos = (int(self.x + ox), int(self.y + oy))
        if self.is_spawning:
            pygame.draw.circle(surf, C_GOLD, pos, self.radius * 2, 2)
            lbl = FONT_MED.render("LEAPING...", True, C_GOLD)
            surf.blit(lbl, lbl.get_rect(center=pos))
            return
            
        if self.kind == "InfDragon" and self.laser_target and self.laser_target.alive and self.laser_time > 0:
            tp = (int(self.laser_target.x + ox), int(self.laser_target.y + oy))
            w = min(8, 2 + int(self.laser_time * 2))
            col = C_RED if self.laser_time > 1.5 else C_SPELL
            pygame.draw.line(surf, col, pos, tp, w)

        if self.is_charging: pygame.draw.circle(surf, C_GOLD, pos, self.radius + 4)
        pygame.draw.circle(surf, self.dark_color, (pos[0]+2, pos[1]+2), self.radius)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        if self.rage_timer > 0: pygame.draw.circle(surf, C_RAGE, pos, self.radius + 3, 2)
        pygame.draw.circle(surf, C_WHITE, pos, self.radius, 2)
        
        lbl = FONT_SMALL.render(self.kind[:2].upper(), True, C_WHITE)
        surf.blit(lbl, lbl.get_rect(center=pos))
        self.draw_hp_bar(surf, pos[0] - self.radius, pos[1] - self.radius - 10, self.radius*2, 4)

class Knight(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Knight", t)
class Archer(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Archer", t)
class Giant(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Giant", t)
    def _find_target(self, eu, et): return min((e for e in et if e.alive), key=lambda e: math.hypot(e.x - self.x, e.y - self.y), default=None)
class Wizard(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Wizard", t)
class Skeleton(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Skeleton", t)
class Valkyrie(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Valkyrie", t)
class Prince(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "Prince", t)
class InfernoDragon(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "InfDragon", t)
class MegaKnight(Unit):
    def __init__(self, x, y, t): super().__init__(x, y, "MegaKnight", t)

# ── Hero Commanders ─────────────────────────────────────────────────────────
class HeroCommander:
    HEROES = ["PALADIN", "ARCHMAGE", "MECHA"]
    def __init__(self, kind, team):
        self.kind = kind
        self.team = team
        self.cd_timer = 0.0
        self.max_cd = 25.0 if kind == "PALADIN" else (30.0 if kind == "ARCHMAGE" else 28.0)

    def update(self, dt):
        if self.cd_timer > 0: self.cd_timer = max(0.0, self.cd_timer - dt)

    def activate_ultimate(self, game):
        if self.cd_timer > 0 or game.state != "PLAYING": return False
        self.cd_timer = self.max_cd
        game.show_flash(f"👑 HERO ULTIMATE: {self.kind}!")
        game.screen_shake = 0.4
        
        my_units = game.player_units if self.team == "player" else game.ai_units
        my_towers= game.player_towers if self.team == "player" else game.ai_towers
        en_units = game.ai_units if self.team == "player" else game.player_units
        en_towers= game.ai_towers if self.team == "player" else game.player_towers
        
        if self.kind == "PALADIN":
            for u in my_units + my_towers:
                u.invuln_timer = max(u.invuln_timer, 3.0)
                u.hp = min(u.max_hp, u.hp + 400)
                game.floating_texts.append(FloatingText(u.x, u.y - 25, "💖 +400 INVULN!", C_INVULN, True))
                for _ in range(15):
                    ang = random.uniform(0, math.pi*2); spd = random.uniform(30, 90)
                    game.particles.append(Particle(u.x, u.y, math.cos(ang)*spd, math.sin(ang)*spd, C_INVULN, 5, 0.5))
        elif self.kind == "ARCHMAGE":
            for _ in range(8):
                tx = random.randint(40, SCREEN_W - 40)
                ty = random.randint(20, RIVER_TOP) if self.team == "player" else random.randint(RIVER_BOTTOM, SCREEN_H - 120)
                game.projectiles.append(Projectile(tx, ty - 350, tx, ty, 650, 180, 55, self.team, "meteor"))
        elif self.kind == "MECHA":
            for t in en_towers:
                t.freeze_timer = max(t.freeze_timer, 4.0)
                game.floating_texts.append(FloatingText(t.x, t.y - 20, "⚡ EMP STUN!", C_CYAN, True))
            for u in my_units:
                u.rage_timer = max(u.rage_timer, 5.0)
                game.floating_texts.append(FloatingText(u.x, u.y - 20, "⚡ OVERDRIVE!", C_RAGE, True))
        return True

# ── Roguelike Perk Manager ──────────────────────────────────────────────────
class PerkManager:
    PERKS = [
        ("💥 Explosive Demise", "EXPLOSIVE"),
        ("🧛 Vampiric Aura",    "VAMPIRIC"),
        ("🏹 Twin Arrows",      "TWIN_ARROWS"),
        ("🛡️ Titan Skin",       "TITAN_SKIN"),
        ("⚡ Elixir Overflow",  "OVERFLOW")
    ]
    def __init__(self):
        self.perks_acquired = set()
        self.elixir_counter = 0.0
        self.perks_available = 0

    def add_spent_elixir(self, amt):
        self.elixir_counter += amt
        if self.elixir_counter >= 20.0:
            self.elixir_counter -= 20.0
            self.perks_available += 1

    def claim_perk(self, game):
        if self.perks_available <= 0: return False
        avail = [p for p in self.PERKS if p[1] not in self.perks_acquired]
        if not avail: return False
        
        name, code = random.choice(avail)
        self.perks_acquired.add(code)
        self.perks_available -= 1
        game.show_flash(f"🌟 PERK UNLOCKED: {name}!")
        
        # Apply immediate buffs
        if code == "TITAN_SKIN":
            for u in game.player_units:
                if u.kind in ("Giant", "Knight", "MegaKnight", "Prince"):
                    u.max_hp *= 1.4; u.hp *= 1.4
        elif code == "TWIN_ARROWS":
            for t in game.player_towers: t.has_twin = True
            for u in game.player_units:
                if u.kind == "Archer": u.has_twin = True
        return True

    def apply_to_unit(self, u):
        if "EXPLOSIVE" in self.perks_acquired: u.has_explosive = True
        if "VAMPIRIC" in self.perks_acquired:  u.has_vampiric = True
        if "TWIN_ARROWS" in self.perks_acquired and u.kind == "Archer": u.has_twin = True
        if "TITAN_SKIN" in self.perks_acquired and u.kind in ("Giant", "Knight", "MegaKnight", "Prince"):
            u.max_hp *= 1.4; u.hp *= 1.4

# ── AI Controller ───────────────────────────────────────────────────────────
class AIController:
    def __init__(self):
        self.interval = 1.8; self.timer = self.interval
        self.hero = HeroCommander("ARCHMAGE", "ai")

    def update(self, dt, elixir, spawn_cb, spell_cb, ai_towers, player_units, ai_units, mode, game):
        self.timer -= dt; self.hero.update(dt)
        if self.hero.cd_timer == 0.0 and len(player_units) >= 3 and random.random() < 0.4:
            self.hero.activate_ultimate(game)

        if self.timer > 0: return elixir
        self.timer = self.interval

        if elixir >= 4 and len(player_units) >= 3:
            for pu in player_units:
                cluster = [u for u in player_units if math.hypot(u.x - pu.x, u.y - pu.y) <= 75]
                if len(cluster) >= 3 and random.random() < 0.7: spell_cb("Fireball", pu.x, pu.y, "ai"); return elixir - 4
                elif len(cluster) >= 2 and elixir >= 3 and random.random() < 0.4: spell_cb("Freeze", pu.x, pu.y, "ai"); return elixir - 3
        
        invaders = [u for u in player_units if u.y < RIVER_BOTTOM + 50]
        if invaders:
            invaders.sort(key=lambda u: u.y); tu = invaders[0]; lane = 0 if tu.x <= SCREEN_W // 2 else 1
            bx = BRIDGE_LEFT_X if lane == 0 else BRIDGE_RIGHT_X
            if tu.kind in ("Giant", "Prince", "MegaKnight") and elixir >= 4:
                if random.random() < 0.5: spawn_cb("InfDragon", bx, AI_HALF_BOTTOM - 50, "ai", False)
                else: spawn_cb("Cannon", bx, AI_HALF_BOTTOM - 60, "ai", False)
                return elixir - 4
            elif tu.kind in ("Skeleton", "Archer") and elixir >= 4:
                spawn_cb("Valkyrie", bx, AI_HALF_BOTTOM - 50, "ai", False); return elixir - 4

        cards = [("Knight",3,False), ("Archer",3,False), ("Giant",5,False), ("Wizard",4,False),
                 ("Skeleton",3,True), ("Valkyrie",4,False), ("Prince",5,False), ("Cannon",3,False),
                 ("InfDragon",4,False), ("MegaKnight",6,False)]
        aff = [c for c in cards if elixir >= c[1]]
        if not aff or random.random() > 0.65: return elixir
        chosen = random.choice(aff); sx, sy = self._random_spawn(ai_towers)
        spawn_cb(chosen[0], sx, sy, "ai", chosen[2]); return elixir - chosen[1]

    def _random_spawn(self, ai_towers):
        for _ in range(20):
            x, y = random.randint(40, SCREEN_W - 40), random.randint(AI_HALF_TOP + 20, AI_HALF_BOTTOM - 30)
            if all(not t.alive or not t.rect.inflate(20,20).collidepoint(x, y) for t in ai_towers): return x, y
        return SCREEN_W // 2, (AI_HALF_TOP + AI_HALF_BOTTOM) // 2

# ── Game State ──────────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.CARDS = [
            ("Knight",    Knight,         3, False, False),
            ("Archer",    Archer,         3, False, False),
            ("Giant",     Giant,          5, False, False),
            ("Wizard",    Wizard,         4, False, False),
            ("Skeleton",  Skeleton,       3, False, True ),
            ("Valkyrie",  Valkyrie,       4, False, False),
            ("Prince",    Prince,         5, False, False),
            ("Cannon",    CannonBuilding, 3, False, False),
            ("InfDragon", InfernoDragon,  4, False, False),
            ("MegaKnight",MegaKnight,     6, False, False),
            ("Fireball",  None,           4, True,  False),
            ("Freeze",    None,           3, True,  False),
        ]
        self.MODES = ["CLASSIC", "3X_INFINITE", "SURVIVAL"]
        self.mode_idx = 0; self.theme_idx = 0; self.best_wave = 1
        self.deck_mode = "MASTER_12" # or "PRO_CYCLE"
        self.hero_idx = 0
        self.reset()

    @property
    def game_mode(self): return self.MODES[self.mode_idx]
    @property
    def theme(self): return THEMES[self.theme_idx]

    def reset(self):
        self.state = "PLAYING"
        self.player_elixir, self.ai_elixir = ELIXIR_START, ELIXIR_START
        self.elapsed_time = 0.0; self.selected_card = 0
        self.flash_msg, self.flash_timer = None, 0.0
        self.player_won, self.is_double_elixir = False, False
        self.screen_shake = 0.0; self.lightning_timer = 15.0; self.lightning_alpha = 0
        
        self.wave_number = 1; self.wave_timer = 15.0; self.rune_timer = 20.0
        
        W, H = SCREEN_W, SCREEN_H
        self.player_king   = KingTower(W//2, H-60, "player")
        self.player_tower_l = PrincessTower(W//4, H-160, "player")
        self.player_tower_r = PrincessTower(3*W//4, H-160, "player")
        self.ai_king       = KingTower(W//2, 60, "ai")
        self.ai_tower_l     = PrincessTower(W//4, 160, "ai")
        self.ai_tower_r     = PrincessTower(3*W//4, 160, "ai")
        
        if self.game_mode == "SURVIVAL":
            self.ai_king.hp = self.ai_king.max_hp = 999999
            self.ai_tower_l.hp = self.ai_tower_l.max_hp = 999999
            self.ai_tower_r.hp = self.ai_tower_r.max_hp = 999999
            
        self.player_towers = [self.player_king, self.player_tower_l, self.player_tower_r]
        self.ai_towers     = [self.ai_king, self.ai_tower_l, self.ai_tower_r]
        self.player_units, self.ai_units = [], []
        self.projectiles, self.particles, self.floating_texts, self.runes = [], [], [], []
        self.ai_ctrl = AIController()
        
        # Hero & Perks
        self.hero = HeroCommander(HeroCommander.HEROES[self.hero_idx], "player")
        self.perk_mgr = PerkManager()
        
        # Pro Deck Cycling Mode Setup
        self.deck_queue = list(range(len(self.CARDS)))
        random.shuffle(self.deck_queue)
        self.hand_indices = [self.deck_queue.pop(0) for _ in range(4)]
        self.next_index = self.deck_queue.pop(0)

    def cycle_hero(self):
        self.hero_idx = (self.hero_idx + 1) % len(HeroCommander.HEROES)
        self.hero = HeroCommander(HeroCommander.HEROES[self.hero_idx], "player")
        self.show_flash(f"Hero Commander: {self.hero.kind}")

    def toggle_deck_mode(self):
        self.deck_mode = "PRO_CYCLE" if self.deck_mode == "MASTER_12" else "MASTER_12"
        self.selected_card = 0
        self.show_flash(f"Deck Mode: {self.deck_mode}")

    def cycle_mode(self):
        self.mode_idx = (self.mode_idx + 1) % len(self.MODES); self.reset()
        self.show_flash(f"Mode: {self.game_mode}")

    def cycle_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(THEMES); self.show_flash(f"Theme: {self.theme['name']}")

    def show_flash(self, msg): self.flash_msg, self.flash_timer = msg, 1.2

    def spawn_unit(self, kind_or_cls, x, y, team, is_swarm=False):
        cls = kind_or_cls if isinstance(kind_or_cls, type) else eval(kind_or_cls if kind_or_cls != "Cannon" else "CannonBuilding")
        target_list = self.player_units if team == "player" else self.ai_units
        if team == "player" and cls == CannonBuilding:
            u = cls(x, y, team); self.perk_mgr.apply_to_unit(u); self.player_towers.append(u)
        elif team == "ai" and cls == CannonBuilding: self.ai_towers.append(cls(x, y, team))
        elif is_swarm:
            for ox, oy in [(-14,-14), (14,-14), (-14,14), (14,14)]:
                u = cls(x+ox, y+oy, team)
                if team == "player": self.perk_mgr.apply_to_unit(u)
                target_list.append(u)
                self.particles.append(Particle(x+ox, y+oy, 0, 0, C_CYAN if team=="player" else C_RED, 12, 0.3))
        else:
            u = cls(x, y, team)
            if team == "player": self.perk_mgr.apply_to_unit(u)
            target_list.append(u)
            self.particles.append(Particle(x, y, 0, 0, C_CYAN if team=="player" else C_RED, 16, 0.35))

    def cast_spell(self, name, x, y, team):
        if name == "Fireball":
            c = CONFIG["Fireball"]
            self.projectiles.append(Projectile(x, y - 350, x, y, 650, c["damage"], c["radius"], team, "meteor"))
            self.screen_shake = 0.25
        elif name == "Freeze":
            c = CONFIG["Freeze"]
            all_targets = (self.ai_units + self.ai_towers) if team == "player" else (self.player_units + self.player_towers)
            for t in all_targets:
                if t.alive and math.hypot(t.x - x, t.y - y) <= c["radius"]:
                    t.freeze_timer = max(t.freeze_timer, c["duration"])
                    self.floating_texts.append(FloatingText(t.x, t.y - 20, "❄️ FREEZE!", C_FREEZE))
            for _ in range(35):
                ang = random.uniform(0, math.pi * 2); spd = random.uniform(20, 100)
                self.particles.append(Particle(x, y, math.cos(ang)*spd, math.sin(ang)*spd, C_FREEZE, random.uniform(4, 8), 0.6))

    def try_deploy(self, mx, my):
        if my >= SCREEN_H - 100: return
        card_idx = self.selected_card if self.deck_mode == "MASTER_12" else self.hand_indices[self.selected_card]
        name, cls, cost, is_spell, is_swarm = self.CARDS[card_idx]
        if self.player_elixir < cost: self.show_flash("Not enough Elixir!"); return
        
        if is_spell:
            self.player_elixir -= cost; self.perk_mgr.add_spent_elixir(cost); self.cast_spell(name, mx, my, "player")
        else:
            if my <= RIVER_BOTTOM: self.show_flash("Deploy on your side!"); return
            for t in self.player_towers + self.ai_towers:
                if t.alive and t.rect.inflate(20,20).collidepoint(mx, my): self.show_flash("Cannot deploy on tower!"); return
            self.player_elixir -= cost; self.perk_mgr.add_spent_elixir(cost); self.spawn_unit(cls, mx, my, "player", is_swarm)
            
        if self.deck_mode == "PRO_CYCLE":
            played_idx = self.hand_indices[self.selected_card]
            self.hand_indices[self.selected_card] = self.next_index
            self.next_index = self.deck_queue.pop(0)
            self.deck_queue.append(played_idx)

    def update(self, dt):
        if self.state != "PLAYING": return
        self.elapsed_time += dt; self.hero.update(dt)
        
        mult = 3.0 if self.game_mode == "3X_INFINITE" else (2.0 if self.is_double_elixir else 1.0)
        self.player_elixir = min(ELIXIR_MAX, self.player_elixir + ELIXIR_REGEN_RATE * mult * dt)
        self.ai_elixir = min(ELIXIR_MAX, self.ai_elixir + ELIXIR_REGEN_RATE * mult * dt)

        if self.game_mode == "CLASSIC" and not self.is_double_elixir and self.elapsed_time >= 60.0:
            self.is_double_elixir = True; self.screen_shake = 0.4
            self.floating_texts.append(FloatingText(SCREEN_W//2, SCREEN_H//2, "⚡ 2X ELIXIR! ⚡", C_GOLD, True, 1.5))

        # Night lightning effect in double elixir
        if self.is_double_elixir or self.game_mode == "3X_INFINITE":
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_timer = random.uniform(8.0, 18.0)
                self.lightning_alpha = 180
                self.screen_shake = 0.15
        if self.lightning_alpha > 0: self.lightning_alpha = max(0, self.lightning_alpha - int(400 * dt))

        self.rune_timer -= dt
        if self.rune_timer <= 0 and len(self.runes) < 2:
            self.rune_timer = 25.0; rx = random.choice([BRIDGE_LEFT_X, BRIDGE_RIGHT_X, SCREEN_W//2])
            self.runes.append(Rune(rx, RIVER_MID + random.randint(-15, 15), random.choice(["rage", "heal"])))

        if self.game_mode == "SURVIVAL":
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.wave_timer = 15.0; self.wave_number += 1; self.best_wave = max(self.best_wave, self.wave_number)
                self.floating_texts.append(FloatingText(SCREEN_W//2, RIVER_TOP + 40, f"🧟 WAVE {self.wave_number}!", C_RED, True, 1.5))
                cnt = min(6, 1 + self.wave_number // 2)
                for _ in range(cnt):
                    kind = random.choice(["Giant", "Prince", "Valkyrie", "Wizard", "Skeleton", "InfDragon", "MegaKnight"])
                    bx = random.choice([BRIDGE_LEFT_X, BRIDGE_RIGHT_X])
                    self.spawn_unit(kind, bx + random.randint(-20,20), AI_HALF_BOTTOM - random.randint(20, 60), "ai", kind=="Skeleton")

        if self.screen_shake > 0: self.screen_shake = max(0.0, self.screen_shake - dt)
        if self.flash_msg:
            self.flash_timer -= dt
            if self.flash_timer <= 0: self.flash_msg = None

        if self.game_mode != "SURVIVAL":
            self.ai_elixir = self.ai_ctrl.update(dt, self.ai_elixir,
                lambda cls, x, y, team, swarm: self.spawn_unit(cls, x, y, team, swarm),
                lambda spell, x, y, team: self.cast_spell(spell, x, y, team),
                self.ai_towers, self.player_units, self.ai_units, self.game_mode, self)
            self.ai_elixir = min(ELIXIR_MAX, self.ai_elixir)

        all_ai = self.ai_units + self.ai_towers; all_pl = self.player_units + self.player_towers
        for p in self.projectiles: p.update(dt, all_ai if p.team=="player" else all_pl, self.particles, self.floating_texts)
        self.projectiles = [p for p in self.projectiles if p.alive]

        for t in self.player_towers: t.update(dt, all_ai, self.projectiles, self.particles)
        for t in self.ai_towers:     t.update(dt, all_pl, self.projectiles, self.particles)

        live_ai_t = [t for t in self.ai_towers if t.alive]; live_pl_t = [t for t in self.player_towers if t.alive]
        live_all_t= live_ai_t + live_pl_t

        pu, au = list(self.player_units), list(self.ai_units)
        for u in pu: u.update(dt, au, live_ai_t, pu, live_all_t, self.projectiles, self.floating_texts, self.particles)
        for u in au: u.update(dt, pu, live_pl_t, au, live_all_t, self.projectiles, self.floating_texts, self.particles)

        for r in self.runes: r.update(dt, pu + au, self.particles, self.floating_texts)
        self.runes = [r for r in self.runes if r.alive]

        self.particles = [pt for pt in self.particles if pt.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]
        
        # Elixir Overflow perk check on unit/building death
        old_ai_count = len(self.ai_units) + len(self.ai_towers)
        self.player_units = [u for u in self.player_units if u.alive]
        self.ai_units = [u for u in self.ai_units if u.alive]
        self.player_towers = [t for t in self.player_towers if t.alive]
        self.ai_towers = [t for t in self.ai_towers if t.alive]
        new_ai_count = len(self.ai_units) + len(self.ai_towers)
        if "OVERFLOW" in self.perk_mgr.perks_acquired and old_ai_count > new_ai_count:
            self.player_elixir = min(ELIXIR_MAX, self.player_elixir + 1.0)
            self.floating_texts.append(FloatingText(SCREEN_W//2, SCREEN_H - 120, "+1 ELIXIR OVERFLOW!", C_PURPLE))

        if not self.ai_king.alive and self.game_mode != "SURVIVAL":
            self.player_won = True; self.state = "GAME_OVER"
        elif not self.player_king.alive:
            self.player_won = False; self.state = "GAME_OVER"

    def draw(self, surf):
        ox = random.randint(-4, 4) if self.screen_shake > 0 else 0
        oy = random.randint(-4, 4) if self.screen_shake > 0 else 0
        th = self.theme
        
        # Day/Night Transition in Double Elixir
        is_night = self.is_double_elixir or self.game_mode == "3X_INFINITE"
        bg_col = th["night_bg"] if is_night and "night_bg" in th else th["bg"]
        riv_col = th["night_river"] if is_night and "night_river" in th else th["river"]
        
        surf.fill(bg_col)
        pygame.draw.rect(surf, riv_col, (0+ox, RIVER_TOP+oy, SCREEN_W, RIVER_BOTTOM - RIVER_TOP))
        for bx in [BRIDGE_LEFT_X, BRIDGE_RIGHT_X]:
            pygame.draw.rect(surf, th["bridge"], (bx - BRIDGE_W//2 + ox, RIVER_TOP + oy, BRIDGE_W, RIVER_BOTTOM - RIVER_TOP))
            pygame.draw.rect(surf, C_BLACK, (bx - BRIDGE_W//2 + ox, RIVER_TOP + oy, BRIDGE_W, RIVER_BOTTOM - RIVER_TOP), 2)
        
        for r in self.runes: r.draw(surf, ox, oy)
        for t in self.player_towers + self.ai_towers: t.draw(surf, ox, oy)
        for u in self.ai_units: u.draw(surf, ox, oy)
        for u in self.player_units: u.draw(surf, ox, oy)
        for p in self.projectiles: p.draw(surf, ox, oy)
        for pt in self.particles: pt.draw(surf, ox, oy)
        for ft in self.floating_texts: ft.draw(surf, ox, oy)
        
        if self.lightning_alpha > 0:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); s.fill((255,255,255, self.lightning_alpha))
            surf.blit(s, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        # Top Info Bar
        pygame.draw.rect(surf, (15, 23, 42), (0, 0, SCREEN_W, 35))
        m_txt = FONT_MED.render(f"Mode[M]: {self.game_mode[:3]}", True, C_GOLD if self.game_mode!="CLASSIC" else C_CYAN)
        d_txt = FONT_MED.render(f"Deck[D]: {self.deck_mode[:3]}", True, C_WHITE)
        t_txt = FONT_MED.render(f"Thm[T]: {th['name'].split()[1][:3]}", True, C_WHITE)
        surf.blit(m_txt, (5, 8)); surf.blit(d_txt, (120, 8)); surf.blit(t_txt, (SCREEN_W - t_txt.get_width() - 5, 8))
        if self.game_mode == "SURVIVAL":
            w_txt = FONT_MED.render(f"W:{self.wave_number}", True, C_RED); surf.blit(w_txt, (230, 8))
        else:
            mm, ss = int(self.elapsed_time)//60, int(self.elapsed_time)%60
            time_txt = FONT_LARGE.render(f"{mm:02d}:{ss:02d}", True, C_GOLD if self.is_double_elixir else C_WHITE)
            surf.blit(time_txt, (235, 3))

        # Hero Commander & Perk Buttons (Middle Right/Left)
        hero_col = C_GOLD if self.hero.cd_timer == 0.0 else (100,116,139)
        pygame.draw.rect(surf, (15,23,42), (5, 42, 140, 26), border_radius=6)
        pygame.draw.rect(surf, hero_col, (5, 42, 140, 26), 1, border_radius=6)
        h_txt = FONT_SMALL.render(f"👑 Hero[H]: {self.hero.kind[:3]} {'READY' if self.hero.cd_timer==0 else f'{int(self.hero.cd_timer)}s'}", True, hero_col)
        surf.blit(h_txt, (10, 48))
        
        if self.perk_mgr.perks_available > 0:
            pygame.draw.rect(surf, C_GOLD, (150, 42, 145, 26), border_radius=6)
            p_txt = FONT_SMALL.render(f"🌟 UPGRADE READY [E]!", True, C_BLACK)
            surf.blit(p_txt, (155, 48))
        elif self.perk_mgr.perks_acquired:
            pygame.draw.rect(surf, (15,23,42), (150, 42, 145, 26), border_radius=6)
            p_txt = FONT_SMALL.render(f"🌟 Perks: {len(self.perk_mgr.perks_acquired)} active", True, C_PURPLE)
            surf.blit(p_txt, (155, 48))

        # Bottom Card Bar
        pygame.draw.rect(surf, (15, 23, 42), (0, SCREEN_H - 100, SCREEN_W, 100))
        pygame.draw.line(surf, (51, 65, 85), (0, SCREEN_H - 100), (SCREEN_W, SCREEN_H - 100), 2)
        
        pygame.draw.rect(surf, (59, 7, 100), (10, SCREEN_H - 95, SCREEN_W - 20, 16), border_radius=6)
        fill_w = int((SCREEN_W - 20) * (self.player_elixir / ELIXIR_MAX))
        if fill_w > 0: pygame.draw.rect(surf, C_PURPLE, (10, SCREEN_H - 95, fill_w, 16), border_radius=6)
        pygame.draw.rect(surf, C_WHITE, (10, SCREEN_H - 95, SCREEN_W - 20, 16), 1, border_radius=6)
        el_txt = FONT_SMALL.render(f"Elixir: {int(self.player_elixir)}/10", True, C_WHITE)
        surf.blit(el_txt, (18, SCREEN_H - 94))

        if self.deck_mode == "MASTER_12":
            cW, cH, gap = 35, 58, 3
            total_w = len(self.CARDS) * cW + (len(self.CARDS) - 1) * gap
            sx = (SCREEN_W - total_w) // 2; bY = SCREEN_H - cH - 6
            for i, (name, _, cost, is_spell, _) in enumerate(self.CARDS):
                cx = sx + i * (cW + gap); aff = self.player_elixir >= cost; sel = i == self.selected_card
                col = (124, 45, 18) if is_spell else (30, 41, 59) if aff else (15, 23, 42)
                pygame.draw.rect(surf, col, (cx, bY, cW, cH), border_radius=5)
                if sel: pygame.draw.rect(surf, C_GOLD, (cx-2, bY-2, cW+4, cH+4), 2, border_radius=6)
                elif not aff:
                    s = pygame.Surface((cW, cH), pygame.SRCALPHA); s.fill((0,0,0,140)); surf.blit(s, (cx, bY))
                icon_col = C_SPELL if is_spell else (C_BLUE if aff else (71, 85, 105))
                pygame.draw.circle(surf, icon_col, (cx + cW//2, bY + 18), 11)
                icon_txt = FONT_SMALL.render(name[:2], True, C_WHITE); surf.blit(icon_txt, icon_txt.get_rect(center=(cx + cW//2, bY + 18)))
                name_txt = FONT_SMALL.render(name[:3], True, C_WHITE if aff else (100,116,139)); surf.blit(name_txt, name_txt.get_rect(center=(cx + cW//2, bY + 38)))
                cost_txt = FONT_SMALL.render(str(cost), True, C_GOLD if aff else (100,116,139)); surf.blit(cost_txt, (cx + cW - 10, bY + 44))
                key_num = str((i + 1) % 10) if i < 10 else ("-" if i==10 else "=")
                key_txt = FONT_SMALL.render(key_num, True, C_CYAN); surf.blit(key_txt, (cx + 2, bY + 2))
        else:
            # PRO_CYCLE 4+1 View
            cW, cH, gap = 64, 62, 8
            total_w = 4 * cW + 3 * gap + 80
            sx = (SCREEN_W - total_w) // 2; bY = SCREEN_H - cH - 6
            for i in range(4):
                card_idx = self.hand_indices[i]
                name, _, cost, is_spell, _ = self.CARDS[card_idx]
                cx = sx + i * (cW + gap); aff = self.player_elixir >= cost; sel = i == self.selected_card
                col = (124, 45, 18) if is_spell else (30, 41, 59) if aff else (15, 23, 42)
                pygame.draw.rect(surf, col, (cx, bY, cW, cH), border_radius=6)
                if sel: pygame.draw.rect(surf, C_GOLD, (cx-2, bY-2, cW+4, cH+4), 2, border_radius=8)
                elif not aff:
                    s = pygame.Surface((cW, cH), pygame.SRCALPHA); s.fill((0,0,0,140)); surf.blit(s, (cx, bY))
                icon_col = C_SPELL if is_spell else (C_BLUE if aff else (71, 85, 105))
                pygame.draw.circle(surf, icon_col, (cx + cW//2, bY + 20), 14)
                icon_txt = FONT_MED.render(name[:2], True, C_WHITE); surf.blit(icon_txt, icon_txt.get_rect(center=(cx + cW//2, bY + 20)))
                name_txt = FONT_SMALL.render(name[:5], True, C_WHITE if aff else (100,116,139)); surf.blit(name_txt, name_txt.get_rect(center=(cx + cW//2, bY + 42)))
                cost_txt = FONT_MED.render(str(cost), True, C_GOLD if aff else (100,116,139)); surf.blit(cost_txt, (cx + cW - 14, bY + 4))
                key_txt = FONT_SMALL.render(str(i+1), True, C_CYAN); surf.blit(key_txt, (cx + 4, bY + 4))
            # Next Preview Box
            nx = sx + 4 * (cW + gap) + 10
            pygame.draw.rect(surf, (15, 23, 42), (nx, bY, 56, 62), border_radius=6)
            pygame.draw.rect(surf, (71, 85, 105), (nx, bY, 56, 62), 1, border_radius=6)
            lbl = FONT_SMALL.render("NEXT", True, C_CYAN); surf.blit(lbl, (nx + 15, bY + 2))
            n_name, _, n_cost, n_spell, _ = self.CARDS[self.next_index]
            pygame.draw.circle(surf, C_SPELL if n_spell else C_BLUE, (nx + 28, bY + 30), 12)
            n_txt = FONT_SMALL.render(n_name[:2], True, C_WHITE); surf.blit(n_txt, n_txt.get_rect(center=(nx + 28, bY + 30)))
            c_txt = FONT_SMALL.render(str(n_cost), True, C_GOLD); surf.blit(c_txt, (nx + 40, bY + 44))

        if self.flash_msg:
            f_txt = FONT_LARGE.render(self.flash_msg, True, C_RED)
            surf.blit(f_txt, f_txt.get_rect(center=(SCREEN_W//2, RIVER_BOTTOM + 20)))

        if self.state == "GAME_OVER":
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); s.fill((0,0,0,210))
            surf.blit(s, (0,0))
            msg = "VICTORY!" if self.player_won else "DEFEAT"
            col = C_GOLD if self.player_won else C_RED
            res_txt = FONT_TITLE.render(msg, True, col)
            surf.blit(res_txt, res_txt.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 140)))
            
            # Post-Game MVP Analytics Box
            pygame.draw.rect(surf, (15, 23, 42), (40, SCREEN_H//2 - 80, SCREEN_W - 80, 160), border_radius=10)
            pygame.draw.rect(surf, C_GOLD, (40, SCREEN_H//2 - 80, SCREEN_W - 80, 160), 2, border_radius=10)
            stat_title = FONT_LARGE.render("📊 BATTLE MVP & ANALYTICS", True, C_GOLD)
            surf.blit(stat_title, stat_title.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 55)))
            
            # Find MVP
            all_fought = self.player_units + self.player_towers + self.ai_units + self.ai_towers
            mvp = max(all_fought, key=lambda e: getattr(e, "damage_dealt", 0), default=None)
            mvp_name = f"{mvp.kind_name} ({mvp.team.upper()})" if mvp else "None"
            mvp_dmg = getattr(mvp, "damage_dealt", 0) if mvp else 0
            
            m_txt1 = FONT_MED.render(f"🏆 MATCH MVP: {mvp_name}", True, C_WHITE)
            m_txt2 = FONT_MED.render(f"💥 Total Damage Dealt: {mvp_dmg}", True, C_CYAN)
            m_txt3 = FONT_MED.render(f"🌟 Perks Acquired: {len(self.perk_mgr.perks_acquired)}", True, C_PURPLE)
            surf.blit(m_txt1, (60, SCREEN_H//2 - 15))
            surf.blit(m_txt2, (60, SCREEN_H//2 + 15))
            surf.blit(m_txt3, (60, SCREEN_H//2 + 45))
            
            hint_txt = FONT_MED.render("Press R to Play Again", True, C_WHITE)
            surf.blit(hint_txt, hint_txt.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 120)))

# ── Main Entry Point ────────────────────────────────────────────────────────
def main():
    game = GameState()
    while True:
        dt = clock.tick(30) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: game.try_deploy(*event.pos)
                elif event.button == 4: game.selected_card = (game.selected_card - 1) % (12 if game.deck_mode=="MASTER_12" else 4)
                elif event.button == 5: game.selected_card = (game.selected_card + 1) % (12 if game.deck_mode=="MASTER_12" else 4)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: game.reset()
                elif event.key == pygame.K_m: game.cycle_mode()
                elif event.key == pygame.K_t: game.cycle_theme()
                elif event.key == pygame.K_d: game.toggle_deck_mode()
                elif event.key == pygame.K_c: game.cycle_hero()
                elif event.key == pygame.K_h: game.hero.activate_ultimate(game)
                elif event.key == pygame.K_e: game.perk_mgr.claim_perk(game)
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    num = event.key - pygame.K_0
                    idx = num - 1
                    if idx < (12 if game.deck_mode=="MASTER_12" else 4): game.selected_card = idx
                elif event.key == pygame.K_0 and game.deck_mode=="MASTER_12": game.selected_card = 9
                elif event.key == pygame.K_MINUS and game.deck_mode=="MASTER_12": game.selected_card = 10
                elif event.key == pygame.K_EQUALS and game.deck_mode=="MASTER_12": game.selected_card = 11
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

if __name__ == "__main__":
    main()
