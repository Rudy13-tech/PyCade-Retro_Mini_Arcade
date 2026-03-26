import tkinter as tk
import importlib
import threading
import socket
import logging
from flask import Flask, request, render_template_string

# ── Retro Styling ─────────────────────────────────────────────────────────────
BG, PANEL_BG, GRID, GREEN, GREEN_DIM = "#060d06", "#040c04", "#0a140a", "#00ff77", "#224422"
TITLE_COL, TEXT_DIM, BORDER, HOVER_BG = "#00ff77", "#336633", "#00bb55", "#0a1f0a"

GAMES = [
    {"name": "GEO DASH", "desc": "Avoid spikes, land on platforms, survive!", "module": "Geodash", "class": "GeoDash"},
    {"name": "RETRO PONG", "desc": "Classic Pong against a bot. First to 7 wins.", "module": "pong_game", "class": "PongGame"},
    {"name": "RETRO SNAKE", "desc": "Eat food, grow longer, beat the high score.", "module": "snake_game", "class": "SnakeGame"},
    {"name": "BRICK BREAKER", "desc": "Smash all the blocks without dropping the ball.", "module": "brick_breaker", "class": "BrickBreaker"},
    {"name": "SPACE SHOOTER", "desc": "Defend the galaxy from falling enemy shapes.", "module": "space_shooter", "class": "SpaceShooter"}
]

# ── Mobile Controller Web App (HTML/CSS/JS) ───────────────────────────────────
CONTROLLER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Arcade Controller</title>
    <style>
        body { background-color: #060d06; color: #00ff77; font-family: 'Courier New', monospace; 
               display: flex; flex-direction: column; align-items: center; justify-content: center; 
               height: 100vh; margin: 0; overflow: hidden; user-select: none; }
        h2 { margin-bottom: 20px; text-shadow: 0 0 5px #00ff77; }
        .gamepad { display: flex; width: 100%; max-width: 600px; justify-content: space-around; align-items: center;}
        .dpad { display: grid; grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px 60px; gap: 5px; }
        .btn { background-color: #040c04; border: 2px solid #00bb55; border-radius: 10px; 
               color: #00ff77; font-size: 24px; font-weight: bold; display: flex; 
               align-items: center; justify-content: center; active-bg: #00ff77; touch-action: none; }
        .btn:active { background-color: #00ff77; color: #000; }
        .empty { visibility: hidden; }
        .action-btns { display: flex; gap: 20px; }
        .action-btn { width: 80px; height: 80px; border-radius: 50%; font-size: 20px; }
        .menu-btns { display: flex; gap: 10px; margin-top: 40px; }
        .menu-btn { padding: 10px 20px; font-size: 14px; border-radius: 5px; width: 80px;}
    </style>
</head>
<body>
    <h2>▓ VIRTUAL PAD ▓</h2>
    <div class="gamepad">
        <div class="dpad">
            <div class="empty"></div>
            <div class="btn" data-key="Up">W</div>
            <div class="empty"></div>
            <div class="btn" data-key="Left">A</div>
            <div class="btn" data-key="Down">S</div>
            <div class="btn" data-key="Right">D</div>
        </div>
        <div class="action-btns">
            <div class="btn action-btn" data-key="space">JUMP<br>(Spc)</div>
        </div>
    </div>
    <div class="menu-btns">
        <div class="btn menu-btn" data-key="r">RESET</div>
        <div class="btn menu-btn" data-key="Alt-Left">BACK</div>
    </div>

    <script>
        const buttons = document.querySelectorAll('.btn');
        
        function sendKey(key, state) {
            fetch('/input', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key, state: state })
            });
        }

        buttons.forEach(btn => {
            // Prevent zooming and scrolling when mashing buttons
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault(); 
                btn.style.backgroundColor = '#00ff77';
                btn.style.color = '#000';
                sendKey(btn.getAttribute('data-key'), 'press');
            }, {passive: false});

            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                btn.style.backgroundColor = '#040c04';
                btn.style.color = '#00ff77';
                sendKey(btn.getAttribute('data-key'), 'release');
            }, {passive: false});
        });
    </script>
</body>
</html>
"""

# ── Global App Reference for Flask ──
tk_app_instance = None

app = Flask(__name__)
# Silence Flask's default terminal spam
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    return render_template_string(CONTROLLER_HTML)

@app.route('/input', methods=['POST'])
def handle_input():
    data = request.json
    key = data.get('key')
    state = data.get('state')
    
    # Safely inject the keypress into the Tkinter main thread
    if tk_app_instance and tk_app_instance.root:
        if state == 'press':
            if key == "Alt-Left":
                tk_app_instance.root.after(0, tk_app_instance.go_back)
            else:
                tk_app_instance.root.after(0, lambda: tk_app_instance.root.event_generate(f"<KeyPress-{key}>"))
        elif state == 'release':
            if key != "Alt-Left":
                tk_app_instance.root.after(0, lambda: tk_app_instance.root.event_generate(f"<KeyRelease-{key}>"))
            
    return {"status": "success"}

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def get_local_ip():
    """Finds the local IP address of the laptop so the user can connect via phone."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# ── The Arcade Hub ────────────────────────────────────────────────────────────
