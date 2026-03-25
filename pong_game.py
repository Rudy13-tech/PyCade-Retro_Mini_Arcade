import tkinter as tk
import math, random, time

# ── Constants ──────────────────────────────────────────────────────────────────
W, H        = 640, 380
PADDLE_W    = 10
PADDLE_H    = 70
BALL_SIZE   = 10
P_SPEED     = 5.5
WIN_SCORE   = 7
FPS         = 16          # ~60 fps

BG        = "#060d06"
GRID      = "#0a140a"
GREEN     = "#00ff77"
GREEN_DIM = "#224422"
RED       = "#ff4466"
RED_DIM   = "#442222"
WHITE     = "#ffffff"
DIVIDER   = "#1a3a1a"
PANEL_BG  = "#040c04"
BORDER    = "#00bb55"
TEXT_DIM  = "#336633"
SCORE_COL = "#00dd66"
TITLE_COL = "#00ff77"

DIFFICULTIES = [
    dict(label="EASY",   ball_spd=3.2, react=4.0,  error=55),
    dict(label="MEDIUM", ball_spd=4.2, react=5.5,  error=28),
    dict(label="HARD",   ball_spd=5.2, react=7.0,  error=10),
]


class PongGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("▓ RETRO PONG ▓")
        self.root.resizable(False, False)
        self.root.configure(bg=PANEL_BG)

        self.diff_idx = 1
        self._build_ui()
        self.root.bind("<KeyPress>",   self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)
        self.root.focus_set()
        self.keys = set()
        self._reset()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        tk.Frame(self.root, bg=PANEL_BG, height=2).pack(fill=tk.X)

        header = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        header.pack(fill=tk.X)

        tk.Label(header, text="▓ RETRO PONG ▓",
                 font=("Courier", 16, "bold"), fg=TITLE_COL, bg=PANEL_BG
                 ).pack(side=tk.LEFT, padx=16)

        score_frame = tk.Frame(header, bg=PANEL_BG)
        score_frame.pack(side=tk.RIGHT, padx=16)

        tk.Label(score_frame, text="PLAYER", font=("Courier", 8),
                 fg=GREEN_DIM, bg=PANEL_BG).grid(row=0, column=0, padx=10)
        tk.Label(score_frame, text="  :  ",  font=("Courier", 8),
                 fg=TEXT_DIM,  bg=PANEL_BG).grid(row=0, column=1)
        tk.Label(score_frame, text="BOT",    font=("Courier", 8),
                 fg=RED_DIM,   bg=PANEL_BG).grid(row=0, column=2, padx=10)

        self.p1_var = tk.StringVar(value="00")
        self.p2_var = tk.StringVar(value="00")

        tk.Label(score_frame, textvariable=self.p1_var,
                 font=("Courier", 20, "bold"), fg=SCORE_COL, bg=PANEL_BG
                 ).grid(row=1, column=0, padx=10)
        tk.Label(score_frame, text="  :  ",
                 font=("Courier", 20, "bold"), fg=TEXT_DIM, bg=PANEL_BG
                 ).grid(row=1, column=1)
        tk.Label(score_frame, textvariable=self.p2_var,
                 font=("Courier", 20, "bold"), fg=RED, bg=PANEL_BG
                 ).grid(row=1, column=2, padx=10)

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        footer = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        footer.pack(fill=tk.X)

        tk.Label(footer, text="W / S  or  ↑ / ↓  to move  |  P = pause  |  first to 7 wins",
                 font=("Courier", 8), fg=TEXT_DIM, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)

        btn_frame = tk.Frame(footer, bg=PANEL_BG)
        btn_frame.pack(side=tk.RIGHT, padx=16)

        self.diff_btn = tk.Button(
            btn_frame, text=f"BOT: {DIFFICULTIES[self.diff_idx]['label']}",
            font=("Courier", 9), fg=GREEN, bg=PANEL_BG,
            activebackground=PANEL_BG, activeforeground=TITLE_COL,
            relief=tk.FLAT, bd=1, padx=10, pady=3, cursor="hand2",
            highlightthickness=1, highlightbackground="#226622",
            command=self._cycle_diff
        )
        self.diff_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame, text="▶  RESTART",
            font=("Courier", 9, "bold"), fg=BG, bg=GREEN,
            activebackground=RED, activeforeground="white",
            relief=tk.FLAT, padx=12, pady=3, cursor="hand2",
            command=self._reset
        ).pack(side=tk.LEFT)

    # ── Game logic ────────────────────────────────────────────────────────────
    def _reset(self):
        d = DIFFICULTIES[self.diff_idx]
        self.p1_y    = H / 2 - PADDLE_H / 2
        self.p2_y    = H / 2 - PADDLE_H / 2
        self.p1_score = 0
        self.p2_score = 0
        self.paused   = False
        self.state    = "playing"
        self.flash    = 0
        self.flash_side = 0
        self.particles = []
        self._spawn_ball(1)
        self.p1_var.set("00")
        self.p2_var.set("00")
        if hasattr(self, "_after_id"):
            self.root.after_cancel(self._after_id)
        self._loop()

    def _spawn_ball(self, direction):
        d = DIFFICULTIES[self.diff_idx]
        angle = random.uniform(-0.3, 0.3)
        if random.random() > 0.5:
            angle += math.pi
        spd = d["ball_spd"]
        self.bx = W / 2
        self.by = H / 2
        self.bdx = math.cos(angle) * spd * direction
        self.bdy = math.sin(angle) * spd + random.uniform(-0.8, 0.8)
        self.ball_glow = 0
        self.trail = []

    def _cycle_diff(self):
        self.diff_idx = (self.diff_idx + 1) % len(DIFFICULTIES)
        self.diff_btn.config(text=f"BOT: {DIFFICULTIES[self.diff_idx]['label']}")
        self._reset()

    def _loop(self):
        if self.state == "playing" and not self.paused:
            self._update()
        self._draw()
        self._after_id = self.root.after(FPS, self._loop)

    def _update(self):
        d = DIFFICULTIES[self.diff_idx]

        # Player
        if "w" in self.keys or "W" in self.keys or "Up" in self.keys:
            self.p1_y -= P_SPEED
        if "s" in self.keys or "S" in self.keys or "Down" in self.keys:
            self.p1_y += P_SPEED
        self.p1_y = max(0, min(H - PADDLE_H, self.p1_y))

        # Bot
        target = self.by - PADDLE_H / 2 + random.uniform(-1, 1) * d["error"] * 0.15
        diff   = target - self.p2_y
        self.p2_y += max(-d["react"], min(d["react"], diff))
        self.p2_y = max(0, min(H - PADDLE_H, self.p2_y))

        # Trail
        self.trail.append((self.bx, self.by))
        if len(self.trail) > 8:
            self.trail.pop(0)

        # Move ball
        self.bx += self.bdx
        self.by += self.bdy
        self.ball_glow = max(0, self.ball_glow - 0.06)

        # Wall bounce
        if self.by - BALL_SIZE / 2 <= 0:
            self.by = BALL_SIZE / 2
            self.bdy = abs(self.bdy)
            self._burst(self.bx, 0, GREEN, 5)
        if self.by + BALL_SIZE / 2 >= H:
            self.by = H - BALL_SIZE / 2
            self.bdy = -abs(self.bdy)
            self._burst(self.bx, H, GREEN, 5)

        # Paddle collision helper
        def hit(px, py, side):
            rel  = (self.by - (py + PADDLE_H / 2)) / (PADDLE_H / 2)
            ang  = rel * 1.1
            spd  = min(math.hypot(self.bdx, self.bdy) * 1.06, 12)
            self.bdx = side * abs(math.cos(ang)) * spd
            self.bdy = math.sin(ang) * spd
            self.ball_glow = 1
            self._burst(self.bx, self.by, GREEN, 10)

        p1x = 18
        p2x = W - 18 - PADDLE_W
        if (self.bdx < 0 and
                p1x <= self.bx - BALL_SIZE / 2 <= p1x + PADDLE_W and
                self.p1_y <= self.by <= self.p1_y + PADDLE_H):
            self.bx = p1x + PADDLE_W + BALL_SIZE / 2
            hit(p1x, self.p1_y, 1)

        if (self.bdx > 0 and
                p2x <= self.bx + BALL_SIZE / 2 <= p2x + PADDLE_W and
                self.p2_y <= self.by <= self.p2_y + PADDLE_H):
            self.bx = p2x - BALL_SIZE / 2
            hit(p2x, self.p2_y, -1)

        # Score
        if self.bx < 0:
            self.p2_score += 1
            self.p2_var.set(f"{self.p2_score:02d}")
            self.flash = 25; self.flash_side = 2
            self._burst(0, self.by, RED, 18)
            if self.p2_score >= WIN_SCORE:
                self.state = "over"; return
            self._spawn_ball(-1)

        if self.bx > W:
            self.p1_score += 1
            self.p1_var.set(f"{self.p1_score:02d}")
            self.flash = 25; self.flash_side = 1
            self._burst(W, self.by, GREEN, 18)
            if self.p1_score >= WIN_SCORE:
                self.state = "over"; return
            self._spawn_ball(1)

        if self.flash > 0:
            self.flash -= 1

        # Particles
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]
            p[4] -= 0.05; p[2] *= 0.88; p[3] *= 0.88
        self.particles = [p for p in self.particles if p[4] > 0]

    def _burst(self, x, y, color, n):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(1.5, 4)
            self.particles.append([x, y, math.cos(a)*s, math.sin(a)*s, 1.0, color])

    # ── Drawing ────────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete("all")
        c.configure(bg=BG)

        # Grid
        for x in range(0, W, 32):
            c.create_line(x, 0, x, H, fill=GRID, width=1)
        for y in range(0, H, 32):
            c.create_line(0, y, W, y, fill=GRID, width=1)

        # Flash
        if self.flash > 0:
            stipple_levels = ["gray12", "gray12", "gray25", "gray25", "gray50", "gray50", "gray75", "gray75"]
            idx = min(int((self.flash / 25) * len(stipple_levels)), len(stipple_levels)-1)
            col = GREEN if self.flash_side == 1 else RED
            sx = 0 if self.flash_side == 1 else W // 2
            c.create_rectangle(sx, 0, sx + W // 2, H, fill=col,
                                outline="", stipple=stipple_levels[idx])

        # Centre divider
        for y in range(0, H, 16):
            c.create_line(W//2, y, W//2, y+8, fill=DIVIDER, width=2)

        # Particles
        for p in self.particles:
            alpha = max(0, p[4])
            if alpha > 0.1:
                c.create_rectangle(p[0]-2, p[1]-2, p[0]+2, p[1]+2, fill=p[5], outline="")

        # Ball trail
        for i, (tx, ty) in enumerate(self.trail):
            frac = (i + 1) / len(self.trail)
            sz = max(2, int(BALL_SIZE * frac * 0.6))
            c.create_rectangle(tx-sz//2, ty-sz//2, tx+sz//2, ty+sz//2,
                                fill=GREEN, outline="")

        # Paddles
        pg = 3
        p1x = 18
        p2x = W - 18 - PADDLE_W
        c.create_rectangle(p1x, self.p1_y + pg, p1x + PADDLE_W, self.p1_y + PADDLE_H - pg,
                            fill=GREEN, outline="#00aa44", width=1)
        c.create_rectangle(p2x, self.p2_y + pg, p2x + PADDLE_W, self.p2_y + PADDLE_H - pg,
                            fill=RED, outline="#cc2244", width=1)

        # Ball
        if self.state in ("playing", "over"):
            if self.ball_glow > 0:
                gw = int(BALL_SIZE * 1.8)
                c.create_rectangle(self.bx-gw, self.by-gw, self.bx+gw, self.by+gw,
                                    fill=GREEN, outline="", stipple="gray25")
            bs = BALL_SIZE // 2
            c.create_rectangle(self.bx-bs, self.by-bs, self.bx+bs, self.by+bs,
                                fill=WHITE, outline="#aaffcc", width=1)

        # Player labels
        c.create_text(28, 10, text="PLAYER", font=("Courier", 8), fill=GREEN_DIM, anchor="w")
        c.create_text(W-28, 10, text="BOT", font=("Courier", 8), fill=RED_DIM, anchor="e")

        # Paused
        if self.paused and self.state == "playing":
            c.create_rectangle(0, 0, W, H, fill="#000000", outline="", stipple="gray50")
            c.create_text(W//2+2, H//2+2, text="-- PAUSED --",
                          font=("Courier", 24, "bold"), fill="#003322")
            c.create_text(W//2, H//2, text="-- PAUSED --",
                          font=("Courier", 24, "bold"), fill=GREEN)
            c.create_text(W//2, H//2+30, text="Press P to resume",
                          font=("Courier", 11), fill=TEXT_DIM)

        # Game over
        if self.state == "over":
            winner = "PLAYER" if self.p1_score >= WIN_SCORE else "BOT"
            wcol   = GREEN if self.p1_score >= WIN_SCORE else RED
            c.create_rectangle(W//2-170, H//2-72, W//2+170, H//2+72,
                                fill="#050f05", outline=wcol, width=2)
            c.create_text(W//2, H//2-40, text="GAME  OVER",
                          font=("Courier", 13, "bold"), fill=TEXT_DIM)
            c.create_text(W//2+2, H//2-6, text=f"{winner}  WINS!",
                          font=("Courier", 26, "bold"), fill="#001500")
            c.create_text(W//2, H//2-6, text=f"{winner}  WINS!",
                          font=("Courier", 26, "bold"), fill=wcol)
            c.create_text(W//2, H//2+24, text=f"{self.p1_score}  :  {self.p2_score}",
                          font=("Courier", 16, "bold"), fill=SCORE_COL)
            c.create_text(W//2, H//2+52, text="Press R or click RESTART",
                          font=("Courier", 10), fill=TEXT_DIM)

    def _key_down(self, e):
        self.keys.add(e.keysym)
        if e.keysym in ("p", "P"):
            self.paused = not self.paused
        if e.keysym in ("r", "R") and self.state == "over":
            self._reset()

    def _key_up(self, e):
        self.keys.discard(e.keysym)


if __name__ == "__main__":
    root = tk.Tk()
    PongGame(root)
    root.mainloop()
