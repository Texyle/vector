from ..bounding_box import BoundingBox
import pygame
from ..camera import Camera
from ..constants import *

class Block:
    def __init__(self, x: int, y: int, z: int, blockage: bool = True, ground: bool = True):
        self.x = x
        self.y = y
        self.z = z
        self.blockage = blockage
        self.ground = ground
        self.bounding_box = []
        self.color = (0, 0, 0)
        
    def get_bounding_box(self) -> list[BoundingBox]:
        return self.bounding_box
    
    def draw(self, surface: pygame.Surface, camera: Camera): 
        for bbox in self.bounding_box:
            corners_world = [
                (bbox.min_x, bbox.min_z),
                (bbox.max_x, bbox.min_z),
                (bbox.max_x, bbox.max_z),
                (bbox.min_x, bbox.max_z)
            ]
            corners_screen = [camera.world_to_screen(x, z) for x, z in corners_world]
            
            on_screen = False
            for screen_x, screen_y in corners_screen:
                if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT):
                    on_screen = True
                    break
            
            if not on_screen:
                return
            
            pygame.draw.polygon(surface, self.color, corners_screen)
            pygame.draw.polygon(surface, (200, 200, 200), corners_screen, 2)