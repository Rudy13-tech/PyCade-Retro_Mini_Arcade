import tkinter as tk
import importlib

# ── Constants (Matching your retro CRT style) ──────────────────────────────────
BG        = "#060d06"
PANEL_BG  = "#040c04"
GRID      = "#0a140a"
GREEN     = "#00ff77"
GREEN_DIM = "#224422"
TITLE_COL = "#00ff77"
TEXT_DIM  = "#336633"
BORDER    = "#00bb55"
HOVER_BG  = "#0a1f0a"

# ── Game Registry ──────────────────────────────────────────────────────────────
GAMES = [
    {
        "name": "GEO DASH",
        "desc": "Avoid spikes, land on platforms, survive!",
        "module": "geo_dash",    
        "class": "GeoDash"
    },
    {
        "name": "RETRO PONG",
        "desc": "Classic Pong against a bot. First to 7 wins.",
        "module": "pong_game",
        "class": "PongGame"
    },
    {
        "name": "RETRO SNAKE",
        "desc": "Eat food, grow longer, beat the high score.",
        "module": "snake_game",
        "class": "SnakeGame"
    },
    {
        "name": "BRICK BREAKER",
        "desc": "Smash all the blocks without dropping the ball.",
        "module": "brick_breaker",    
        "class": "BrickBreaker"
    },
    {
        "name": "SPACE SHOOTER",
        "desc": "Defend the galaxy from falling enemy shapes.",
        "module": "space_shooter",    
        "class": "SpaceShooter"
    }
]

class ArcadeHub:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("▓ RETRO ARCADE HUB ▓")
        # Made the window slightly taller and wider to accommodate the scrollbar
        self.root.geometry("680x600") 
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._build_ui()

        # Bind mousewheel for scrolling
        self.root.bind("<MouseWheel>", self._on_mousewheel)
        # Linux scroll support
        self.root.bind("<Button-4>", self._on_mousewheel)
        self.root.bind("<Button-5>", self._on_mousewheel)

    def _build_ui(self):
        # ── Header ──
        tk.Frame(self.root, bg=PANEL_BG, height=2).pack(fill=tk.X)
        header = tk.Frame(self.root, bg=PANEL_BG, pady=15)
        header.pack(fill=tk.X)

        tk.Label(header, text="▓ RETRO ARCADE HUB ▓",
                 font=("Courier", 22, "bold"), fg=TITLE_COL, bg=PANEL_BG).pack()
        tk.Label(header, text="SELECT A GAME TO PLAY",
                 font=("Courier", 10), fg=TEXT_DIM, bg=PANEL_BG).pack(pady=(5, 0))

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        # ── Scrollable Area Setup ──
        # 1. Main container to hold Canvas and Scrollbar
        self.main_container = tk.Frame(self.root, bg=BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # 2. Canvas
        self.canvas = tk.Canvas(self.main_container, bg=BG, highlightthickness=0)
        
        # 3. Scrollbar
        self.scrollbar = tk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        
        # 4. Frame inside the Canvas (This will hold the game cards)
        self.list_frame = tk.Frame(self.canvas, bg=BG)

        # Configure canvas to update scroll region when inner frame changes size
        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Add the inner frame to a window in the canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        
        # Make the inner frame expand to canvas width
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5))

        # Populate the list frame with games
        for game_info in GAMES:
            self._create_game_card(game_info)

        # ── Footer ──
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)
        footer = tk.Frame(self.root, bg=PANEL_BG, pady=10)
        footer.pack(fill=tk.X)
        
        tk.Label(footer, text="Scroll down to see more games!",
                 font=("Courier", 8), fg=GREEN_DIM, bg=PANEL_BG).pack()

    def _on_canvas_configure(self, event):
        # Update the width of the inner frame to match the canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Handle scrolling for Windows/Mac (MouseWheel) and Linux (Button-4/5)
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def _create_game_card(self, game_info):
        """Creates a stylized clickable card for a game."""
        card = tk.Frame(self.list_frame, bg=PANEL_BG, bd=1, relief=tk.SOLID, 
                        highlightbackground=BORDER, highlightthickness=1, cursor="hand2")
        # Pack with some padding to look nice
        card.pack(fill=tk.X, padx=20, pady=10)

        # Left side info
        info_frame = tk.Frame(card, bg=PANEL_BG)
        info_frame.pack(side=tk.LEFT, padx=15, pady=15)

        title = tk.Label(info_frame, text=f"▶ {game_info['name']}", 
                         font=("Courier", 16, "bold"), fg=GREEN, bg=PANEL_BG)
        title.pack(anchor="w")

        desc = tk.Label(info_frame, text=game_info['desc'], 
                        font=("Courier", 10), fg=TEXT_DIM, bg=PANEL_BG)
        desc.pack(anchor="w", pady=(4, 0))

        # Right side button visual
        play_btn = tk.Label(card, text="PLAY", font=("Courier", 12, "bold"), 
                            fg=BG, bg=GREEN, padx=15, pady=5)
        play_btn.pack(side=tk.RIGHT, padx=20)

        # Bind hover and click events
        widgets = [card, info_frame, title, desc, play_btn]
        for w in widgets:
            w.bind("<Enter>", lambda e, c=card, t=info_frame, l1=title, l2=desc: 
                   self._on_hover(c, t, l1, l2, True))
            w.bind("<Leave>", lambda e, c=card, t=info_frame, l1=title, l2=desc: 
                   self._on_hover(c, t, l1, l2, False))
            w.bind("<Button-1>", lambda e, g=game_info: self._launch_game(g))

    def _on_hover(self, card, info, title, desc, entering):
        """Highlights the card when hovered."""
        bg_color = HOVER_BG if entering else PANEL_BG
        card.configure(bg=bg_color)
        info.configure(bg=bg_color)
        title.configure(bg=bg_color)
        desc.configure(bg=bg_color)

    def _launch_game(self, game_info):
        """Dynamically imports the requested game and runs it."""
        try:
            game_module = importlib.import_module(game_info["module"])
            GameClass = getattr(game_module, game_info["class"])
        except Exception as e:
            print(f"[Error] Could not load {game_info['name']}: {e}")
            return

        # Hide the hub window
        self.root.withdraw()

        # Create a new Toplevel window for the game
        game_window = tk.Toplevel(self.root)
        
        def on_close():
            game_window.destroy()
            self.root.deiconify()

        game_window.protocol("WM_DELETE_WINDOW", on_close)

        # Initialize the game inside the new window
        app = GameClass(game_window)

if __name__ == "__main__":
    root = tk.Tk()
    app = ArcadeHub(root)
    root.mainloop()