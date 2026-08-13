import tkinter as tk
import random
import math
import pygame
import os

# ---------------- CONFIGURATION ----------------
WIDTH, HEIGHT = 600, 600  # Larger window
GRID_SIZE = 20
base_speed = 100          # Lower number = faster
PARTICLE_COUNT = 15       # Particles per explosion

# COLORS (Neon / Cyberpunk Theme)
COLOR_BG = "#0d0d15"
COLOR_GRID = "#1a1a24"
COLOR_SNAKE_HEAD = "#00ffcc" # Cyan
COLOR_SNAKE_BODY = "#00bfa5" # Darker Cyan
COLOR_FOOD = "#ff0055"       # Neon Red/Pink
COLOR_OBSTACLE = "#ff9900"   # Neon Orange
COLOR_TEXT = "#ffffff"
COLOR_PARTICLE = ["#ff0055", "#ffcc00", "#00ffcc", "#ffffff"]

# POWER-UPS
POWERUPS = {
    "SHRINK": {"color": "#00ff00", "label": "Shrink Potion"},
    "MULTIPLIER": {"color": "#ffd700", "label": "2x Score"},
    "SLOWMO": {"color": "#0099ff", "label": "Time Freeze"}
}

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Snake Deluxe 🐍")
        self.root.resizable(False, False)

        # Canvas Setup
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # Audio Setup
        self.init_audio()

        # Game Variables
        self.snake = []
        self.direction = "Right"
        self.next_direction = "Right" # Buffer to prevent instant 180 turns
        self.score = 0
        self.high_score = 0
        self.running = False
        self.paused = False
        self.speed = base_speed
        
        # Game Objects
        self.food = None
        self.obstacles = [] # List of {'id': id, 'dx': speed_x, 'dy': speed_y}
        self.powerup = None # Active powerup on board
        self.active_effects = [] # Effects currently applied to snake (e.g. multiplier)
        self.particles = [] # List for particle effects

        # Bindings
        self.root.bind("<Key>", self.handle_input)
        
        # Show Menu
        self.draw_background_grid()
        self.show_menu()

    def init_audio(self):
        """Safely initialize audio so game doesn't crash if files are missing."""
        pygame.mixer.init()
        self.sounds = {}
        try:
            self.sounds["bg"] = pygame.mixer.Sound("sounds/snakebgsound.mp3")
            self.sounds["eat"] = pygame.mixer.Sound("sounds/eat.mp3")
            self.sounds["dead"] = pygame.mixer.Sound("sounds/dead.mp3")
            self.sounds["powerup"] = pygame.mixer.Sound("sounds/eat.mp3") # Reuse or add specific sound
            self.sounds["bg"].set_volume(0.3)
        except Exception as e:
            print(f"Audio Warning: Could not load sound files. {e}")
            # Create dummy lambda objects so code doesn't break
            dummy = type('obj', (object,), {'play': lambda self, *args: None, 'stop': lambda self: None})
            self.sounds = {k: dummy() for k in ["bg", "eat", "dead", "powerup"]}

    # ---------------- GRAPHICS & HELPERS ----------------

    def draw_background_grid(self):
        """Draws a subtle static grid."""
        for i in range(0, WIDTH, GRID_SIZE):
            self.canvas.create_line(i, 0, i, HEIGHT, fill=COLOR_GRID, tag="static_grid")
        for i in range(0, HEIGHT, GRID_SIZE):
            self.canvas.create_line(0, i, WIDTH, i, fill=COLOR_GRID, tag="static_grid")

    def create_particles(self, x, y, color):
        """Spawns an explosion of particles at x, y."""
        for _ in range(PARTICLE_COUNT):
            # Random velocity
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, 4)
            size = random.randint(2, 5)
            p_id = self.canvas.create_oval(x, y, x+size, y+size, fill=random.choice(COLOR_PARTICLE), width=0)
            self.particles.append({'id': p_id, 'vx': vx, 'vy': vy, 'life': 20}) # Life = frames

    def update_particles(self):
        """Physics engine for particles."""
        for p in self.particles[:]:
            self.canvas.move(p['id'], p['vx'], p['vy'])
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
                self.particles.remove(p)

    def draw_eyes(self, head_x, head_y):
        """Draws eyes that track the food location using math.atan2."""
        food_coords = self.canvas.coords(self.food)
        if not food_coords: return
        fx, fy = food_coords[0], food_coords[1]
        
        # Calculate angle to food
        angle = math.atan2(fy - head_y, fx - head_x)
        
        # Eye offsets based on angle
        eye_offset = 4
        pupil_offset = 2
        
        # Left Eye
        lx, ly = head_x + 6, head_y + 6
        self.canvas.create_oval(lx, ly, lx+8, ly+8, fill="white", tags="snake")
        self.canvas.create_oval(lx + pupil_offset*math.cos(angle) + 2, 
                                ly + pupil_offset*math.sin(angle) + 2, 
                                lx + pupil_offset*math.cos(angle) + 6, 
                                ly + pupil_offset*math.sin(angle) + 6, fill="black", tags="snake")

        # Right Eye
        rx, ry = head_x + 14 if self.direction in ["Up","Down"] else head_x + 6, head_y + 6
        # Adjusting strictly for visuals is complex, simplifying to "Tracking Eyes"
        # We just draw two eyes relative to head center
        center_x = head_x + GRID_SIZE/2
        center_y = head_y + GRID_SIZE/2
        
        # Draw eyes slightly offset towards direction
        eye_spread = 5
        
        # Clear specific eye logic for a simpler "Look at food" approach
        # Eye 1
        e1_x = center_x - eye_spread + (math.cos(angle) * 3)
        e1_y = center_y - eye_spread + (math.sin(angle) * 3)
        self.canvas.create_oval(e1_x-3, e1_y-3, e1_x+3, e1_y+3, fill="white", tags="snake")
        self.canvas.create_oval(e1_x + math.cos(angle)*1.5 -1, e1_y + math.sin(angle)*1.5 -1, 
                                e1_x + math.cos(angle)*1.5 +1, e1_y + math.sin(angle)*1.5 +1, fill="black", tags="snake")

        # Eye 2
        e2_x = center_x + eye_spread + (math.cos(angle) * 3)
        e2_y = center_y + eye_spread + (math.sin(angle) * 3) # Simple diagonal offset
        
        # Better: Perpendicular vector for eye separation
        perp_angle = angle + math.pi/2
        e1_x = center_x + math.cos(perp_angle) * 4 + math.cos(angle) * 2
        e1_y = center_y + math.sin(perp_angle) * 4 + math.sin(angle) * 2
        
        e2_x = center_x - math.cos(perp_angle) * 4 + math.cos(angle) * 2
        e2_y = center_y - math.sin(perp_angle) * 4 + math.sin(angle) * 2

        self.canvas.create_oval(e1_x-3, e1_y-3, e1_x+3, e1_y+3, fill="white", tags="snake")
        self.canvas.create_oval(e1_x-1 + math.cos(angle), e1_y-1 + math.sin(angle), e1_x+1 + math.cos(angle), e1_y+1 + math.sin(angle), fill="black", tags="snake")
        
        self.canvas.create_oval(e2_x-3, e2_y-3, e2_x+3, e2_y+3, fill="white", tags="snake")
        self.canvas.create_oval(e2_x-1 + math.cos(angle), e2_y-1 + math.sin(angle), e2_x+1 + math.cos(angle), e2_y+1 + math.sin(angle), fill="black", tags="snake")


    # ---------------- GAME LOGIC ----------------

    def start_game(self):
        self.running = True
        self.score = 0
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.direction = "Right"
        self.next_direction = "Right"
        self.obstacles = []
        self.active_effects = []
        self.speed = base_speed
        
        self.canvas.delete("all")
        self.draw_background_grid()
        self.spawn_food()
        self.spawn_obstacle(initial=True)
        
        self.sounds["bg"].play(-1)
        self.game_loop()

    def spawn_food(self):
        self.canvas.delete("food")
        x = random.randint(0, (WIDTH-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
        y = random.randint(0, (HEIGHT-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
        
        # Don't spawn on snake or obstacles
        while (x, y) in self.snake or self.check_obstacle_collision(x, y):
            x = random.randint(0, (WIDTH-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
            y = random.randint(0, (HEIGHT-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
            
        self.food = self.canvas.create_oval(x+2, y+2, x+GRID_SIZE-2, y+GRID_SIZE-2, 
                                            fill=COLOR_FOOD, outline=COLOR_FOOD, tags="food")
        
        # Chance to spawn powerup
        if random.random() < 0.2: # 20% chance
            self.spawn_powerup()

    def spawn_powerup(self):
        self.canvas.delete("powerup")
        p_type = random.choice(list(POWERUPS.keys()))
        x = random.randint(1, (WIDTH-GRID_SIZE)//GRID_SIZE - 1) * GRID_SIZE
        y = random.randint(1, (HEIGHT-GRID_SIZE)//GRID_SIZE - 1) * GRID_SIZE
        
        color = POWERUPS[p_type]["color"]
        # Draw a glowing square or star
        pid = self.canvas.create_rectangle(x+4, y+4, x+GRID_SIZE-4, y+GRID_SIZE-4, 
                                           fill=color, outline="white", width=2, tags="powerup")
        self.powerup = {'id': pid, 'type': p_type, 'x': x, 'y': y}

    def spawn_obstacle(self, initial=False):
        # Moving obstacles (Asteroids)
        if initial: count = 2
        else: count = 1
        
        for _ in range(count):
            x = random.randint(0, (WIDTH-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
            y = random.randint(0, (HEIGHT-GRID_SIZE)//GRID_SIZE) * GRID_SIZE
            # Random slow velocity
            dx = random.choice([-1, 0, 1]) * (GRID_SIZE / 5) 
            dy = random.choice([-1, 0, 1]) * (GRID_SIZE / 5)
            if dx == 0 and dy == 0: dx = GRID_SIZE / 5
            
            oid = self.canvas.create_rectangle(x, y, x+GRID_SIZE*2, y+GRID_SIZE*2, 
                                               fill=COLOR_OBSTACLE, outline="#444", stipple="gray50", tags="obstacle")
            self.obstacles.append({'id': oid, 'dx': dx, 'dy': dy, 'rect': [x, y, x+GRID_SIZE*2, y+GRID_SIZE*2]})

    def check_obstacle_collision(self, x, y):
        # Check against dynamic obstacles
        for obs in self.obstacles:
            ox1, oy1, ox2, oy2 = self.canvas.coords(obs['id'])
            # Simple AABB collision
            if (x < ox2 and x + GRID_SIZE > ox1 and y < oy2 and y + GRID_SIZE > oy1):
                return True
        return False

    def move_obstacles(self):
        for obs in self.obstacles:
            self.canvas.move(obs['id'], obs['dx'], obs['dy'])
            coords = self.canvas.coords(obs['id'])
            
            # Bounce logic
            if coords[0] <= 0 or coords[2] >= WIDTH:
                obs['dx'] *= -1
            if coords[1] <= 0 or coords[3] >= HEIGHT:
                obs['dy'] *= -1

    def apply_powerup(self, p_type):
        self.sounds["powerup"].play()
        self.create_particles(self.snake[0][0], self.snake[0][1], POWERUPS[p_type]['color'])
        
        # Show floating text
        self.canvas.create_text(WIDTH/2, HEIGHT/2, text=POWERUPS[p_type]['label'], 
                                fill=POWERUPS[p_type]['color'], font=("Arial", 24, "bold"), tags="temp_text")
        self.root.after(1000, lambda: self.canvas.delete("temp_text"))

        if p_type == "SHRINK":
            if len(self.snake) > 3:
                # Remove last 3 segments
                for _ in range(3):
                    if len(self.snake) > 3: self.snake.pop()
        elif p_type == "MULTIPLIER":
            self.active_effects.append("MULTIPLIER")
            # Remove effect after 10 seconds
            self.root.after(10000, lambda: self.active_effects.remove("MULTIPLIER") if "MULTIPLIER" in self.active_effects else None)
        elif p_type == "SLOWMO":
            self.speed = 150
            self.root.after(5000, lambda: setattr(self, 'speed', max(base_speed - (self.score * 2), 50)))

        self.canvas.delete("powerup")
        self.powerup = None

    def game_loop(self):
        if not self.running: return

        # 1. Update Direction
        self.direction = self.next_direction
        
        # 2. Move Snake Head
        head_x, head_y = self.snake[0]
        if self.direction == "Up": head_y -= GRID_SIZE
        elif self.direction == "Down": head_y += GRID_SIZE
        elif self.direction == "Left": head_x -= GRID_SIZE
        elif self.direction == "Right": head_x += GRID_SIZE
        
        new_head = (head_x, head_y)

        # 3. Collision Checks
        # Walls
        if head_x < 0 or head_x >= WIDTH or head_y < 0 or head_y >= HEIGHT:
            self.game_over()
            return
        # Self
        if new_head in self.snake:
            self.game_over()
            return
        # Obstacles
        if self.check_obstacle_collision(head_x, head_y):
            self.game_over()
            return

        self.snake.insert(0, new_head)

        # 4. Eating Food
        food_coords = self.canvas.coords(self.food)
        # Check proximity (since oval coords are complex, check grid align)
        if head_x == food_coords[0]-2 and head_y == food_coords[1]-2:
            self.sounds["eat"].play()
            points = 2 if "MULTIPLIER" in self.active_effects else 1
            self.score += points
            self.create_particles(head_x, head_y, COLOR_FOOD)
            self.spawn_food()
            
            # Speed up
            if self.speed > 50 and "SLOWMO" not in self.active_effects:
                self.speed -= 2
                
            # Add obstacle every 5 points
            if self.score % 5 == 0:
                self.spawn_obstacle()
        else:
            self.snake.pop()

        # 5. Eating Powerup
        if self.powerup:
            if head_x == self.powerup['x'] and head_y == self.powerup['y']:
                self.apply_powerup(self.powerup['type'])

        # 6. Render & Updates
        self.move_obstacles()
        self.draw_snake()
        self.update_particles()
        self.draw_hud()
        
        # Animate Food (Pulse)
        # Simple flicker effect by changing outline width slightly
        w = random.choice([1, 3])
        self.canvas.itemconfig(self.food, width=w, outline="white")

        self.root.after(self.speed, self.game_loop)

    def draw_snake(self):
        self.canvas.delete("snake")
        for i, (x, y) in enumerate(self.snake):
            # Gradient color logic
            if i == 0:
                color = COLOR_SNAKE_HEAD
                # Draw Eyes for head
                self.canvas.create_oval(x, y, x+GRID_SIZE, y+GRID_SIZE, fill=color, outline="", tags="snake")
                self.draw_eyes(x, y)
            else:
                # Fade color based on index
                shade = max(50, 255 - (i * 5))
                # Create hex color code manually for gradient green/cyan
                color = f"#00{shade:02x}{min(255, shade+50):02x}"
                self.canvas.create_oval(x+1, y+1, x+GRID_SIZE-1, y+GRID_SIZE-1, fill=color, outline="", tags="snake")

    def draw_hud(self):
        self.canvas.delete("hud")
        # Score
        self.canvas.create_text(60, 20, text=f"SCORE: {self.score}", fill="#fff", font=("Courier", 14, "bold"), tags="hud")
        # Multiplier Indicator
        if "MULTIPLIER" in self.active_effects:
             self.canvas.create_text(WIDTH-60, 20, text="2X ACTIVE", fill="#ffd700", font=("Courier", 14, "bold"), tags="hud")

    def show_menu(self):
        self.canvas.delete("all")
        self.draw_background_grid()
        self.canvas.create_text(WIDTH/2, HEIGHT/3, text="NEON SNAKE", fill=COLOR_SNAKE_HEAD, font=("Verdana", 40, "bold"), tags="menu")
        self.canvas.create_text(WIDTH/2, HEIGHT/3 + 50, text="DELUXE EDITION", fill=COLOR_FOOD, font=("Verdana", 20, "italic"), tags="menu")
        
        btn_text = "Press ENTER to Start"
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 20, text=btn_text, fill="white", font=("Arial", 14), tags="menu")
        
        self.canvas.create_text(WIDTH/2, HEIGHT - 50, text="Use Arrow Keys to Move", fill="#888", font=("Arial", 10), tags="menu")

    def game_over(self):
        self.running = False
        self.sounds["bg"].stop()
        self.sounds["dead"].play()
        
        # Semi-transparent overlay
        self.canvas.create_rectangle(50, HEIGHT/2 - 80, WIDTH-50, HEIGHT/2 + 80, fill="#111", outline=COLOR_FOOD, width=3)
        
        self.canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text="GAME OVER", fill=COLOR_FOOD, font=("Verdana", 30, "bold"))
        self.canvas.create_text(WIDTH/2, HEIGHT/2, text=f"Final Score: {self.score}", fill="white", font=("Arial", 18))
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 40, text="Press 'R' to Restart", fill="#aaa", font=("Arial", 14))

    def handle_input(self, event):
        key = event.keysym
        if not self.running:
            if key == "Return" or key == "r":
                self.start_game()
            elif key == "Escape":
                self.root.destroy()
            return

        if key == "Left" and self.direction != "Right":
            self.next_direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.next_direction = "Right"
        elif key == "Up" and self.direction != "Down":
            self.next_direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.next_direction = "Down"

# ---------------- MAIN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()