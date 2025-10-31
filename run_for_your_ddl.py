import os, sys, random, pygame

# ------------------ Initialization ------------------
pygame.init()
WIDTH, HEIGHT = 400, 800
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Run for Your DDL - Collect Time!")
clock = pygame.time.Clock()

WHITE=(255,255,255); BLACK=(20,20,20); RED=(240,60,60); BLUE=(80,120,255); SKY=(200,220,255)
DARK=(40,40,40)

font_big    = pygame.font.Font(None, 72)
font_title  = pygame.font.Font(None, 56)
font_medium = pygame.font.Font(None, 40)
font_small  = pygame.font.Font(None, 28)

LANES_X = [WIDTH//6, WIDTH//2, WIDTH*5//6]
GROUND_Y = HEIGHT - 90

# ------------------ Score record file ------------------
SCORE_FILE = "scores.txt"

def read_scores():
    """Read all saved scores from the file safely."""
    scores = []
    try:
        # Create the file if it does not exist
        if not os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "w") as f:
                f.write("")
        with open(SCORE_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.isdigit():
                    scores.append(int(line))
        # Ensure all loaded scores are valid
        assert all(isinstance(s, int) and s >= 0 for s in scores), "Invalid score data detected!"
    except Exception as e:
        print(f"⚠️ Error reading score file: {e}")
        scores = []
    return scores

def write_score(new_score):
    """Append the latest score to the file."""
    try:
        with open(SCORE_FILE, "a") as f:
            f.write(str(new_score) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to save score: {e}")

def get_highest_score():
    """Return the highest recorded score."""
    scores = read_scores()
    return max(scores) if scores else 0

# ------------------ Image loader ------------------
def load_or_placeholder(name, size, color, alpha=True):
    """
    Load an image from the same directory. 
    If the file is missing, create a colored placeholder surface instead.
    """
    path = os.path.join(os.path.dirname(__file__), name)
    try:
        img = pygame.image.load(path)
        img = img.convert_alpha() if alpha else img.convert()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except:
        surf = pygame.Surface(size, pygame.SRCALPHA if alpha else 0)
        surf.fill(color)
        return surf

# ------------------ Asset setup ------------------
BACKGROUND = load_or_placeholder("background.jpg", (WIDTH, HEIGHT), SKY, alpha=False)
PLAYER_IMG = load_or_placeholder("player.png", (50, 120), BLUE, alpha=True)
TIME_SIZE  = (34, 34)
OBSTACLE_SIZE = (60, 60)
TIME_IMG   = load_or_placeholder("time.png", TIME_SIZE, (180,230,255), alpha=True)
OBSTACLE_IMG = load_or_placeholder("obstacle.png", OBSTACLE_SIZE, (220,50,50), alpha=True)

# ------------------ Player class ------------------
class Player(pygame.sprite.Sprite):
    """Player can move left and right between three lanes."""
    def __init__(self):
        super().__init__()
        self.image = PLAYER_IMG
        self.rect = self.image.get_rect(midbottom=(LANES_X[1], GROUND_Y))
        self.lane = 1
        self.target_x = LANES_X[self.lane]
        self.move_speed = 12

    def request_lane(self, dir_sign):
        """Move one lane left (-1) or right (+1)."""
        self.lane = max(0, min(2, self.lane + dir_sign))
        self.target_x = LANES_X[self.lane]

    def handle_actions(self, keydowns):
        """Handle one-time key presses for lane switching."""
        if keydowns.get(pygame.K_LEFT):
            self.request_lane(-1)
        elif keydowns.get(pygame.K_RIGHT):
            self.request_lane(+1)

    def update(self):
        """Smoothly move toward target lane center."""
        if abs(self.rect.centerx - self.target_x) > 2:
            dx = self.move_speed if self.target_x > self.rect.centerx else -self.move_speed
            self.rect.centerx += dx
        else:
            self.rect.centerx = self.target_x
        self.rect.bottom = GROUND_Y

# ------------------ Obstacles & Time objects ------------------
class Obstacle(pygame.sprite.Sprite):
    """Red obstacle blocks that end the game on collision."""
    def __init__(self, lane, speed):
        super().__init__()
        self.image = OBSTACLE_IMG
        self.rect = self.image.get_rect(midtop=(LANES_X[lane], -OBSTACLE_SIZE[1]))
        self.speed = speed
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT + 20:
            self.kill()

class Time(pygame.sprite.Sprite):
    """Blue time token that increases your score."""
    def __init__(self, lane, speed):
        super().__init__()
        self.image = TIME_IMG
        self.rect = self.image.get_rect(midtop=(LANES_X[lane], -TIME_SIZE[1]))
        self.speed = speed
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT + 20:
            self.kill()

# ------------------ Random spawning ------------------
def spawn(objects, times, speed):
    """Randomly generate new time tokens and obstacles."""
    if random.randint(1, 8) == 1:
        times.add(Time(random.randint(0,2), speed))
    if random.randint(1, 30) == 1:
        objects.add(Obstacle(random.randint(0,2), speed + 2))

# ------------------ World reset ------------------
def reset_world():
    """Reset all game entities and parameters."""
    player = Player()
    g_player = pygame.sprite.GroupSingle(player)
    g_obstacle = pygame.sprite.Group()
    g_time = pygame.sprite.Group()
    score = 0
    speed_base = 7
    return player, g_player, g_obstacle, g_time, score, speed_base

# ------------------ UI Button renderer ------------------
def draw_button(text, center, size=(180,56)):
    """Draw a simple clickable rounded button."""
    rect = pygame.Rect(0,0,*size)
    rect.center = center
    mx,my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx,my)
    body = (255,255,255) if hover else (240,240,240)
    pygame.draw.rect(SCREEN, body, rect, border_radius=10)
    pygame.draw.rect(SCREEN, (60,60,60), rect, 2, border_radius=10)
    label = font_medium.render(text, True, DARK)
    SCREEN.blit(label, (rect.centerx-label.get_width()//2, rect.centery-label.get_height()//2))
    return rect

# ------------------ Main game loop ------------------
def main():
    highest = get_highest_score()
    player, g_player, g_ob, g_time, score, speed = reset_world()
    state = "PLAY"
    running = True
    victory_shown = False

    while running:
        keydowns = {}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if state == "PLAY" and event.type == pygame.KEYDOWN:
                keydowns[event.key] = True
            if state == "OVER":
                # Handle clicks or keyboard inputs in Game Over state
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_c.collidepoint(event.pos):
                        player, g_player, g_ob, g_time, score, speed = reset_world()
                        state = "PLAY"
                        victory_shown = False
                    if btn_q.collidepoint(event.pos):
                        running = False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_c, pygame.K_RETURN, pygame.K_SPACE):
                        player, g_player, g_ob, g_time, score, speed = reset_world()
                        state = "PLAY"
                        victory_shown = False
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False

        SCREEN.blit(BACKGROUND, (0,0))

        if state == "PLAY":
            # --- Core gameplay ---
            player.handle_actions(keydowns)
            player.update()
            spawn(g_ob, g_time, speed)
            g_ob.update()
            g_time.update()

            # Collision with obstacles → Game Over
            if pygame.sprite.spritecollide(player, g_ob, False):
                write_score(score)
                state = "OVER"
                highest = get_highest_score()

            # Collision with time tokens → +1 score
            for _ in pygame.sprite.spritecollide(player, g_time, True):
                score += 1

            # Reaching 88 time units → victory message (game continues)
            if score >= 88 and not victory_shown:
                victory_shown = True
                victory_time = pygame.time.get_ticks()

            # Draw sprites
            g_time.draw(SCREEN)
            g_ob.draw(SCREEN)
            g_player.draw(SCREEN)

            # HUD display
            score_txt = font_small.render(f"Time Collected: {score}", True, BLACK)
            SCREEN.blit(score_txt, (10,10))
            high_txt = font_small.render(f"Best Record: {highest}", True, BLACK)
            SCREEN.blit(high_txt, (10,40))

            # Show victory banner for 4 seconds
            if victory_shown:
                elapsed = (pygame.time.get_ticks() - victory_time) / 1000
                if elapsed < 4:
                    alpha = min(255, int(255 * (1 - elapsed / 4)))
                    msg = font_medium.render("✅ You finished your DDL on time! ✅", True, BLUE)
                    overlay = pygame.Surface(msg.get_size(), pygame.SRCALPHA)
                    overlay.blit(msg, (0,0))
                    overlay.set_alpha(alpha)
                    SCREEN.blit(overlay, (WIDTH//2 - msg.get_width()//2, 100))

        else:
            # --- Game Over screen ---
            overlay = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            SCREEN.blit(overlay, (0,0))
            title = font_title.render("GAME OVER", True, RED)
            SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 160))
            btn_c = draw_button("Continue", (WIDTH//2, HEIGHT//2 - 40))
            btn_q = draw_button("Quit", (WIDTH//2, HEIGHT//2 + 40))
            end_txt = font_small.render(f"Time Collected: {score} | Best: {highest}", True, WHITE)
            SCREEN.blit(end_txt,(WIDTH//2 - end_txt.get_width()//2, HEIGHT//2 - 100))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
