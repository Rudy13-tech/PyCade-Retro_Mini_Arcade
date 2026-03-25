import tkinter as tk
import math, random, json, os

# ── Constants ──────────────────────────────────────────────────────────────────
W, H        = 640, 360
GROUND_Y    = H - 70
CUBE_SIZE   = 28
GRAVITY     = 0.52
JUMP_FORCE  = -11.5
FPS         = 16   # ms per frame (~60 fps)
BEST_FILE   = os.path.join(os.path.expanduser("~"), ".geodash_best.json")

BG       = "#060d06"
GRID     = "#0a140a"
GREEN    = "#00ff77"
GREEN_M  = "#00cc55"
GREEN_D  = "#003311"
GREEN_DK = "#0d2010"
GREEN_B  = "#1a4422"
G_LINE   = "#00aa44"
G_DIM    = "#226622"
RED      = "#ff3355"
RED_L    = "#ff6677"
RED_HL   = "#ff7788"
WHITE    = "#ffffff"
PANEL_BG = "#040c04"
BORDER   = "#00bb55"
TEXT_DIM = "#336633"
SCORE_COL= "#00dd66"
TITLE_COL= "#00ff77"
DIVIDER  = "#1a3a1a"
STAR_COL = "#1a3a1a"
PLATFORM_FILL = "#004422"
PLATFORM_LINE = "#00aa55"

SPEEDS = [("SLOW", 4.0), ("NORMAL", 6.0), ("FAST", 9.0)]


def load_best():
    try:
        with open(BEST_FILE) as f:
            return json.load(f).get("best", 0)
    except Exception:
        return 0

def save_best(v):
    try:
        with open(BEST_FILE, "w") as f:
            json.dump({"best": v}, f)
    except Exception:
        pass


