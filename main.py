import pygame
import math
import heapq
import random
import sys
import time
pygame.mixer.init()
shot_sound = pygame.mixer.Sound("shot.mp3")
gun_sound = pygame.mixer.Sound("gun.mp3")
# Game Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
MAX_SCORE = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
# Game Mechanics
TANK_SIZE = 40
BULLET_RADIUS = 5
BULLET_SPEED = 3
VELOCITY = 3
ROTATE_SPEED = 5
SHOOT_COOLDOWN = 0.5
class Enemy:
    """
    Lớp Enemy đại diện cho đối tượng kẻ địch trong trò chơi.
    
    Thuộc tính:
        image_original: Hình ảnh gốc của kẻ địch
        image: Hình ảnh sau khi xoay
        rect: Hình chữ nhật bao quanh kẻ địch
        grid: Lưới dùng để di chuyển
        cell_size: Kích thước mỗi ô trong lưới
        angle: Góc quay hiện tại của kẻ địch
        speed: Tốc độ di chuyển của kẻ địch
        path: Đường đi tới mục tiêu
        grid_x, grid_y: Vị trí trong lưới
        target_player: Người chơi đang được nhắm tới
        detection_range: Phạm vi phát hiện người chơi
        last_attack_time: Thời điểm tấn công gần nhất
        target_x, target_y: Vị trí đích
        moving: Trạng thái đang di chuyển
        move_timer: Bộ đếm thời gian di chuyển
        path_update_timer: Bộ đếm thời gian cập nhật đường đi
    """
    def __init__(self, x, y, grid, cell_size=53):
          
        self.image_original = pygame.Surface((10, 10), pygame.SRCALPHA)
        self.image_original.fill(RED)
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.grid = grid
        self.cell_size = cell_size
        self.angle = 0
        self.speed = 1
        self.path = []
        self.grid_x = x // cell_size
        self.grid_y = y // cell_size
      
        self.target_player = None
        self.detection_range = 350  # Phạm vi phát hiện người chơi
        self.last_attack_time = 0
        
        # Smooth movement
        self.target_x = x
        self.target_y = y
        self.moving = False
        self.move_timer = 0
        self.path_update_timer = 0

    def draw(self, screen): 
        """
        Vẽ kẻ địch lên màn hình.
        
        Tham số:
            screen: Đối tượng Surface của pygame để vẽ lên
        """
        screen.blit(self.image, self.rect)

    def heuristic(self, a, b): 
        """
        Tính toán hàm heuristic cho thuật toán A* dựa trên khoảng cách.
        
        Tham số:
            a: Điểm bắt đầu (x, y)
            b: Điểm kết thúc (x, y)
            
        Trả về:
            Khoảng cách Euclid giữa hai điểm
        """
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def astar(self, start, end):
        """
        Thuật toán A* để tìm đường đi từ điểm bắt đầu đến điểm kết thúc.
        
        Tham số:
            start: Điểm bắt đầu (x, y)
            end: Điểm kết thúc (x, y)
            
        Trả về:
            Danh sách các điểm tạo thành đường đi
        """
        heap = []
        heapq.heappush(heap, (0, start))
        came_from = {}
        cost_so_far = {start: 0}
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]

        while heap:
            _, current = heapq.heappop(heap)
            if current == end:
                break

            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if (0 <= neighbor[0] < len(self.grid[0]) and
                    0 <= neighbor[1] < len(self.grid) and
                    self.grid[neighbor[1]][neighbor[0]] == 0):
                    
                    step_cost = math.hypot(dx, dy)
                    new_cost = cost_so_far[current] + step_cost

                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + self.heuristic(end, neighbor)
                        heapq.heappush(heap, (priority, neighbor))
                        came_from[neighbor] = current

        # Xây dựng đường đi
        path = []
        node = end
        while node != start:
            path.append(node)
            node = came_from.get(node)
            if node is None:
                return []
        path.reverse()
        return path
    def check_bullet_collision(self, bullet):
        """
        Kiểm tra va chạm giữa kẻ địch và đạn.
        
        Tham số:
            bullet: Đối tượng đạn cần kiểm tra
            
        Trả về:
            True nếu có va chạm, ngược lại False
        """
        bullet_rect = bullet.get_rect()
        return self.rect.colliderect(bullet_rect)
    def find_nearest_player(self, players):
        """
        Tìm người chơi gần nhất trong phạm vi phát hiện.
        
        Tham số:
            players: Danh sách người chơi
            
        Trả về:
            Đối tượng người chơi gần nhất hoặc None nếu không có ai trong tầm
        """
        nearest_player = None
        min_distance = self.detection_range
        
        for player in players:
            distance = math.hypot(
                self.rect.centerx - player.rect.centerx,
                self.rect.centery - player.rect.centery
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_player = player
                
        return nearest_player

    def update_target_and_path(self, players):
        """
        Cập nhật mục tiêu và đường đi tới người chơi gần nhất.
        
        Tham số:
            players: Danh sách người chơi
        """
        self.target_player = self.find_nearest_player(players)
        
        if self.target_player:
            target_x, target_y = self.target_player.rect.center
            target_cell = (target_x // self.cell_size, target_y // self.cell_size)
            start_cell = (self.grid_x, self.grid_y)
            
            # Chỉ tính toán lại đường đi nếu mục tiêu đã thay đổi đáng kể
            self.path = self.astar(start_cell, target_cell)

    def move_along_path(self):
        """
        Di chuyển kẻ địch theo đường đi đã tính toán.
        """
        if not self.moving and self.path:
            # Bắt đầu di chuyển tới ô tiếp theo
            next_cell = self.path.pop(0)
            self.grid_x, self.grid_y = next_cell
            self.target_x = self.grid_x * self.cell_size + self.cell_size // 2
            self.target_y = self.grid_y * self.cell_size + self.cell_size // 2
            self.moving = True
            
            # Xoay tank theo hướng di chuyển
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            if dx != 0 or dy != 0:
                self.angle = math.atan2(-dy, dx) * 180 / math.pi            
                # Xoay image như code gốc của bạn
                self.image = pygame.transform.rotozoom(self.image_original, self.angle, 1.0)
                self.rect = self.image.get_rect(center=self.rect.center)

        if self.moving:
            # Di chuyển mượt tới vị trí mục tiêu
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = math.hypot(dx, dy)
            
            if distance > 0:
                # Chưa tới mục tiêu, tiếp tục di chuyển
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.rect.centerx += move_x
                self.rect.centery += move_y
            else:
                # Đã tới mục tiêu
                self.rect.center = (self.target_x, self.target_y)
                self.moving = False
    
    def check_collision_with_players(self, players):
        """
        Kiểm tra va chạm với người chơi và gây sát thương.
        
        Tham số:
            players: Danh sách người chơi
            
        Trả về:
            True nếu có va chạm, ngược lại False
        """
        current_time = pygame.time.get_ticks()
        
        for player in players:
            other_player = players[1] if player == players[0] else players[0]
            if self.rect.colliderect(player.rect):
                    other_player.score +=1
                    self.last_attack_time = current_time
                    return True
        return False

    def update(self, players):
        """
        Cập nhật trạng thái của kẻ địch.
        
        Tham số:
            players: Danh sách người chơi
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.path_update_timer > 400:
            self.update_target_and_path(players)
            self.path_update_timer = current_time
        
        # Di chuyển theo đường đi
        self.move_along_path()
        
        # Kiểm tra va chạm với người chơi
        self.check_collision_with_players(players)

class EnemyManager:
    """
    Lớp quản lý kẻ địch trong trò chơi.
    
    Thuộc tính:
        grid: Lưới dùng để di chuyển
        cell_size: Kích thước mỗi ô trong lưới
        enemies: Danh sách các kẻ địch đang hoạt động
        spawn_timer: Bộ đếm thời gian sinh kẻ địch
        spawn_interval: Khoảng thời gian giữa các lần sinh kẻ địch
        max_enemies: Số lượng kẻ địch tối đa
    """
    def __init__(self, grid, cell_size=53):
        self.grid = grid
        self.cell_size = cell_size
        self.enemies = []
        # Spawn settings
        self.spawn_timer = 0
        self.spawn_interval = 5000  # Khoảng thời gian giữa các lần sinh kẻ địch
        self.max_enemies = 10
    def check_bullets_hit(self, players):
        """
        Kiểm tra đạn bắn trúng kẻ địch.
        
        Tham số:
            players: Danh sách người chơi
            
        Trả về:
            True nếu có va chạm, ngược lại False
        """
        for enemy in self.enemies[:]: 
            for player in players:
                for bullet in player.bullets[:]:  # Duyệt qua đạn
                    if enemy.check_bullet_collision(bullet):
                        if bullet in player.bullets:
                            player.bullets.remove(bullet)
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        player.score+=1
                        shot_sound.play()
                        return True  # Có va chạm với bullet

                # Kiểm tra va chạm với người chơi
                if enemy in self.enemies and enemy.check_collision_with_players(players):
                    self.enemies.remove(enemy)
                    shot_sound.play()
                    return True
        return False
    def find_spawn_position(self, players=None, min_distance=100):
        """
        Tìm vị trí sinh kẻ địch ngẫu nhiên xa người chơi.
        
        Tham số:
            players: Danh sách người chơi
            min_distance: Khoảng cách tối thiểu với người chơi
            
        Trả về:
            Tọa độ (x, y) để sinh kẻ địch hoặc None nếu không tìm được
        """
        empty_cells = []
        
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] == 0:  # Ô trống
                    cell_x = x * self.cell_size + self.cell_size // 2
                    cell_y = y * self.cell_size + self.cell_size // 2
                    
                    # Kiểm tra khoảng cách với players
                    if players:
                        far_enough = True
                        for player in players:
                            distance = math.hypot(
                                cell_x - player.rect.centerx,
                                cell_y - player.rect.centery
                            )
                            if distance < min_distance:
                                far_enough = False
                                break
                        
                        if far_enough:
                            empty_cells.append((cell_x, cell_y))
                    else:
                        empty_cells.append((cell_x, cell_y))
        
        if empty_cells:
            return random.choice(empty_cells)
        
        # Fallback: spawn ở vị trí bất kỳ
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] == 0:
                    cell_x = x * self.cell_size + self.cell_size // 2
                    cell_y = y * self.cell_size + self.cell_size // 2
                    return cell_x, cell_y
        
        return None
    
    def spawn_enemy(self, players):
        """
        Sinh kẻ địch mới.
        
        Tham số:
            players: Danh sách người chơi
        """
        if len(self.enemies) >= self.max_enemies:
            return
        
        spawn_pos = self.find_spawn_position(players)
        if spawn_pos:
            spawn_x, spawn_y = spawn_pos
            new_enemy = Enemy(spawn_x, spawn_y, self.grid, self.cell_size)
            self.enemies.append(new_enemy)
    
    def remove_enemy(self, enemy):
        """
        Xóa kẻ địch khỏi danh sách.
        
        Tham số:
            enemy: Đối tượng kẻ địch cần xóa
        """
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def update(self, players):
        """
        Cập nhật trạng thái của tất cả kẻ địch.
        
        Tham số:
            players: Danh sách người chơi
        """
        current_time = pygame.time.get_ticks()
        
        # Kiểm tra va chạm giữa đạn và enemy
        self.check_bullets_hit(players)
        # Auto spawn
        if current_time - self.spawn_timer >= self.spawn_interval:
            self.spawn_enemy(players)
            self.spawn_timer = current_time
        
        # Update tất cả enemies
        for enemy in self.enemies[:]:  # Sử dụng slice để tránh lỗi khi xóa
            enemy.update(players)
    
    def draw(self, screen):
        """
        Vẽ tất cả kẻ địch lên màn hình.
        
        Tham số:
            screen: Đối tượng Surface của pygame để vẽ lên
        """
        for enemy in self.enemies:
            enemy.draw(screen) 
    def clear_all_enemies(self):
        """
        Xóa tất cả kẻ địch.
        """
        self.enemies.clear()    
class Bullet:
    """
    Lớp Bullet đại diện cho đạn trong trò chơi.
    
    Thuộc tính:
        x, y: Tọa độ hiện tại của đạn
        dx, dy: Vector hướng đạn
        creation_time: Thời điểm tạo đạn
        lifetime: Thời gian tồn tại tối đa của đạn
    """
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.creation_time = time.time()
        self.lifetime = 5.0

    def move(self):
        """
        Di chuyển đạn theo hướng và tốc độ đã định.
        """
        self.x += self.dx * BULLET_SPEED
        self.y += self.dy * BULLET_SPEED

    def get_rect(self):
        """
        Lấy hình chữ nhật bao quanh đạn.
        
        Trả về:
            Đối tượng pygame.Rect
        """
        return pygame.Rect(
            self.x - BULLET_RADIUS, 
            self.y - BULLET_RADIUS, 
            BULLET_RADIUS * 1, 
            BULLET_RADIUS * 1
        )

    def is_off_screen(self):
        """
        Kiểm tra đạn đã ra khỏi màn hình chưa.
        
        Trả về:
            True nếu đạn đã ra khỏi màn hình, ngược lại False
        """
        return not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT)

    def is_expired(self, current_time):
        """
        Kiểm tra đạn đã hết thời gian tồn tại chưa.
        
        Tham số:
            current_time: Thời gian hiện tại
            
        Trả về:
            True nếu đạn đã hết thời gian tồn tại, ngược lại False
        """
        return current_time - self.creation_time > self.lifetime

    def bounce(self, wall_rect):
        """
        Xử lý đạn nảy khi va chạm với tường.
        
        Tham số:
            wall_rect: Hình chữ nhật của tường
        """
        # Xác định va chạm và đổi hướng đạn
        bullet_rect = self.get_rect()
        
        # Va chạm theo trục x
        if self.dx > 0 and bullet_rect.right >= wall_rect.left and bullet_rect.left < wall_rect.left:
            self.x = wall_rect.left - BULLET_RADIUS
            self.dx *= -1
        elif self.dx < 0 and bullet_rect.left <= wall_rect.right and bullet_rect.right > wall_rect.right:
            self.x = wall_rect.right + BULLET_RADIUS
            self.dx *= -1
        
        # Va chạm theo trục y
        if self.dy > 0 and bullet_rect.bottom >= wall_rect.top and bullet_rect.top < wall_rect.top:
            self.y = wall_rect.top - BULLET_RADIUS
            self.dy *= -1
        elif self.dy < 0 and bullet_rect.top <= wall_rect.bottom and bullet_rect.bottom > wall_rect.bottom:
            self.y = wall_rect.bottom + BULLET_RADIUS
            self.dy *= -1
        
        # Thêm nhiễu nhỏ để tránh kẹt
        self.dx += random.uniform(-0.05, 0.05)
        self.dy += random.uniform(-0.05, 0.05)
        
        # Chuẩn hóa vector tốc độ
        magnitude = math.sqrt(self.dx * self.dx + self.dy * self.dy)
        self.dx /= magnitude
        self.dy /= magnitude
class Wall:
    def __init__(self, x, y, width, height, color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, window):
        pygame.draw.rect(window, self.color, self.rect)

    def generate_maze_walls(grid_width, grid_height):
        walls = []
        grid = [[1 for _ in range(grid_width)] for _ in range(grid_height)]

        def recursive_backtrack(x, y):
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                
                if (0 < new_x < grid_width - 1 and 
                    0 < new_y < grid_height - 1 and 
                    grid[new_y][new_x] == 1):
                    grid[new_y][new_x] = 0
                    grid[y + dy // 2][x + dx // 2] = 0
                    
                    recursive_backtrack(new_x, new_y)

        # Bắt đầu sinh mê cung
        grid[1][1] = 0  # Điểm bắt đầu
        recursive_backtrack(1, 1)

        wall_width = WIDTH / grid_width + 1  # Thêm 1 pixel để chắc chắn không có khoảng trống
        wall_height = HEIGHT / grid_height + 1
        # Tạo tường bao quanh
        walls.extend([
            Wall(0, 0, WIDTH, 10),           # Trên
            Wall(0, HEIGHT-10, WIDTH, 10),   # Dưới
            Wall(0, 0, 10, HEIGHT),          # Trái
            Wall(WIDTH-10, 0, 10, HEIGHT)    # Phải
        ])
        for row in range(grid_height):
            for col in range(grid_width):
                if grid[row][col] == 1:
                    wall_x = col * (WIDTH // grid_width)
                    wall_y = row * (HEIGHT // grid_height)
                    wall_w = WIDTH // grid_width
                    wall_h = HEIGHT // grid_height
                    walls.append(Wall(wall_x, wall_y, wall_w, wall_h))

        # Tạo các điểm spawn và đảm bảo không có tường ở gần điểm spawn
        spawn_points=[]
        for i in range(2):
            spawn_points.append((random.randint(50,WIDTH-50),
                                 random.randint(50,HEIGHT-50)))

        # Tạo vùng an toàn xung quanh điểm spawn (gấp đôi kích thước xe tăng)
        safe_zones = [
            pygame.Rect(p[0] - TANK_SIZE*2, p[1] - TANK_SIZE*2, TANK_SIZE*2, TANK_SIZE*2)
            for p in spawn_points
        ]

        # Loại bỏ tường tại và xung quanh điểm spawn
        # walls = [wall for wall in walls if not any(safe_zone.colliderect(wall.rect) for safe_zone in safe_zones)]

        return walls, spawn_points,grid

class Tank:
    """
    Đại diện cho một xe tăng trong trò chơi Tank Battle.
    
    Class này quản lý các chức năng chính của xe tăng như di chuyển, xoay, bắn đạn và 
    kiểm tra va chạm với các vật thể khác trong trò chơi.
    
    Thuộc tính:
        image_original (pygame.Surface): Hình ảnh gốc của xe tăng.
        image (pygame.Surface): Hình ảnh hiện tại của xe tăng (đã xoay).
        rect (pygame.Rect): Hình chữ nhật biểu diễn vị trí và kích thước của xe tăng.
        controls (dict): Các phím điều khiển của xe tăng.
        bullets (list): Danh sách các viên đạn hiện có của xe tăng.
        score (int): Điểm số hiện tại của xe tăng.
        last_shot (float): Thời điểm bắn viên đạn cuối cùng.
        angle (float): Góc xoay hiện tại của xe tăng (0 là hướng lên trên).
        max_bullets (int): Số lượng đạn tối đa có thể bắn cùng lúc.
        color (tuple): Màu sắc của xe tăng.
        direction (int): Hướng di chuyển của xe tăng (0 là hướng lên trên).
    """
    def __init__(self, x, y, color, controls):
        """
        Khởi tạo một xe tăng mới.
        
        Tham số:
            x (int): Tọa độ x ban đầu của xe tăng.
            y (int): Tọa độ y ban đầu của xe tăng.
            color (tuple): Màu sắc của xe tăng, quyết định hình ảnh được sử dụng.
            controls (dict): Từ điển chứa phím điều khiển cho xe tăng 
                             (lên, xuống, trái, phải, bắn).
        """
        if color == RED:
            self.image_original = pygame.image.load('tank1.png').convert_alpha()
        else :
            self.image_original = pygame.image.load('tank2.png').convert_alpha()
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.controls = controls
        self.bullets = []
        self.score = 0
        self.last_shot = 0
        self.angle = 0  # Góc quay (0 là hướng lên trên)
        self.max_bullets = 3
        self.color = color
        self.direction = 0  # Hướng di chuyển (0 là hướng lên trên)

    def draw(self, window):
        """
        Vẽ xe tăng và các viên đạn của nó lên cửa sổ trò chơi.
        
        Phương thức này xoay hình ảnh xe tăng theo góc hiện tại, vẽ nòng súng
        và hiển thị tất cả các viên đạn hiện có của xe tăng.
        
        Tham số:
            window (pygame.Surface): Cửa sổ nơi xe tăng sẽ được vẽ.
        """
        # Xoay xe tăng theo góc hiện tại
        self.image = pygame.transform.rotate(self.image_original, +self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        
        # Vẽ xe tăng đã xoay
        window.blit(self.image, self.rect)
        
        # Vẽ nòng súng theo góc hiện tại
        gun_length = 15
        end_x = self.rect.centerx + gun_length * math.cos(math.radians(self.angle))
        end_y = self.rect.centery - gun_length * math.sin(math.radians(self.angle))
        pygame.draw.line(window, BLACK, 
                         (self.rect.centerx, self.rect.centery), 
                         (end_x, end_y), 3)
        
        # Vẽ đạn
        for bullet in self.bullets:
            pygame.draw.circle(window, BLACK, (int(bullet.x), int(bullet.y)), BULLET_RADIUS)

    def move(self, keys_pressed, walls, other_tank):
        """
        Di chuyển xe tăng dựa trên phím được nhấn và xử lý va chạm.
        
        Phương thức này xử lý xoay xe tăng, tính toán vector di chuyển và kiểm tra
        va chạm với tường và xe tăng khác trước khi thực hiện di chuyển.
        
        Tham số:
            keys_pressed (pygame.key.ScancodeWrapper): Trạng thái hiện tại của bàn phím.
            walls (list): Danh sách các bức tường trong trò chơi.
            other_tank (Tank): Xe tăng khác để kiểm tra va chạm.
        """
        # Xoay xe
        if keys_pressed[self.controls["left"]]:
            self.angle += ROTATE_SPEED
        if keys_pressed[self.controls["right"]]:
            self.angle -= ROTATE_SPEED

        # Tính toán vector di chuyển
        movement_vector = pygame.math.Vector2(0, 0)
        if keys_pressed[self.controls["up"]]:
            movement_vector.from_polar((VELOCITY, -self.angle))
        elif keys_pressed[self.controls["down"]]:
            movement_vector.from_polar((VELOCITY, -self.angle + 180))

        dx, dy = movement_vector.x, movement_vector.y

        # Di chuyển với kiểm tra va chạm
        if dx != 0 or dy != 0:
            # Di chuyển theo x
            temp_rect = self.rect.copy()
            temp_rect.x += dx
            collision_x = False
            
            for wall in walls:
                if temp_rect.colliderect(wall.rect):
                    dx = 0
                    collision_x = True
                    break
                    
            if temp_rect.colliderect(other_tank.rect):
                dx = 0
                collision_x = True
            
            self.rect.x += dx

            # Di chuyển theo y
            temp_rect = self.rect.copy()
            temp_rect.y += dy
            collision_y = False
            
            for wall in walls:
                if temp_rect.colliderect(wall.rect):
                    dy = 0
                    collision_y = True
                    break
                    
            if temp_rect.colliderect(other_tank.rect):
                dy = 0
                collision_y = True
            
            self.rect.y += dy

    def shoot(self, current_time,shoot_sound):
        """
        Bắn đạn từ xe tăng nếu thỏa mãn điều kiện.
        
        Phương thức này tạo một viên đạn mới từ vị trí hiện tại của xe tăng
        theo hướng hiện tại, nếu chưa đạt giới hạn số lượng đạn tối đa và
        thời gian hồi đã đủ.
        
        Tham số:
            current_time (float): Thời gian hiện tại để kiểm tra thời gian hồi.
            shoot_sound (pygame.mixer.Sound): Âm thanh khi bắn đạn.
            
        Trả về:
            bool: True nếu bắn đạn thành công, False nếu không.
        """
        if current_time - self.last_shot < SHOOT_COOLDOWN:
            return False
        
        if len(self.bullets) >= self.max_bullets:
            return False
            
        # Tính hướng đạn theo hướng xe tăng
        dx = math.cos(math.radians(self.angle))
        dy = -math.sin(math.radians(self.angle))
        
        # Vị trí bắn đạn (từ phía trước xe tăng)
        front_x = self.rect.centerx + (TANK_SIZE//1.5) * dx
        front_y = self.rect.centery + (TANK_SIZE//1.5) * dy
        
        self.bullets.append(Bullet(front_x, front_y, dx, dy))
        shoot_sound.play()
        self.last_shot = current_time
        
        return True
    
    def set_position(self, x, y):
        self.rect.center = (x, y)

def draw_start_screen(window, font):
    """Thiết lập màn hình bắt đầu"""
    window.fill(WHITE)
    background_image = pygame.image.load("tank_battle.png")
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
    window.blit(background_image, (0, 0))   
    pygame.display.update()
def find_valid_spawn_position(spawn_point, walls, other_tank=None):
    """Tìm vị trí spawn hợp lệ gần điểm spawn ban đầu"""
    x, y = spawn_point
    
    # Tạo một hình chữ nhật tương ứng với kích thước xe tăng
    tank_rect = pygame.Rect(0, 0, TANK_SIZE, TANK_SIZE)
    tank_rect.center = (x, y)
    
    # Kiểm tra xem vị trí ban đầu có hợp lệ không
    is_valid = True
    for wall in walls:
        if tank_rect.colliderect(wall.rect):
            is_valid = False
            break
    
    if other_tank and tank_rect.colliderect(other_tank.rect):
        is_valid = False
    
    if is_valid:
        return x, y
    
    # Nếu vị trí ban đầu không hợp lệ, tìm vị trí gần đó
    search_radius = TANK_SIZE
    max_search_radius = 150  # Giới hạn phạm vi tìm kiếm
    
    while search_radius <= max_search_radius:
        # Thử các vị trí xung quanh theo hình tròn
        for angle in range(0, 360, 20):  # Mỗi 20 độ
            rad = math.radians(angle)
            test_x = x + search_radius * math.cos(rad)
            test_y = y + search_radius * math.sin(rad)
            
            # Đảm bảo vị trí nằm trong màn hình
            if test_x < TANK_SIZE or test_x > WIDTH - TANK_SIZE or test_y < TANK_SIZE or test_y > HEIGHT - TANK_SIZE:
                continue
                
            tank_rect.center = (test_x, test_y)
            
            # Kiểm tra va chạm
            is_valid = True
            for wall in walls:
                if tank_rect.colliderect(wall.rect):
                    is_valid = False
                    break
            
            if other_tank and tank_rect.colliderect(other_tank.rect):
                is_valid = False
            
            if is_valid:
                return test_x, test_y
        
        search_radius += TANK_SIZE
    
    # Nếu không tìm thấy vị trí hợp lệ, trả về vị trí mặc định an toàn
    safe_positions = [(WIDTH // 4, HEIGHT // 4), (WIDTH * 3 // 4, HEIGHT * 3 // 4)]
    return random.choice(safe_positions)

def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tank Battle")
    clock = pygame.time.Clock()
    # Khởi tạo font
    try:
        font = pygame.font.SysFont("comicsans", 36)
    except:
        font = pygame.font.Font(None, 36)

    # Màn hình bắt đầu
    show_start_screen = True
    while show_start_screen:
        clock.tick(FPS)
        draw_start_screen(window, font)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_start_screen = False
    
    # Tạo bản đồ và điểm spawn
    walls, spawn_points,grid = Wall.generate_maze_walls(15, 10)
    # Tạo xe tăng với kiểm tra vị trí hợp lệ
    player1 = Tank(100, 100, GREEN, {
        "up": pygame.K_w, "down": pygame.K_s, 
        "left": pygame.K_a, "right": pygame.K_d, 
        "shoot": pygame.K_SPACE
    })
    enemy_manager = EnemyManager(grid, 53)
    # Đặt player1 vào vị trí spawn hợp lệ
    x1, y1 = find_valid_spawn_position(spawn_points[0], walls)
    player1.set_position(x1, y1)
    player1.angle = 0  # Hướng lên trên
    player2 = Tank(600, 400, RED, {
        "up": pygame.K_UP, "down": pygame.K_DOWN, 
        "left": pygame.K_LEFT, "right": pygame.K_RIGHT, 
        "shoot": pygame.K_RETURN
    })
    
    # Đặt player2 vào vị trí spawn hợp lệ, đảm bảo không đụng player1
    x2, y2 = find_valid_spawn_position(spawn_points[1], walls, player1)
    player2.set_position(x2, y2)
    player2.angle = 180  # Hướng xuống dưới
    # Biến trạng thái game
    player=[player1,player2]
    game_over = False
    winner = ""

    # Vòng lặp chính
    running = True
    while running:
        clock.tick(FPS)
        current_time = time.time()
        window.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    # Khởi động lại game
                    player1.score = 0
                    player2.score = 0
                    player1.bullets.clear()
                    player2.bullets.clear()
                    game_over = False

                    # Tạo bản đồ mới và đặt lại vị trí xe tăng
                    walls, spawn_points,grid = Wall.generate_maze_walls(15, 10)
                    
                    # Đặt player1 vào vị trí spawn hợp lệ
                    x1, y1 = find_valid_spawn_position(spawn_points[0], walls)
                    player1.set_position(x1, y1)
                    
                    # Đặt player2 vào vị trí spawn hợp lệ
                    x2, y2 = find_valid_spawn_position(spawn_points[1], walls, player1)
                    player2.set_position(x2, y2)

        if not game_over:
            keys_pressed = pygame.key.get_pressed()
            
            player1.move(keys_pressed, walls, player2)
            player2.move(keys_pressed, walls, player1)
            enemy_manager.update([player1,player2])   
            enemy_manager.draw(window) 
            # Xử lý bắn
            if keys_pressed[player1.controls["shoot"]]:
                player1.shoot(current_time,gun_sound)

            if keys_pressed[player2.controls["shoot"]]:
                player2.shoot(current_time,gun_sound)

            # Quản lý đạn của player 1
            for bullet in player1.bullets[:]:
                bullet.move()
                
                # Kiểm tra đạn ra ngoài màn hình
                if bullet.is_off_screen() or bullet.is_expired(current_time):
                    player1.bullets.remove(bullet)
                    continue
                
                # Kiểm tra va chạm với xe của player 1 (friendly fire)
                if bullet.get_rect().colliderect(player1.rect):
                    
                    player1.bullets.remove(bullet)
                    shot_sound.play()
                    player2.score += 1
                    continue
                
                # Kiểm tra va chạm với xe của player 2
                if bullet.get_rect().colliderect(player2.rect):
                    player1.bullets.remove(bullet)
                    shot_sound.play()
                    player1.score += 1
                    continue
                
                # Kiểm tra va chạm với tường
                for wall in walls:
                    if bullet.get_rect().colliderect(wall.rect):
                        bullet.bounce(wall.rect)
                        break

            # Quản lý đạn của player 2
            for bullet in player2.bullets[:]:
                bullet.move()
                
                # Kiểm tra đạn ra ngoài màn hình hoặc hết thời gian sống
                if bullet.is_off_screen() or bullet.is_expired(current_time):
                    player2.bullets.remove(bullet)
                    continue
                
                # Kiểm tra va chạm với xe của player 2 (friendly fire)
                if bullet.get_rect().colliderect(player2.rect):
                    player2.bullets.remove(bullet)
                    shot_sound.play()
                    player1.score += 1
                    continue
                
                # Kiểm tra va chạm với xe của player 1
                if bullet.get_rect().colliderect(player1.rect):
                    player2.bullets.remove(bullet)
                    shot_sound.play()
                    player2.score += 1
                    continue
                
                # Kiểm tra va chạm với tường
                for wall in walls:
                    if bullet.get_rect().colliderect(wall.rect):
                        bullet.bounce(wall.rect)
                        break

            # Kiểm tra điều kiện thắng
            if player1.score >= MAX_SCORE or player2.score >= MAX_SCORE:
                winner = "Player 1" if player1.score >= MAX_SCORE else "Player 2"
                game_over = True


        # Vẽ tường
        for wall in walls:
            wall.draw(window)

        # Vẽ xe tăng
        player1.draw(window)
        player2.draw(window)

        # Vẽ điểm số
        score_text = font.render(f"P1: {player1.score}    P2: {player2.score}", True, RED)
        window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))

        # Hiển thị màn hình game over
        if game_over:
            winner_text = font.render(f"{winner} Wins!", True, RED)
            restart_text = font.render("Press R to restart", True, RED)
            window.blit(winner_text, (WIDTH // 2 - winner_text.get_width() // 2, HEIGHT // 2 - 20))
            window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()