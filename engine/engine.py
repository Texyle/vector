import pygame
from .constants import *
from .player import Player
from .camera import Camera
from .level import Level
from numpy import float32 as fl
import time
import math
import os
import csv

class Engine:    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Vector Engine")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player()
        self.camera = Camera(0, 0, math.radians(180))
        self.level = Level()
        self.font = pygame.font.SysFont(FONT, 16)
        self.fps = 0
        self.fps_samples = []
        self.max_samples = 10
        self.tick_rate = 1000
        self.do_draw = False
        self.last_player = None
        self.recent_attempts = []
        
        self.offset_x = -999.0
        self.offset_z = -999.0
        self.total_offset = -999.0
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.tick()
                    self.draw(1)
                if event.key == pygame.K_r:
                    self.player.set_position()
                if event.key == pygame.K_t:
                    if self.tick_rate == TICK_RATE:
                        self.tick_rate = 1000
                    else:
                        self.tick_rate = TICK_RATE
                if event.key == pygame.K_y:
                    self.do_draw = not self.do_draw

    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_t]:
            if self.tick_rate == TICK_RATE:
                self.tick_rate = 1000
            else:
                self.tick_rate = TICK_RATE

        # if keys[pygame.K_RIGHT]:
        #     self.camera.move_right(1, dt)
        # if keys[pygame.K_LEFT]:
        #     self.camera.move_right(-1, dt)
        # if keys[pygame.K_DOWN]:
        #     self.camera.move_forward(1, dt)
        # if keys[pygame.K_UP]:
        #     self.camera.move_forward(-1, dt)
        # if keys[pygame.K_PERIOD]:
        #     self.camera.rotate(1, dt)
        # if keys[pygame.K_COMMA]:
        #     self.camera.rotate(-1, dt)

        # Player movement controls        
        if keys[pygame.K_LCTRL] or TOGGLE_SPRINT:
            self.player.set_sprint(True)
        else:
            self.player.set_sprint(False)
        if keys[pygame.K_SPACE]:
            self.player.jump()
        self.player.set_movement(keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d])

    def tick(self):
        self.player.tick(self.level, self.camera)
        self.last_player = self.player
        self.check_offset()
    
    def draw(self, active_keys = {}, ai_info = []):
        if not self.do_draw:
            return
        
        self.screen.fill(BACKGROUND_COLOR)
        
        if CENTER_CAMERA_ON_PLAYER:
            self.camera.set_position(self.player.x, self.player.z)

        self.level.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        self.draw_info_panel(ai_info)
        self.draw_keystrokes(active_keys)
        
        pygame.display.flip()

    def draw_info_panel(self, ai_info: list = []):
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, INFO_PANEL_WIDTH, SCREEN_HEIGHT))

        panel_x = 0
        panel_y = 0
        line_height = 30
        padding = 10
        info_lines = self.player.get_info_text()
        info_lines.insert(0, f"FPS: {self.fps}")
        for i, line in enumerate(info_lines):
            text_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text_surface, (panel_x + padding, panel_y + padding + i * line_height))
            
        for i, line in enumerate(ai_info):
            text_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text_surface, (panel_x + padding, panel_y + padding + (i + 12) * line_height))
            
    def draw_keystrokes(self, active_keys = {}):
        if len(active_keys) == 0:
            return
        
        key_size = 50
        spacing = 10
        base_x = 20
        base_y = 550
        
        # Key colors
        inactive_color = (100, 100, 100) # Grey
        active_color = (255, 255, 255)  # White

        # Define key layouts and positions
        key_positions = {
            'W': (base_x + key_size + spacing, base_y),
            'A': (base_x, base_y + key_size + spacing),
            'S': (base_x + key_size + spacing, base_y + key_size + spacing),
            'D': (base_x + 2 * (key_size + spacing), base_y + key_size + spacing),
            'space': (base_x, base_y + 2 * (key_size + spacing)),
            'sprint': (base_x, base_y + 3 * (key_size + spacing))
        }
        
        # Define key labels and sizes
        key_info = {
            'W': {'label': 'W', 'width': key_size, 'height': key_size},
            'A': {'label': 'A', 'width': key_size, 'height': key_size},
            'S': {'label': 'S', 'width': key_size, 'height': key_size},
            'D': {'label': 'D', 'width': key_size, 'height': key_size},
            'space': {'label': 'space', 'width': 3 * key_size + 2 * spacing, 'height': key_size},
            'sprint': {'label': 'sprint', 'width': key_size, 'height': key_size},
        }
        
        font = pygame.font.Font(None, 24)
                        
        for key, pos in key_positions.items():
            key_data = key_info[key]
            width = key_data['width']
            height = key_data['height']
            label = key_data['label']

            # Determine color based on whether the key is active
            color = active_color if active_keys[key] else inactive_color
            
            # Draw the rectangle
            pygame.draw.rect(self.screen, color, (pos[0], pos[1], width, height))
            
            # Render the text
            text_surface = font.render(label, True, active_color)
            text_rect = text_surface.get_rect(center=(pos[0] + width / 2, pos[1] + height / 2))
            self.screen.blit(text_surface, text_rect)
            
    def draw_recent_attempts(self, attempts):
        start_x = SCREEN_WIDTH - 100
        start_y = 0
        line_height = 30
        
        attempts.insert(0, f"Recent attempts:")
        
        for i, line in enumerate(attempts):
            text_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text_surface, (start_x, start_y + (i + 12) * line_height))
            
    def reset(self):
        self.player.set_position()
        self.player.reset_macro()
        self.offset_x = -999.0
        self.offset_z = -999.0
        self.total_offset = -999.0
        
    def spawn_player(self, x: float, y: float, z: float, f: float):
        self.player = Player(x, y, z, f)
        
    def get_goal(self):
        return self.level.goal_x, self.level.goal_y, self.level.goal_z
    
    def get_player_bbox(self):
        return self.player.get_bounding_box()
    
    def get_start_bounds(self):
        return self.level.get_start_bounds()
    
    def get_player_position(self):
        return self.player.get_position()
    
    def get_player_velocity(self):
        return self.player.get_velocity()
    
    def get_distance_to_ground(self):
        return self.player.get_distance_to_ground()
    
    def get_player_facing(self):
        return self.player.facing
    
    def save_macro(self, name, iteration):
        if not self.player.macro:
            print("Macro buffer is empty. Skipping save.")
            return

        filename = f"{name}_{iteration}.csv"
        filepath = os.path.join("macros", filename)
        os.makedirs("macros", exist_ok=True)

        header = [
            "X", "Y", "Z", "YAW", "PITCH", "ANGLE_X", "ANGLE_Y",
            "W", "A", "S", "D", "SPRINT", "SNEAK", "JUMP", "LMB", "RMB",
            "VEL_X", "VEL_Y", "VEL_Z"
        ]

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write the spawn coordinates on the first line
                spawn_coords = [
                    self.player.spawn_x,
                    self.player.spawn_y,
                    self.player.spawn_z,
                    self.player.spawn_f
                ]
                writer.writerow(spawn_coords)
                
                # Write the header
                writer.writerow(header)
                
                # Write the macro data
                for row in self.player.macro:
                    writer.writerow(row)
            
            print("Macro data saved successfully.")
        except IOError as e:
            print(f"Error saving macro data: {e}")

        self.player.macro = []
    
    def raycast(self, x: float, y: float, z: float, height: float, angle: float, inverted: bool = True) -> float:
        return self.level.raycast(x, y, z, height, angle, self.screen, self.camera, inverted)
    
    def check_offset(self):
        start_x, _, start_z = self.level.get_start_bounds().get_center()
        
        if self.level.goal_x < start_x:
            invert_x = False
        else:
            invert_x = True
            
        if self.level.goal_z > start_z:
            invert_z = False
        else:
            invert_z = True
            
        landed, offset_x, offset_z, total_offset = self.player.get_offset(self.level.goal_x, self.level.goal_y, self.level.goal_z, self.level.landing_mode, invert_x, invert_z)
        if landed:
            self.offset_x = offset_x
            self.offset_z = offset_z
            self.total_offset = total_offset
            
    def reached_goal(self):
        if self.total_offset > 0:
            return True
        
        return False
    
    def player_died(self):
        if self.player.y < self.level.goal_y:
            return True
        
        return False
    
    def is_colliding_wall(self):
        return self.player.is_colliding
    
    def apply_player_input(self, keys, mouse_delta):
        self.player.turn(mouse_delta)
        # self.player.set_sprint(keys['sprint'])
        self.player.set_movement(keys['W'], keys['A'], keys['S'], keys['D'], keys['sprint'], keys['space'])
        # if keys['space']:
        #     self.player.jump()
            
    def run(self):
        frame_count = 0
        fps_update_interval = 0.5
        fps_timer = 0
        
        tick_interval = 1.0 / TICK_RATE
        accumulator = 0.0
        previous_time = time.time()
        
        self.player = Player(0.5, 11, -0.29999, 0)
        
        while self.running:
            current_time = time.time()
            dt = current_time - previous_time
            previous_time = current_time
            
            if dt > 0.25:
                dt = 0.25
                
            accumulator += dt
            
            self.handle_events()
            self.handle_input(dt)
            
            while accumulator >= tick_interval:
                if not PAUSE:
                    self.tick()
                accumulator -= tick_interval
            
            self.draw()
            
            frame_count += 1
            fps_timer += dt
            if fps_timer >= fps_update_interval:
                self.fps = int(frame_count / fps_timer)
                frame_count = 0
                fps_timer = 0
            