class GeoDash:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("▓ GEO DASH ▓")
        self.root.resizable(False, False)
        self.root.configure(bg=PANEL_BG)

        self.speed_idx = 1
        self.attempts  = 0
        self.best      = load_best()

        self._build_ui()
        self.root.bind("<KeyPress>",   self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)
        self.canvas.bind("<ButtonPress-1>",   self._mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self._mouse_up)
        self.root.focus_set()

        self._init_stars()
        self._init_game()
        self._loop()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        header = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        header.pack(fill=tk.X)

        tk.Label(header, text="▓ GEO DASH ▓",
                 font=("Courier", 16, "bold"), fg=TITLE_COL, bg=PANEL_BG
                 ).pack(side=tk.LEFT, padx=16)

        hud = tk.Frame(header, bg=PANEL_BG)
        hud.pack(side=tk.RIGHT, padx=16)

        for col, label in enumerate(["DISTANCE", "BEST", "ATTEMPTS"]):
            tk.Label(hud, text=label, font=("Courier", 8),
                     fg=TEXT_DIM, bg=PANEL_BG).grid(row=0, column=col, padx=12)

        self.dist_var = tk.StringVar(value="0000")
        self.best_var = tk.StringVar(value=f"{self.best:04d}")
        self.att_var  = tk.StringVar(value="00")

        colors = [SCORE_COL, "#ffbb00", SCORE_COL]
        for col, (var, color) in enumerate(zip(
                [self.dist_var, self.best_var, self.att_var], colors)):
            tk.Label(hud, textvariable=var,
                     font=("Courier", 15, "bold"), fg=color, bg=PANEL_BG
                     ).grid(row=1, column=col, padx=12)

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        footer = tk.Frame(self.root, bg=PANEL_BG, pady=6)
        footer.pack(fill=tk.X)

        tk.Label(footer, text="SPACE / CLICK to jump  |  R = restart",
                 font=("Courier", 8), fg=TEXT_DIM, bg=PANEL_BG
                 ).pack(side=tk.LEFT, padx=16)

        btn_f = tk.Frame(footer, bg=PANEL_BG)
        btn_f.pack(side=tk.RIGHT, padx=16)

        self.spd_lbl = tk.StringVar(value=f"SPEED: {SPEEDS[self.speed_idx][0]}")
        tk.Button(btn_f, textvariable=self.spd_lbl,
                  font=("Courier", 9), fg=GREEN, bg=PANEL_BG,
                  activebackground=PANEL_BG, activeforeground=TITLE_COL,
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  highlightthickness=1, highlightbackground="#226622",
                  command=self._cycle_speed
                  ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(btn_f, text="▶  RESTART",
                  font=("Courier", 9, "bold"), fg=BG, bg=GREEN,
                  activebackground=RED, activeforeground="white",
                  relief=tk.FLAT, padx=12, pady=3, cursor="hand2",
                  command=self._full_reset
                  ).pack(side=tk.LEFT)

    # ── Stars ──────────────────────────────────────────────────────────────────
    def _init_stars(self):
        self.stars = [
            {"x": random.uniform(0, W),
             "y": random.uniform(0, GROUND_Y - 20),
             "s": random.uniform(0.8, 2.0),
             "spd": random.uniform(0.1, 0.5)}
            for _ in range(60)
        ]

    # ── Level generation ────────────────────────────────────────────────────────
    def _gen_obstacles(self):
        obs = []
        x = W + 80
        last = ""
        while x < W * 40:
            gap = random.randint(220, 400)
            x += gap
            choices = ["spike", "doublespike", "platform", "tallspike", "gap"]
            t = last
            while t == last:
                t = random.choice(choices)
            last = t

            if t == "spike":
                obs.append({"type": "spike", "x": x, "y": GROUND_Y, "w": 28, "h": 32})
            elif t == "doublespike":
                obs.append({"type": "spike", "x": x,      "y": GROUND_Y, "w": 28, "h": 32})
                obs.append({"type": "spike", "x": x + 34, "y": GROUND_Y, "w": 28, "h": 32})
            elif t == "tallspike":
                obs.append({"type": "spike", "x": x, "y": GROUND_Y - 14, "w": 32, "h": 46})
            elif t == "platform":
                py = GROUND_Y - 60 - random.randint(0, 30)
                obs.append({"type": "platform", "x": x,      "y": py,        "w": 80, "h": 14})
                obs.append({"type": "spike",    "x": x + 26, "y": py,        "w": 24, "h": 28})
            elif t == "gap":
                for k in range(3):
                    obs.append({"type": "spike", "x": x + k * 30, "y": GROUND_Y, "w": 26, "h": 30})
        return obs

    # ── Game init ───────────────────────────────────────────────────────────────
    def _init_game(self):
        self.cube       = {"y": float(GROUND_Y - CUBE_SIZE), "vy": 0.0, "on_ground": True}
        self.angle      = 0.0
        self.scroll_x   = 0.0
        self.dist       = 0
        self.state      = "start"
        self.particles  = []
        self.trail      = []
        self.jump_held  = False
        self.jump_cd    = 0
        self.ground_off = 0.0
        self.obstacles  = self._gen_obstacles()
        self.dist_var.set("0000")
        self.best_var.set(f"{self.best:04d}")

    def _full_reset(self):
        self.attempts = 0
        self.att_var.set("00")
        self._init_game()

    def _cycle_speed(self):
        self.speed_idx = (self.speed_idx + 1) % len(SPEEDS)
        self.spd_lbl.set(f"SPEED: {SPEEDS[self.speed_idx][0]}")
        self._full_reset()

    # ── Input ───────────────────────────────────────────────────────────────────
    def _do_jump(self):
        if self.state in ("start", "dead"):
            self._start_round()
            return
        if self.cube["on_ground"] and self.jump_cd <= 0:
            self.cube["vy"] = JUMP_FORCE
            self.cube["on_ground"] = False
            self.jump_cd = 8
            self._burst(90 + CUBE_SIZE / 2, self.cube["y"] + CUBE_SIZE, GREEN, 7)

    def _start_round(self):
        if self.state == "dead":
            self.attempts += 1
            self.att_var.set(f"{self.attempts:02d}")
        self.cube = {"y": float(GROUND_Y - CUBE_SIZE), "vy": 0.0, "on_ground": True}
        self.angle     = 0.0
        self.scroll_x  = 0.0
        self.dist      = 0
        self.particles = []
        self.trail     = []
        self.jump_held = False
        self.jump_cd   = 0
        self.state     = "playing"
        self.obstacles = self._gen_obstacles()
        self.dist_var.set("0000")

    def _key_down(self, e):
        k = e.keysym
        if k == "space":
            self.jump_held = True
            self._do_jump()
        if k in ("r", "R"):
            self._full_reset()

    def _key_up(self, e):
        if e.keysym == "space":
            self.jump_held = False

    def _mouse_down(self, e):
        self.jump_held = True
        self._do_jump()

    def _mouse_up(self, e):
        self.jump_held = False

    # ── Game loop ───────────────────────────────────────────────────────────────
    def _loop(self):
        if self.state == "playing":
            self._update()
        self._draw()
        self.root.after(FPS, self._loop)

    def _update(self):
        spd = SPEEDS[self.speed_idx][1]

        self.scroll_x += spd
        self.ground_off = self.scroll_x % 32
        self.dist = int(self.scroll_x / 10)
        self.dist_var.set(f"{self.dist:04d}")
        if self.dist > self.best:
            self.best = self.dist
            save_best(self.best)
            self.best_var.set(f"{self.best:04d}")

        # Stars
        for s in self.stars:
            s["x"] -= s["spd"] * spd / 6
            if s["x"] < 0:
                s["x"] = W

        # Physics
        self.cube["vy"] += GRAVITY
        self.cube["y"]  += self.cube["vy"]

        if self.cube["y"] >= GROUND_Y - CUBE_SIZE:
            self.cube["y"] = float(GROUND_Y - CUBE_SIZE)
            self.cube["vy"] = 0.0
            self.cube["on_ground"] = True
            # Snap to nearest 90° so the cube lands flat
            self.angle = round(self.angle / 90) * 90
        else:
            self.cube["on_ground"] = False

        if not self.cube["on_ground"]:
            self.angle += 4.5
        if self.jump_cd > 0:
            self.jump_cd -= 1
        if self.jump_held and self.cube["on_ground"] and self.jump_cd <= 0:
            self._do_jump()

        # Trail
        self.trail.append({"x": 90 + CUBE_SIZE / 2, "y": self.cube["y"] + CUBE_SIZE / 2, "life": 1.0})
        if len(self.trail) > 14:
            self.trail.pop(0)
        for t in self.trail:
            t["life"] -= 0.08

        # Collision
        cx1 = 90 + 3;          cy1 = self.cube["y"] + 3
        cx2 = 90 + CUBE_SIZE - 3; cy2 = self.cube["y"] + CUBE_SIZE - 3

        for obs in self.obstacles:
            ox = obs["x"] - self.scroll_x
            if ox + obs["w"] < -50 or ox > W + 50:
                continue
            if obs["type"] == "spike":
                sx1, sy1 = ox + 2, obs["y"] - obs["h"]
                sx2, sy2 = ox + obs["w"] - 2, obs["y"]
                if cx2 > sx1 and cx1 < sx2 and cy2 > sy1 + 4 and cy1 < sy2:
                    self._die(); return
            elif obs["type"] == "platform":
                px1, py1 = ox, obs["y"]
                px2, py2 = ox + obs["w"], obs["y"] + obs["h"]
                if cx2 > px1 + 4 and cx1 < px2 - 4 and \
                   self.cube["y"] + CUBE_SIZE <= py2 + 4 and \
                   self.cube["y"] + CUBE_SIZE >= py1 - 2 and self.cube["vy"] >= 0:
                    self.cube["y"] = py1 - CUBE_SIZE
                    self.cube["vy"] = 0.0
                    self.cube["on_ground"] = True
                    self.angle = round(self.angle / 90) * 90
                elif cx2 > px1 and cx1 < px2 and cy2 > py1 and cy1 < py2:
                    self._die(); return

        # Particles
        for p in self.particles:
            p["x"] += p["dx"]; p["y"] += p["dy"]
            p["dy"] += 0.15;   p["life"] -= 0.04
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _die(self):
        self.state = "dead"
        self._burst(90 + CUBE_SIZE / 2, self.cube["y"] + CUBE_SIZE / 2, GREEN, 12)
        self._burst(90 + CUBE_SIZE / 2, self.cube["y"] + CUBE_SIZE / 2, "#ffcc00", 10)

    def _burst(self, x, y, color, n):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(1.5, 5)
            self.particles.append({
                "x": x, "y": y,
                "dx": math.cos(a) * s, "dy": math.sin(a) * s - 1,
                "life": 1.0, "color": color
            })

    # ── Drawing ─────────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete("all")

        # Grid
        for x in range(0, W, 32):
            c.create_line(x, 0, x, H, fill=GRID, width=1)
        for y in range(0, H, 32):
            c.create_line(0, y, W, y, fill=GRID, width=1)

        # Stars
        for s in self.stars:
            c.create_rectangle(s["x"], s["y"], s["x"] + s["s"], s["y"] + s["s"],
                                fill=STAR_COL, outline="")

        # Ground tiles
        start = -int(self.ground_off) - 32
        for tx in range(start, W + 32, 32):
            c.create_rectangle(tx, GROUND_Y, tx + 32, H,
                                fill=GREEN_DK, outline=GREEN_B, width=1)
        c.create_line(0, GROUND_Y, W, GROUND_Y, fill=G_LINE, width=2)

        # Obstacles
        for obs in self.obstacles:
            ox = obs["x"] - self.scroll_x
            if ox + obs["w"] < -60 or ox > W + 60:
                continue
            if obs["type"] == "spike":
                tx, ty = ox + obs["w"] / 2, obs["y"] - obs["h"]
                bx1, bx2, by = ox, ox + obs["w"], obs["y"]
                c.create_polygon(tx, ty, bx2, by, bx1, by,
                                 fill=RED, outline=RED_L, width=1)
                # highlight
                c.create_polygon(tx, ty + 6,
                                 tx + 5, by - 8,
                                 tx - 5, by - 8,
                                 fill=RED_HL, outline="")
            elif obs["type"] == "platform":
                ox2 = ox + obs["w"]
                c.create_rectangle(ox, obs["y"], ox2, obs["y"] + obs["h"],
                                   fill=PLATFORM_FILL, outline=PLATFORM_LINE, width=1)
                c.create_rectangle(ox + 2, obs["y"] + 2, ox2 - 2, obs["y"] + 5,
                                   fill="#00ff7733", outline="")

        # Trail
        for i, t in enumerate(self.trail):
            frac = (i + 1) / max(len(self.trail), 1)
            sz = max(2, int(CUBE_SIZE * frac * 0.5))
            alpha = max(0, t["life"])
            if alpha > 0.05:
                c.create_rectangle(t["x"] - sz // 2, t["y"] - sz // 2,
                                   t["x"] + sz // 2, t["y"] + sz // 2,
                                   fill=GREEN, outline="")

        # Particles
        for p in self.particles:
            if p["life"] > 0.05:
                c.create_rectangle(p["x"] - 3, p["y"] - 3,
                                   p["x"] + 3, p["y"] + 3,
                                   fill=p["color"], outline="")

        # Cube
        if self.state != "dead" or self.particles:
            if self.state != "dead":
                cx = 90 + CUBE_SIZE / 2
                cy = self.cube["y"] + CUBE_SIZE / 2
                rad = math.radians(self.angle)
                cos_r, sin_r = math.cos(rad), math.sin(rad)

                def rot(dx, dy):
                    return (cx + cos_r * dx - sin_r * dy,
                            cy + sin_r * dx + cos_r * dy)

                h = CUBE_SIZE / 2
                corners = [rot(-h, -h), rot(h, -h), rot(h, h), rot(-h, h)]
                flat = [v for pt in corners for v in pt]
                # shadow
                sc = [v + 2 for v in flat]  # rough offset
                # body
                c.create_polygon(flat, fill=GREEN_M, outline=GREEN, width=1)
                # inner square
                h2 = h - 4
                inner = [rot(-h2, -h2), rot(h2, -h2), rot(h2, h2), rot(-h2, h2)]
                c.create_polygon([v for pt in inner for v in pt],
                                 fill=GREEN, outline="")
                # centre hole
                h3 = h - 8
                centre = [rot(-h3, -h3), rot(h3, -h3), rot(h3, h3), rot(-h3, h3)]
                c.create_polygon([v for pt in centre for v in pt],
                                 fill=GREEN_D, outline="")
                # corner dots
                for dx2, dy2 in [(-h + 4, -h + 4), (h - 7, -h + 4),
                                  (-h + 4, h - 7),  (h - 7, h - 7)]:
                    dot = rot(dx2, dy2)
                    c.create_rectangle(dot[0], dot[1],
                                       dot[0] + 4, dot[1] + 4,
                                       fill=GREEN, outline="")

        # Progress bar
        if self.state == "playing":
            prog = min(self.dist / 3000, 1.0)
            c.create_rectangle(10, 10, 210, 16, fill="#0a1a0a", outline=G_DIM, width=1)
            if prog > 0:
                c.create_rectangle(10, 10, 10 + int(200 * prog), 16,
                                   fill=G_LINE, outline="")

        # Start screen
        if self.state == "start":
            c.create_rectangle(0, 0, W, H, fill="#000000", outline="", stipple="gray50")
            c.create_text(W // 2 + 2, H // 2 - 28, text="▓ GEO DASH ▓",
                          font=("Courier", 26, "bold"), fill="#001500")
            c.create_text(W // 2, H // 2 - 28, text="▓ GEO DASH ▓",
                          font=("Courier", 26, "bold"), fill=GREEN)
            c.create_text(W // 2, H // 2 + 10,
                          text="PRESS SPACE or CLICK to start",
                          font=("Courier", 12), fill=TEXT_DIM)
            c.create_text(W // 2, H // 2 + 34,
                          text="avoid spikes  |  land on platforms  |  survive!",
                          font=("Courier", 10), fill="#224422")

        # Dead screen
        if self.state == "dead" and len(self.particles) < 4:
            c.create_rectangle(W // 2 - 170, H // 2 - 65, W // 2 + 170, H // 2 + 70,
                                fill="#050f05", outline=RED, width=2)
            c.create_text(W // 2 + 2, H // 2 - 24, text="YOU DIED",
                          font=("Courier", 26, "bold"), fill="#300005")
            c.create_text(W // 2, H // 2 - 24, text="YOU DIED",
                          font=("Courier", 26, "bold"), fill=RED)
            c.create_text(W // 2, H // 2 + 8,
                          text=f"DISTANCE  {self.dist:04d}",
                          font=("Courier", 14, "bold"), fill=SCORE_COL)
            if self.dist >= self.best and self.dist > 0:
                c.create_text(W // 2, H // 2 + 30,
                              text="✦ NEW BEST ✦",
                              font=("Courier", 11), fill="#ffcc00")
            c.create_text(W // 2, H // 2 + 54,
                          text="SPACE / CLICK to retry",
                          font=("Courier", 10), fill=TEXT_DIM)


if __name__ == "__main__":
    root = tk.Tk()
    GeoDash(root)
    root.mainloop()
