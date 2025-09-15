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
        self.player = Player(1, 20, 1, 0)
        self.camera = Camera(0, 0, math.radians(90))
        self.level = Level()
        self.font = pygame.font.SysFont(FONT, 16)
        self.fps = 0
        self.fps_samples = []
        self.max_samples = 10
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.tick()
                    self.draw()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Camera movement controls
        camera_speed = 0.2
        camera_rotation_speed = 0.05

        if keys[pygame.K_RIGHT]:
            self.camera.move_right(camera_speed)
        if keys[pygame.K_LEFT]:
            self.camera.move_right(-camera_speed)
        if keys[pygame.K_DOWN]:
            self.camera.move_forward(camera_speed)
        if keys[pygame.K_UP]:
            self.camera.move_forward(-camera_speed)
        if keys[pygame.K_PERIOD]:
            self.camera.rotate(camera_rotation_speed)
        if keys[pygame.K_COMMA]:
            self.camera.rotate(-camera_rotation_speed)

        # Player movement controls
        self.player.set_movement(keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d])

    def tick(self):
        self.player.tick()
    
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        self.level.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        self.draw_info_panel()

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

    def run(self):
        last_time = time.time()
        frame_count = 0
        fps_update_interval = 0.5  # Update FPS every 0.5 seconds
        fps_timer = 0
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            frame_count += 1
            fps_timer += dt
            
            # Update FPS at regular intervals to reduce flickering
            if fps_timer >= fps_update_interval:
                self.fps = int(frame_count / fps_timer)
                frame_count = 0
                fps_timer = 0
            
            self.handle_events()
            self.handle_input()

            if not PAUSE:
                self.tick()
            
            self.draw()
            #self.clock.tick(FPS)