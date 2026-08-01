import streamlit as st

import textwrap, pathlib
code = textwrap.dedent('''
import pygame, math, random, sys
pygame.init()

SCREEN_W, SCREEN_H = 480, 800
FPS = 60
RIVER_TOP    = SCREEN_H // 2 - 30
RIVER_BOTTOM = SCREEN_H // 2 + 30
RIVER_MID    = (RIVER_TOP + RIVER_BOTTOM) // 2
BRIDGE_LEFT_X  = SCREEN_W // 4
BRIDGE_RIGHT_X = 3 * SCREEN_W // 4
BRIDGE_W       = 60
PLAYER_HALF_TOP    = RIVER_BOTTOM
PLAYER_HALF_BOTTOM = SCREEN_H - 110
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
st.write("Config loaded ok")
'''.strip())
pathlib.Path("test_cfg.py").write_text(code, encoding="utf-8")
st.write("wrote test_cfg.py")
