from .constants import *
from numpy import float32 as fl
import math

class Camera:
    def __init__(self, x: float, z: float, rotation: float):
        self.x = x
        self.z = z
        self.rotation = rotation
        
    def rotate(self, direction: int, dt: float):
        self.rotation += CAMERA_ROTATION_SPEED * direction * dt
    
    def set_rotation(self, angle):
        self.rotation = angle
        
    def set_position(self, x: float, z: float):
        self.x = x
        self.z = z
        
    def get_forward_vector(self):
        return math.sin(self.rotation), math.cos(self.rotation)
    
    def get_right_vector(self):
        return math.cos(self.rotation), -math.sin(self.rotation)
    
    def move_forward(self, direction: int, dt: float):
        dx, dz = self.get_forward_vector()
        self.x += dx * CAMERA_MOVEMENT_SPEED * direction * dt
        self.z += dz * CAMERA_MOVEMENT_SPEED * direction * dt
    
    def move_right(self, direction: int, dt: float):
        dx, dz = self.get_right_vector()
        self.x += dx * CAMERA_MOVEMENT_SPEED * direction * dt
        self.z += dz * CAMERA_MOVEMENT_SPEED * direction * dt
    
    def world_to_screen(self, world_x, world_z):
        rel_x = world_x - self.x
        rel_z = world_z - self.z
        
        if self.rotation != 0:
            cos_angle = math.cos(self.rotation)
            sin_angle = math.sin(self.rotation)
            rotated_x = rel_x * cos_angle - rel_z * sin_angle
            rotated_z = rel_x * sin_angle + rel_z * cos_angle
        else:
            rotated_x = rel_x
            rotated_z = rel_z
        
        screen_x = SCREEN_WIDTH // 2 + int(rotated_x * BLOCK_SIZE)
        screen_y = SCREEN_HEIGHT // 2 + int(rotated_z * BLOCK_SIZE)
        
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        rel_x = (screen_x - SCREEN_WIDTH // 2) / BLOCK_SIZE
        rel_z = (screen_y - SCREEN_HEIGHT // 2) / BLOCK_SIZE
        
        if self.rotation != 0:
            cos_angle = math.cos(-self.rotation)
            sin_angle = math.sin(-self.rotation)
            world_x = rel_x * cos_angle - rel_z * sin_angle
            world_z = rel_x * sin_angle + rel_z * cos_angle
        else:
            world_x = rel_x
            world_z = rel_z
        
        return world_x + self.x, world_z + self.z