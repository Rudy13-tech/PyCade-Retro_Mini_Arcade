import tkinter as tk
import random
import json
import os

# ── Constants ────────────────────────────────────────────────────────────────
CELL  = 20
COLS  = 30
ROWS  = 25
W     = CELL * COLS          # 600
H     = CELL * ROWS          # 500
FPS   = 130                  # ms between ticks (start speed)
SCORE_FILE = os.path.join(os.path.expanduser("~"), ".snake_hiscore.json")

# Retro CRT palette
BG        = "#0a0a0a"
GRID      = "#111111"
SNAKE_H   = "#00ff88"
SNAKE_B   = "#00cc66"
FOOD_COL  = "#ff3355"
FOOD_GLO  = "#ff6680"
TEXT_COL  = "#00ff88"
DIM_COL   = "#336644"
SCORE_COL = "#ffcc00"
PANEL_BG  = "#0d1a0d"
BORDER    = "#00aa55"

# ── High-score persistence ────────────────────────────────────────────────────
def load_hiscore():
    try:
        with open(SCORE_FILE) as f:
            return json.load(f).get("hi", 0)
    except Exception:
        return 0

def save_hiscore(score):
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump({"hi": score}, f)
    except Exception:
        pass

# ── Game class ────────────────────────────────────────────────────────────────
class SnakeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🐍  RETRO SNAKE")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.hi_score = load_hiscore()

        # ── Layout ──
        self._build_header()
        self._build_canvas()
        self._build_footer()

        # ── Bindings ──
        self.root.bind("<KeyPress>", self._on_key)
        self.root.focus_set()

        self._reset()

    # ── UI Builders ──────────────────────────────────────────────────────────
    def _build_header(self):
        top = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        top.pack(fill=tk.X)

        tk.Label(top, text="▓ RETRO SNAKE ▓", font=("Courier", 16, "bold"),
                 fg=TEXT_COL, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)

        right = tk.Frame(top, bg=PANEL_BG)
        right.pack(side=tk.RIGHT, padx=16)

        tk.Label(right, text="SCORE", font=("Courier", 8), fg=DIM_COL, bg=PANEL_BG).grid(row=0, column=0, padx=8)
        tk.Label(right, text="HIGH", font=("Courier", 8),  fg=DIM_COL, bg=PANEL_BG).grid(row=0, column=1, padx=8)
        tk.Label(right, text="LEVEL", font=("Courier", 8), fg=DIM_COL, bg=PANEL_BG).grid(row=0, column=2, padx=8)

        self.score_var = tk.StringVar(value="000000")
        self.hi_var    = tk.StringVar(value=f"{self.hi_score:06d}")
        self.level_var = tk.StringVar(value="01")

        tk.Label(right, textvariable=self.score_var, font=("Courier", 14, "bold"),
                 fg=SCORE_COL, bg=PANEL_BG).grid(row=1, column=0, padx=8)
        tk.Label(right, textvariable=self.hi_var, font=("Courier", 14, "bold"),
                 fg="#ff9900", bg=PANEL_BG).grid(row=1, column=1, padx=8)
        tk.Label(right, textvariable=self.level_var, font=("Courier", 14, "bold"),
                 fg=TEXT_COL, bg=PANEL_BG).grid(row=1, column=2, padx=8)

        # border line
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

    def _build_footer(self):
        bot = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        bot.pack(fill=tk.X)

        tk.Label(bot, text="← ↑ → ↓  or  W A S D   |   P = Pause",
                 font=("Courier", 8), fg=DIM_COL, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)

        self.restart_btn = tk.Button(
            bot, text="▶  RESTART", font=("Courier", 9, "bold"),
            fg=BG, bg=TEXT_COL, activebackground=FOOD_COL, activeforeground="white",
            relief=tk.FLAT, padx=12, pady=3, cursor="hand2",
            command=self._reset
        )
        self.restart_btn.pack(side=tk.RIGHT, padx=16)

    # ── Game State ───────────────────────────────────────────────────────────
    def _reset(self):
        self.score   = 0
        self.level   = 1
        self.speed   = FPS
        self.paused  = False
        self.alive   = True
        self.direction  = (1, 0)
        self.next_dir   = (1, 0)

        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]

        self._place_food()
        self._update_hud()
        self.score_var.set("000000")
        self.level_var.set("01")

        if hasattr(self, "_after_id"):
            self.root.after_cancel(self._after_id)
        self._tick()

    def _place_food(self):
        occupied = set(self.snake)
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in occupied:
                self.food = pos
                break

    # ── Main Loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if not self.paused and self.alive:
            self._move()
        self._draw()
        self._after_id = self.root.after(self.speed, self._tick)

    def _move(self):
        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nx, ny = (hx + dx) % COLS, (hy + dy) % ROWS

        if (nx, ny) in self.snake[:-1]:
            self.alive = False
            self._game_over()
            return

        self.snake.insert(0, (nx, ny))

        if (nx, ny) == self.food:
            self.score += 10 * self.level
            if len(self.snake) % 5 == 0:          # level up every 5 food
                self.level += 1
                self.speed  = max(55, FPS - (self.level - 1) * 10)
                self.level_var.set(f"{self.level:02d}")
            if self.score > self.hi_score:
                self.hi_score = self.score
                save_hiscore(self.hi_score)
                self.hi_var.set(f"{self.hi_score:06d}")
            self.score_var.set(f"{self.score:06d}")
            self._place_food()
        else:
            self.snake.pop()

    def _update_hud(self):
        self.score_var.set(f"{self.score:06d}")
        self.hi_var.set(f"{self.hi_score:06d}")
        self.level_var.set(f"{self.level:02d}")

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete("all")

        # Grid
        for x in range(0, W, CELL):
            c.create_line(x, 0, x, H, fill=GRID, width=1)
        for y in range(0, H, CELL):
            c.create_line(0, y, W, y, fill=GRID, width=1)

        # Food – pulsing cross + glow square
        fx, fy = self.food
        px, py = fx * CELL, fy * CELL
        m = 3
        c.create_rectangle(px + m, py + m, px + CELL - m, py + CELL - m,
                            fill=FOOD_COL, outline=FOOD_GLO, width=2)
        c.create_line(px + CELL // 2, py + 2, px + CELL // 2, py + CELL - 2,
                      fill="white", width=2)
        c.create_line(px + 2, py + CELL // 2, px + CELL - 2, py + CELL // 2,
                      fill="white", width=2)

        # Snake
        for i, (sx, sy) in enumerate(self.snake):
            px2, py2 = sx * CELL, sy * CELL
            color = SNAKE_H if i == 0 else SNAKE_B
            pad = 1 if i > 0 else 0
            c.create_rectangle(px2 + pad, py2 + pad,
                                px2 + CELL - pad, py2 + CELL - pad,
                                fill=color, outline=BG, width=1)
            if i == 0:          # eyes
                ex = px2 + CELL - 5
                ey = py2 + 4
                c.create_oval(ex, ey, ex + 4, ey + 4, fill="black", outline="")
                c.create_oval(ex, ey + 8, ex + 4, ey + 12, fill="black", outline="")

        # Paused overlay
        if self.paused:
            c.create_rectangle(0, 0, W, H, fill="", stipple="gray50",
                                outline="", )
            self._draw_text("-- PAUSED --", W // 2, H // 2, size=22)
            self._draw_text("Press P to resume", W // 2, H // 2 + 36, size=11, color=DIM_COL)

    def _draw_text(self, text, x, y, size=16, color=TEXT_COL, anchor="center"):
        self.canvas.create_text(x + 2, y + 2, text=text,
                                font=("Courier", size, "bold"),
                                fill="#003322", anchor=anchor)
        self.canvas.create_text(x, y, text=text,
                                font=("Courier", size, "bold"),
                                fill=color, anchor=anchor)

    def _game_over(self):
        c = self.canvas
        c.create_rectangle(W // 2 - 170, H // 2 - 60,
                            W // 2 + 170, H // 2 + 80,
                            fill="#050f05", outline=FOOD_COL, width=2)
        self._draw_text("GAME  OVER",    W // 2, H // 2 - 28, size=22, color=FOOD_COL)
        self._draw_text(f"SCORE  {self.score:06d}", W // 2, H // 2 + 12, size=13)
        if self.score >= self.hi_score and self.score > 0:
            self._draw_text("✦ NEW HIGH SCORE ✦", W // 2, H // 2 + 38, size=11, color=SCORE_COL)
        self._draw_text("Press R or click RESTART", W // 2, H // 2 + 62, size=9, color=DIM_COL)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _on_key(self, event):
        k = event.keysym.lower()
        dirs = {
            "up": (0, -1), "w": (0, -1),
            "down": (0, 1), "s": (0, 1),
            "left": (-1, 0), "a": (-1, 0),
            "right": (1, 0), "d": (1, 0),
        }
        if k in dirs:
            nd = dirs[k]
            # Prevent 180° reverse
            if (nd[0] + self.direction[0], nd[1] + self.direction[1]) != (0, 0):
                self.next_dir = nd
        elif k == "p":
            self.paused = not self.paused
        elif k == "r":
            self._reset()


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
