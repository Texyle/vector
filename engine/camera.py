from .constants import *
from numpy import float32 as fl

class Camera:
    def __init__(self, x: fl, z: fl):
        self.x = fl(x)
        self.z = fl(z)
    
    def world_to_screen(self, world_x: fl, world_z: fl) -> tuple[int, int]:
        screen_x = int((world_x - self.x) * BLOCK_SIZE + SCREEN_WIDTH // 2)
        screen_z = int((world_z - self.z) * BLOCK_SIZE + SCREEN_HEIGHT // 2)
        return screen_x, screen_z

    def screen_to_world(self, screen_x: int, screen_z: int) -> tuple[fl, fl]:
        world_x = fl((screen_x - SCREEN_WIDTH // 2) / BLOCK_SIZE + self.x)
        world_z = fl((screen_z - SCREEN_HEIGHT // 2) / BLOCK_SIZE + self.z)
        return world_x, world_z