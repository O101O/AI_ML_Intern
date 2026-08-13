from ursina import *
from random import randint

# 1. Setup the 3D Window
app = Ursina()
window.title = "3D Snake Game"
window.color = color.black
window.borderless = False 
window.fullscreen = False

# 2. Camera Setup (Isometric/Top-Down View)
camera.position = (0, 25, -25)
camera.rotation_x = 45

# 3. Game Settings
grid_size = 20
snake_speed = 0.15  # Lower is faster
last_move_time = 0
direction = (0, 0, 1) # Moving forward (z-axis)
game_running = True

# 4. Create Objects
# The ground
ground = Entity(model='plane', scale=(grid_size*2, 1, grid_size*2), color=color.dark_gray, texture='white_cube')

# The Snake (Head)
head = Entity(model='cube', color=color.green, position=(0, 0.5, 0), scale=0.9)
body = [] # List to store body segments

# The Food
food = Entity(model='sphere', color=color.red, position=(5, 0.5, 5), scale=0.9)

# Lighting
DirectionalLight(y=2, z=3, shadows=True)

# ---------------- FUNCTIONS ----------------

def new_food_position():
    """Places food at a random spot"""
    x = randint(-grid_size//2, grid_size//2)
    z = randint(-grid_size//2, grid_size//2)
    food.position = (x, 0.5, z)

def reset_game():
    global game_running, direction, body
    print("Game Over! Resetting...")
    head.position = (0, 0.5, 0)
    direction = (0, 0, 1)
    
    # Remove old body parts
    for b in body:
        destroy(b)
    body = []
    game_running = True

def update():
    global last_move_time, game_running
    
    if not game_running:
        return

    # Check inputs (WASD or Arrows)
    handle_input()

    # Move Snake on a timer (not every frame)
    if time.time() - last_move_time > snake_speed:
        move_snake()
        last_move_time = time.time()

def handle_input():
    global direction
    if held_keys['w'] or held_keys['up arrow']:    
        if direction != (0, 0, -1): direction = (0, 0, 1)
    if held_keys['s'] or held_keys['down arrow']:  
        if direction != (0, 0, 1): direction = (0, 0, -1)
    if held_keys['a'] or held_keys['left arrow']:  
        if direction != (1, 0, 0): direction = (-1, 0, 0)
    if held_keys['d'] or held_keys['right arrow']: 
        if direction != (-1, 0, 0): direction = (1, 0, 0)

def move_snake():
    global game_running

    # Calculate new position
    new_x = head.x + direction[0]
    new_z = head.z + direction[2]

    # 1. Create a new body segment at current head position
    segment = Entity(model='cube', color=color.lime, position=head.position, scale=0.9)
    body.insert(0, segment)

    # 2. Move Head
    head.position = (new_x, 0.5, new_z)

    # 3. Check Collision (Wall)
    if abs(head.x) > grid_size or abs(head.z) > grid_size:
        reset_game()
        return

    # 4. Check Collision (Self)
    # We check if the head is occupying the same space as any body part
    for segment in body:
        if segment.position == head.position:
            reset_game()
            return

    # 5. Check Food
    if head.x == food.x and head.z == food.z:
        new_food_position()
        # Make a sound (optional)
        Audio('assets/eat_sound.wav', autoplay=True, loop=False) if 'assets' in sys.path else None
    else:
        # If we didn't eat, remove the last tail segment
        if len(body) > 0:
            removed_segment = body.pop()
            destroy(removed_segment)

# Run the game
app.run()