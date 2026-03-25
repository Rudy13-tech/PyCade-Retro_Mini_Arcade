import tkinter as tk
import random, math

W, H = 500, 600
FPS  = 16

BG       = "#050510"
GRID     = "#0a0a1a"
PLAYER_C = "#00ff88"
ENEMY_C  = "#ff3355"
BULLET_C = "#00ffff"
PANEL_BG = "#020205"
BORDER   = "#0055ff"

class SpaceShooter:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("▓ SPACE SHOOTER ▓")
        self.root.resizable(False, False)
        self.root.configure(bg=PANEL_BG)

        self.score = 0
        self._build_ui()
        
        self.root.bind("<KeyPress>", self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)
        self.keys = set()
        
        self._reset()
        self._loop()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        header.pack(fill=tk.X)
        tk.Label(header, text="▓ GALAXY DEFENDER ▓", font=("Courier", 16, "bold"), fg=PLAYER_C, bg=PANEL_BG).pack(side=tk.LEFT, padx=16)
        
        self.score_var = tk.StringVar(value="000")
        tk.Label(header, textvariable=self.score_var, font=("Courier", 15, "bold"), fg=BULLET_C, bg=PANEL_BG).pack(side=tk.RIGHT, padx=16)

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)
        self.canvas = tk.Canvas(self.root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.pack()
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

    def _reset(self):
        self.px = W / 2
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.stars = [{"x": random.randint(0, W), "y": random.randint(0, H), "spd": random.uniform(1, 3)} for _ in range(40)]
        self.cooldown = 0
        self.spawn_timer = 0
        self.state = "playing"
        self.score = 0
        self.score_var.set("000")

    def _key_down(self, e):
        self.keys.add(e.keysym)
        if e.keysym in ("r", "R") and self.state == "over":
            self._reset()

    def _key_up(self, e):
        self.keys.discard(e.keysym)

    def _burst(self, x, y, color):
        for _ in range(10):
            a = random.uniform(0, math.tau)
            s = random.uniform(1, 4)
            self.particles.append([x, y, math.cos(a)*s, math.sin(a)*s, 1.0, color])

    def _update(self):
        if self.state == "over": return

        # Movement
        if "Left" in self.keys or "a" in self.keys: self.px = max(20, self.px - 6)
        if "Right" in self.keys or "d" in self.keys: self.px = min(W - 20, self.px + 6)

        # Shooting
        if ("space" in self.keys or "w" in self.keys) and self.cooldown <= 0:
            self.bullets.append({"x": self.px, "y": H - 50})
            self.cooldown = 12
        if self.cooldown > 0: self.cooldown -= 1

        # Move Bullets
        for b in self.bullets: b["y"] -= 8
        self.bullets = [b for b in self.bullets if b["y"] > 0]

        # Spawn Enemies
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.enemies.append({"x": random.randint(20, W-20), "y": -20, "hp": 1})
            self.spawn_timer = max(20, 60 - (self.score * 2)) # Gets faster!

        # Move Enemies & Check Collisions
        for e in self.enemies:
            e["y"] += 2
            
            # Hit player?
            if abs(e["x"] - self.px) < 20 and abs(e["y"] - (H - 40)) < 20:
                self.state = "over"
                self._burst(self.px, H-40, PLAYER_C)

            # Hit by bullet?
            for b in self.bullets:
                if abs(b["x"] - e["x"]) < 20 and abs(b["y"] - e["y"]) < 20:
                    e["hp"] = 0
                    b["y"] = -100 # move bullet offscreen
                    self.score += 1
                    self.score_var.set(f"{self.score:03d}")
                    self._burst(e["x"], e["y"], ENEMY_C)
                    break

        self.enemies = [e for e in self.enemies if e["hp"] > 0 and e["y"] < H + 20]

        # Stars & Particles
        for s in self.stars:
            s["y"] += s["spd"]
            if s["y"] > H: s["y"] = 0; s["x"] = random.randint(0, W)
            
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 0.05
        self.particles = [p for p in self.particles if p[4] > 0]

    def _draw(self):
        self.canvas.delete("all")
        for s in self.stars: self.canvas.create_rectangle(s["x"], s["y"], s["x"]+2, s["y"]+2, fill="#333344", outline="")
        
        if self.state == "playing":
            # Player Ship (Triangle)
            self.canvas.create_polygon(self.px, H-50, self.px-15, H-20, self.px+15, H-20, fill="", outline=PLAYER_C, width=2)
            
        for b in self.bullets:
            self.canvas.create_line(b["x"], b["y"], b["x"], b["y"]+10, fill=BULLET_C, width=3)

        for e in self.enemies:
            self.canvas.create_rectangle(e["x"]-12, e["y"]-12, e["x"]+12, e["y"]+12, fill=BG, outline=ENEMY_C, width=2)

        for p in self.particles:
            if p[4] > 0.1: self.canvas.create_rectangle(p[0]-2, p[1]-2, p[0]+2, p[1]+2, fill=p[5], outline="")

        if self.state == "over":
            self.canvas.create_text(W//2, H//2, text="MISSION FAILED", font=("Courier", 26, "bold"), fill=ENEMY_C)
            self.canvas.create_text(W//2, H//2 + 30, text="Press R to Restart", font=("Courier", 12), fill=PLAYER_C)

    def _loop(self):
        self._update()
        self._draw()
        self.root.after(FPS, self._loop)

if __name__ == "__main__":
    root = tk.Tk()
    SpaceShooter(root)
    root.mainloop()