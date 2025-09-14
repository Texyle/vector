import pygame
from .blocks.stone import StoneBlock
from .constants import *
from .camera import Camera
from numpy import float32 as fl

class Level:
    def __init__(self):
        self.blocks = []
        self.test()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if DRAW_GRID:
            offset_x = float((camera.x % 1) * BLOCK_SIZE)
            offset_z = float((camera.z % 1) * BLOCK_SIZE)
            
            for x in range(-BLOCK_SIZE, SCREEN_WIDTH + BLOCK_SIZE * 2, BLOCK_SIZE):
                screen_x = x - offset_x
                pygame.draw.line(surface, GRID_COLOR, (screen_x, 0), (screen_x, SCREEN_HEIGHT))
            
            for y in range(-BLOCK_SIZE, SCREEN_HEIGHT + BLOCK_SIZE * 2, BLOCK_SIZE):
                screen_y = y - offset_z
                pygame.draw.line(surface, GRID_COLOR, (0, screen_y), (SCREEN_WIDTH, screen_y))
        
        if DRAW_BLOCK_COORDINATES:
            font = pygame.font.SysFont(FONT, 14)
            
            top_left_world = camera.screen_to_world(0, 0)
            bottom_right_world = camera.screen_to_world(SCREEN_WIDTH, SCREEN_HEIGHT)
            
            start_x = int(top_left_world[0]-1)
            start_y = int(top_left_world[1]-1)
            end_x = int(bottom_right_world[0]) + 1
            end_y = int(bottom_right_world[1]) + 1

            for world_x in range(start_x, end_x):
                for world_y in range(start_y, end_y):
                    screen_x, screen_y = camera.world_to_screen(fl(world_x), fl(world_y))
                    coord_text = f"{world_x},{world_y}"
                    text_surface = font.render(coord_text, True, (200, 200, 200))
                    text_x = screen_x + (BLOCK_SIZE - text_surface.get_width()) // 2
                    text_y = screen_y + (BLOCK_SIZE - text_surface.get_height()) // 2
                    surface.blit(text_surface, (text_x, text_y))
        
        for block in self.blocks:
            screen_x, screen_y = camera.world_to_screen(block.x, block.y)
            
            if (screen_x + BLOCK_SIZE > 0 and screen_x < SCREEN_WIDTH and
                screen_y + BLOCK_SIZE > 0 and screen_y < SCREEN_HEIGHT):
                pygame.draw.rect(surface, block.color, (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(surface, (30, 30, 40), (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE), 1)

    def test(self):
        self.blocks.append(StoneBlock(10, 0, 10))