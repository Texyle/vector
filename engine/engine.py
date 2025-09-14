import pygame
from .constants import *
from .player import Player
from .camera import Camera
from .level import Level
import math
from numpy import float32 as fl

F3_PANEL_WIDTH = 220  # Add this constant near the top if you want

class Engine:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player(fl(0), fl(20), fl(0), fl(180))
        self.camera = Camera(fl(0.0), fl(-0.0))
        self.level = Level()
        self.font = pygame.font.SysFont(FONT, 16)
    
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
        camera_speed = fl(0.1)
        if keys[pygame.K_RIGHT]:
            self.camera.x += camera_speed
        if keys[pygame.K_LEFT]:
            self.camera.x -= camera_speed
        if keys[pygame.K_DOWN]:
            self.camera.z += camera_speed
        if keys[pygame.K_UP]:
            self.camera.z -= camera_speed

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
        for i, line in enumerate(info_lines):
            text_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text_surface, (panel_x + padding, panel_y + padding + i * line_height))

    def run(self):
        self.draw()

        while self.running:
            self.handle_events()
            self.handle_input()

            if not PAUSE:
                self.tick()
                self.draw()

            self.clock.tick(FPS)