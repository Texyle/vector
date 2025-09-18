import pygame
from .constants import *
from .player import Player
from .camera import Camera
from .level import Level
from numpy import float32 as fl
import time
import math

class Engine:    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = None
        self.camera = Camera(0, 0, math.radians(180))
        self.level = Level()
        self.font = pygame.font.SysFont(FONT, 16)
        self.fps = 0
        self.fps_samples = []
        self.max_samples = 10
    
    def handle_events(self, dt: float):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.tick()
                    self.draw(1)
                if event.key == pygame.K_r:
                    self.player.set_position()

    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT]:
            self.camera.move_right(1, dt)
        if keys[pygame.K_LEFT]:
            self.camera.move_right(-1, dt)
        if keys[pygame.K_DOWN]:
            self.camera.move_forward(1, dt)
        if keys[pygame.K_UP]:
            self.camera.move_forward(-1, dt)
        if keys[pygame.K_PERIOD]:
            self.camera.rotate(1, dt)
        if keys[pygame.K_COMMA]:
            self.camera.rotate(-1, dt)

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
    
    def draw(self, dt: float):
        self.screen.fill(BACKGROUND_COLOR)
        
        if CENTER_CAMERA_ON_PLAYER:
            self.camera.set_position(self.player.x, self.player.z)

        self.level.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        self.draw_info_panel()
        
        self.raycast(self.player.x, self.player.y, self.player.z, 0)

        pygame.display.flip()

    def draw_info_panel(self):
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
            
    def reset(self):
        self.player.set_position
        
    def spawn_player(self, x: float, y: float, z: float, f: float):
        self.player = Player(x, y, z, f)
        
    def get_goal_position(self):
        return self.level.get_goal_position()
    
    def get_start_bounds(self):
        return self.level.get_start_bounds()
    
    def get_player_position(self):
        return self.player.get_position()
    
    def get_player_velocity(self):
        return self.player.get_velocity()
    
    def raycast(self, x: float, y: float, z: float, angle: float) -> float:
        for i in range(RAYCAST_NUMBER):
            angle = (i / RAYCAST_NUMBER) * 2 * math.pi
        
            self.level.raycast(x, y, z, 1.0, angle, self.screen, self.camera)
            self.level.raycast(x, y-1, z, 1.0, angle, self.screen, self.camera, inverted=True)
        
        #return self.level.raycast(x, y, z, angle, self.camera)
            
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
            
            self.handle_events(dt)
            self.handle_input(dt)
            
            while accumulator >= tick_interval:
                if not PAUSE:
                    self.tick()
                accumulator -= tick_interval
            
            self.draw(dt)
            
            frame_count += 1
            fps_timer += dt
            if fps_timer >= fps_update_interval:
                self.fps = int(frame_count / fps_timer)
                frame_count = 0
                fps_timer = 0
            