class ArcadeHub:
    def __init__(self, root: tk.Tk):
        global tk_app_instance
        tk_app_instance = self
        self.root = root
        self.current_game_instance = None
        
        self.local_ip = get_local_ip()
        
        self.root.bind("<Alt-Left>", self.go_back)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))
        self.root.attributes("-fullscreen", True) 
        self.show_hub()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_hub(self):
        self.clear_window()
        self.root.title("▓ RETRO ARCADE HUB ▓")
        self.root.configure(bg=BG)

        header = tk.Frame(self.root, bg=PANEL_BG, pady=25)
        header.pack(fill=tk.X)
        tk.Label(header, text="▓ RETRO ARCADE HUB ▓", font=("Courier", 32, "bold"), fg=TITLE_COL, bg=PANEL_BG).pack()
        
        # Display the Controller URL here!
        url_text = f"PHONE CONTROLLER: http://{self.local_ip}:5000"
        tk.Label(header, text=url_text, font=("Courier", 14, "bold"), fg="#ffcc00", bg=PANEL_BG).pack(pady=(10, 5))
        tk.Label(header, text="PRESS ESC TO TOGGLE FULLSCREEN | SELECT A GAME", font=("Courier", 12), fg=TEXT_DIM, bg=PANEL_BG).pack(pady=(0, 0))
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        self.main_container = tk.Frame(self.root, bg=BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, pady=20)

        self.canvas = tk.Canvas(self.main_container, bg=BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=BG)

        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5))

        self.root.bind("<MouseWheel>", self._on_mousewheel)

        for game_info in GAMES:
            self._create_game_card(game_info)

    def _on_mousewheel(self, event):
        if not self.current_game_instance:
            if event.delta > 0: self.canvas.yview_scroll(-1, "units")
            elif event.delta < 0: self.canvas.yview_scroll(1, "units")

    def _create_game_card(self, game_info):
        border_frame = tk.Frame(self.list_frame, bg=BORDER, cursor="hand2")
        border_frame.pack(fill=tk.X, padx=150, pady=15)

        card = tk.Frame(border_frame, bg=PANEL_BG)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        info_frame = tk.Frame(card, bg=PANEL_BG)
        info_frame.pack(side=tk.LEFT, padx=25, pady=25)
        
        title = tk.Label(info_frame, text=f"▶ {game_info['name']}", font=("Courier", 20, "bold"), fg=GREEN, bg=PANEL_BG)
        title.pack(anchor="w")
        
        desc = tk.Label(info_frame, text=game_info['desc'], font=("Courier", 12), fg=TEXT_DIM, bg=PANEL_BG)
        desc.pack(anchor="w", pady=(8, 0))

        play_btn = tk.Label(card, text="PLAY", font=("Courier", 16, "bold"), fg=BG, bg=GREEN, padx=25, pady=10)
        play_btn.pack(side=tk.RIGHT, padx=30)

        for w in [border_frame, card, info_frame, title, desc, play_btn]:
            w.bind("<Enter>", lambda e, bf=border_frame: self._on_hover(bf, True))
            w.bind("<Leave>", lambda e, bf=border_frame: self._on_hover(bf, False))
            w.bind("<Button-1>", lambda e, g=game_info: self.launch_game(g))

    def _on_hover(self, border_frame, entering):
        color = TITLE_COL if entering else BORDER
        border_frame.configure(bg=color)

    def launch_game(self, game_info):
        self.clear_window()
        self.root.unbind("<MouseWheel>")
        
        nav = tk.Frame(self.root, bg="#003311", pady=8)
        nav.pack(fill=tk.X)
        back_btn = tk.Button(nav, text="🔙 BACK TO HUB (Alt + ←)", font=("Courier", 11, "bold"), fg=BG, bg=GREEN, cursor="hand2", relief=tk.FLAT, command=self.go_back)
        back_btn.pack(side=tk.LEFT, padx=20)

        try:
            game_module = importlib.import_module(game_info["module"])
            importlib.reload(game_module)
            GameClass = getattr(game_module, game_info["class"])
            self.current_game_instance = GameClass(self.root)
        except Exception as e:
            print(f"[Error] Could not load {game_info['name']}: {e}")
            self.show_hub()

    def go_back(self, event=None):
        if self.current_game_instance:
            if hasattr(self.current_game_instance, 'cleanup'): 
                self.current_game_instance.cleanup()
            
            for b in ["<KeyPress>", "<KeyRelease>", "<ButtonPress-1>", "<ButtonRelease-1>", "<Motion>"]: 
                self.root.unbind(b)
            
            self.current_game_instance = None
            
        self.show_hub()

if __name__ == "__main__":
    # Start the web server in the background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start the Arcade GUI
    root = tk.Tk()
    app = ArcadeHub(root)
    root.mainloop()
