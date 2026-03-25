import tkinter as tk
import math, random

# ── Constants ──────────────────────────────────────────────────────────────────
W, H        = 640, 480
PADDLE_W    = 80
PADDLE_H    = 10
BALL_SIZE   = 10
FPS         = 16

BG        = "#060d06"
GRID      = "#0a140a"
GREEN     = "#00ff77"
CYAN      = "#00ffff"
PURPLE    = "#ff00ff"
WHITE     = "#ffffff"
PANEL_BG  = "#040c04"
BORDER    = "#00bb55"
TEXT_DIM  = "#336633"

class BrickBreaker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("▓ BRICK BREAKER ▓")
        self.root.resizable(False, False)
        self.root.configure(bg=PANEL_BG)

        self.score = 0
        self.state = "start"
        self._build_ui()
        
        self.root.bind("<KeyPress>", self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)
        self.root.bind("<Motion>", self._mouse_move)
        self.keys = set()
        
        self._reset()
        self._loop()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        header.pack(fill=tk.X)

        tk.Label(header, text="▓ BRICK BREAKER ▓", font=("Courier", 16, "bold"), fg=CYAN, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)
        
        self.score_var = tk.StringVar(value="0000")
        tk.Label(header, text="SCORE", font=("Courier", 8), fg=TEXT_DIM, bg=PANEL_BG).pack(side=tk.RIGHT, padx=(0, 16))
        tk.Label(header, textvariable=self.score_var, font=("Courier", 15, "bold"), fg=GREEN, bg=PANEL_BG).pack(side=tk.RIGHT, padx=10)

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)
        self.canvas = tk.Canvas(self.root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.pack()
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        footer = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        footer.pack(fill=tk.X)
        tk.Label(footer, text="MOUSE or ← / → to move  |  SPACE to launch", font=("Courier", 8), fg=TEXT_DIM, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)

    def _reset(self):
        self.paddle_x = W / 2 - PADDLE_W / 2
        self.ball_x = W / 2
        self.ball_y = H - 40
        self.ball_dx = 0
        self.ball_dy = 0
        self.bricks = []
        self.particles = []
        self.state = "start"
        self.score = 0
        self.score_var.set("0000")
        
        # Generate Bricks
        colors = [PURPLE, CYAN, GREEN]
        for row in range(5):
            for col in range(10):
                self.bricks.append({
                    "x": 20 + col * 60, "y": 40 + row * 25, 
                    "w": 50, "h": 15, 
                    "color": colors[row % len(colors)], "active": True
                })

    def _launch(self):
        if self.state == "start":
            self.state = "playing"
            self.ball_dx = random.choice([-4, 4])
            self.ball_dy = -5

    def _key_down(self, e):
        self.keys.add(e.keysym)
        if e.keysym == "space":
            self._launch()
        if e.keysym in ("r", "R") and self.state == "over":
            self._reset()

    def _key_up(self, e):
        self.keys.discard(e.keysym)

    def _mouse_move(self, e):
        if self.state in ("start", "playing"):
            self.paddle_x = max(0, min(W - PADDLE_W, e.x - PADDLE_W / 2))

    def _burst(self, x, y, color):
        for _ in range(8):
            a = random.uniform(0, math.tau)
            s = random.uniform(2, 6)
            self.particles.append([x, y, math.cos(a)*s, math.sin(a)*s, 1.0, color])

    def _update(self):
        # Paddle Move Keyboard
        if "Left" in self.keys: self.paddle_x = max(0, self.paddle_x - 7)
        if "Right" in self.keys: self.paddle_x = min(W - PADDLE_W, self.paddle_x + 7)

        if self.state == "start":
            self.ball_x = self.paddle_x + PADDLE_W / 2
            return

        if self.state == "playing":
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy

            # Wall bounces
            if self.ball_x <= 0 or self.ball_x >= W:
                self.ball_dx *= -1
            if self.ball_y <= 0:
                self.ball_dy *= -1

            # Paddle bounce
            if (self.ball_dy > 0 and H - 30 <= self.ball_y <= H - 20 and 
                self.paddle_x <= self.ball_x <= self.paddle_x + PADDLE_W):
                self.ball_dy *= -1
                # Add slight angle based on where it hit the paddle
                hit_pos = (self.ball_x - self.paddle_x) / PADDLE_W
                self.ball_dx = (hit_pos - 0.5) * 10 

            # Brick collision
            for b in self.bricks:
                if b["active"]:
                    if (b["x"] < self.ball_x < b["x"] + b["w"] and 
                        b["y"] < self.ball_y < b["y"] + b["h"]):
                        b["active"] = False
                        self.ball_dy *= -1
                        self.score += 10
                        self.score_var.set(f"{self.score:04d}")
                        self._burst(self.ball_x, self.ball_y, b["color"])
                        break

            # Death
            if self.ball_y > H:
                self.state = "over"

            # Check Win
            if not any(b["active"] for b in self.bricks):
                self.state = "over"

        # Particles
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 0.05
        self.particles = [p for p in self.particles if p[4] > 0]

    def _draw(self):
        self.canvas.delete("all")
        
        # Grid
        for x in range(0, W, 32): self.canvas.create_line(x, 0, x, H, fill=GRID)
        for y in range(0, H, 32): self.canvas.create_line(0, y, W, y, fill=GRID)

        # Paddle
        self.canvas.create_rectangle(self.paddle_x, H - 30, self.paddle_x + PADDLE_W, H - 20, fill=CYAN, outline=WHITE)

        # Bricks
        for b in self.bricks:
            if b["active"]:
                self.canvas.create_rectangle(b["x"], b["y"], b["x"]+b["w"], b["y"]+b["h"], fill=BG, outline=b["color"], width=2)

        # Particles
        for p in self.particles:
            if p[4] > 0.1:
                self.canvas.create_rectangle(p[0]-2, p[1]-2, p[0]+2, p[1]+2, fill=p[5], outline="")

        # Ball
        if self.state in ("start", "playing"):
            bs = BALL_SIZE // 2
            self.canvas.create_rectangle(self.ball_x-bs, self.ball_y-bs, self.ball_x+bs, self.ball_y+bs, fill=WHITE, outline=GREEN)

        if self.state == "over":
            self.canvas.create_text(W//2, H//2, text="GAME OVER", font=("Courier", 26, "bold"), fill=PURPLE)
            self.canvas.create_text(W//2, H//2 + 30, text="Press R to Restart", font=("Courier", 12), fill=TEXT_DIM)

    def _loop(self):
        self._update()
        self._draw()
        self.root.after(FPS, self._loop)

if __name__ == "__main__":
    root = tk.Tk()
    BrickBreaker(root)
    root.mainloop()