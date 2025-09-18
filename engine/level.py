import pygame
from .blocks.stone import StoneBlock
from .blocks.glass_pane import GlassPane, Connection
from .constants import *
from .camera import Camera
from .bounding_box import BoundingBox
import numpy as np
import math
from .utils import *

class Level:
    def __init__(self):
        self.blocks = []
        self.start_bounds = None
        self.test()
        self.coordinates_font = pygame.font.SysFont(FONT, 14)

    def draw(self, surface: pygame.Surface, camera: Camera):
        screen_corners_world = [
            camera.screen_to_world(-BLOCK_SIZE, -BLOCK_SIZE),
            camera.screen_to_world(SCREEN_WIDTH + BLOCK_SIZE, -BLOCK_SIZE),
            camera.screen_to_world(SCREEN_WIDTH + BLOCK_SIZE, SCREEN_HEIGHT + BLOCK_SIZE),
            camera.screen_to_world(-BLOCK_SIZE, SCREEN_HEIGHT + BLOCK_SIZE)
        ]
        
        world_x_coords = [corner[0] for corner in screen_corners_world]
        world_z_coords = [corner[1] for corner in screen_corners_world]
        
        start_x = int(min(world_x_coords)) - 1
        end_x = int(max(world_x_coords)) + 1
        start_z = int(min(world_z_coords)) - 1
        end_z = int(max(world_z_coords)) + 1
        start_y = 0
        end_y = 100
        
        if DRAW_GRID:
            self.draw_grid(surface, camera, start_x, end_x, start_z, end_z)
        
        visible_blocks = self.get_blocks_in_area(start_x, end_x, start_y, end_y, start_z, end_z)
        for block in visible_blocks:
            block.draw(surface, camera)
        
        if DRAW_BLOCK_COORDINATES:
            self.draw_coordinates(surface, camera, visible_blocks)
            
        if DRAW_START_BOUNDS:
            self.draw_start_bounds(surface, camera)
            
    def draw_start_bounds(self, surface: pygame.Surface, camera: Camera):
        corners_world = [
            (self.start_bounds.min_x, self.start_bounds.min_z),
            (self.start_bounds.max_x, self.start_bounds.min_z),
            (self.start_bounds.max_x, self.start_bounds.max_z),
            (self.start_bounds.min_x, self.start_bounds.max_z)
        ]
        
        corners_screen = [camera.world_to_screen(x, z) for x, z in corners_world]
        
        on_screen = False
        for screen_x, screen_y in corners_screen:
            if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT):
                on_screen = True
                break
        
        if not on_screen:
            return
        
        pygame.draw.polygon(surface, START_BOUNDS_COLOR, corners_screen, 2)

    def draw_grid(self, surface: pygame.Surface, camera: Camera, start_x: int, end_x: int, start_z: int, end_z: int):
        for x in range(start_x, end_x + 1):
            start_screen = camera.world_to_screen(x, start_z)
            end_screen = camera.world_to_screen(x, end_z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)
        
        for z in range(start_z, end_z + 1):
            start_screen = camera.world_to_screen(start_x, z)
            end_screen = camera.world_to_screen(end_x, z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)

    def draw_coordinates(self, surface: pygame.Surface, camera: Camera, blocks):
        for block in blocks:
            center_screen = camera.world_to_screen(block.x+0.5, block.z+0.5)
            
            if not (0 <= center_screen[0] < SCREEN_WIDTH and 0 <= center_screen[1] < SCREEN_HEIGHT):
                continue
            
            coord_text = f"{int(block.x)},{int(block.z)}"
            text_surface = self.coordinates_font.render(coord_text, True, (200, 200, 200))
            
            text_x = center_screen[0] - text_surface.get_width() // 2
            text_y = center_screen[1] - text_surface.get_height() // 2
            
            surface.blit(text_surface, (text_x, text_y))
            
    def check_collision(self, bounding_box: BoundingBox) -> BoundingBox:
        blocks = self.get_blocks_in_area(int(bounding_box.min_x)-1, int(bounding_box.max_x)+1,
                                         int(bounding_box.min_y), int(bounding_box.max_y),
                                         int(bounding_box.min_z)-1, int(bounding_box.max_z)+1)
        
        for block in blocks:
            if block.blockage is False:
                continue
            
            block_bboxes = block.get_bounding_box()
            
            for bbox in block_bboxes:
                if self.bbox_intersect(bounding_box, bbox):
                    return bbox
            
        return None

    def bbox_intersect(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        return (bbox1.min_x < bbox2.max_x and 
                bbox1.max_x > bbox2.min_x and
                bbox1.min_y < bbox2.max_y and
                bbox1.max_y > bbox2.min_y and
                bbox1.min_z < bbox2.max_z and
                bbox1.max_z > bbox2.min_z)

    def get_blocks_in_area(self, start_x: int, end_x: int, start_y: int, end_y: int, start_z: int, end_z: int):
        return [block for block in self.blocks 
                if start_x <= block.x <= end_x and start_z <= block.z <= end_z and start_y <= block.y <= end_y]
        
    def get_goal_position(self):
        for block in self.blocks:
            if block.goal:
                return block.x+0.5, block.y+1, block.z+0.5
            
    def get_start_bounds(self) -> BoundingBox:
        return self.start_bounds
    
    def raycast(self, x: float, y: float, z: float, height: float, angle: float, surface: pygame.Surface, camera: Camera, inverted: bool = False) -> float:
        dir_x = math.cos(angle)
        dir_z = math.sin(angle)
        dir_y = 0
        
        end_x = x + dir_x * MAX_RAYCAST_DISTANCE
        end_z = z + dir_z * MAX_RAYCAST_DISTANCE

        if not inverted:
            blocks = self.get_blocks_along_ray(x, y, z, end_x, y + height, end_z)
            hit, closest_hit = self.normal_raycast(x, y, z, height, dir_x, dir_y, dir_z, blocks)
        else:
            hit, closest_hit = self.inverted_raycast(x, y, z, height, dir_x, dir_y, dir_z, 0)
        
        if DRAW_RAYCAST_LINES:
            player_x, player_y = camera.world_to_screen(x, z)
            screen_x, screen_y = camera.world_to_screen(x + dir_x * closest_hit, z + dir_z * closest_hit)
            pygame.draw.line(surface, RAYCAST_COLOR, (player_x, player_y), (screen_x, screen_y), 1)
            
        if DRAW_RAYCASTS_HITS and hit:
            hit_x = x + dir_x * closest_hit
            hit_z = z + dir_z * closest_hit
            screen_x, screen_y = camera.world_to_screen(hit_x, hit_z)
            cross_size = 4
            thickness = 2
            
            if inverted:
                color = RAYCAST_GROUND_HIT_COLOR
            else:
                color = RAYCAST_BLOCKAGE_HIT_COLOR
            
            pygame.draw.line(surface, color,
                            (screen_x - cross_size, screen_y - cross_size),
                            (screen_x + cross_size, screen_y + cross_size),
                            thickness)

            pygame.draw.line(surface, color,
                            (screen_x + cross_size, screen_y - cross_size),
                            (screen_x - cross_size, screen_y + cross_size),
                            thickness)
            
        return closest_hit
    
    def normal_raycast(self, x, y, z, height, dir_x, dir_y, dir_z, blocks):
        closest_hit = MAX_RAYCAST_DISTANCE
        hit = False
        
        for block in blocks:         
            if not block.blockage:
                continue
            
            for bbox in block.get_bounding_box():
                hit_distance = ray_bbox_intersection(
                    x, y, z, dir_x, dir_y, dir_z,
                    bbox.min_x, bbox.max_x,
                    bbox.min_y, bbox.max_y,
                    bbox.min_z, bbox.max_z, height)
                
                if hit_distance is not None and hit_distance < closest_hit:
                    closest_hit = hit_distance
                    hit = True
                    
        return hit, closest_hit
    
    def inverted_raycast(self, x, y, z, height, dir_x, dir_y, dir_z, distance):
        if distance > MAX_RAYCAST_DISTANCE:
            return False, MAX_RAYCAST_DISTANCE
        
        block = self.get_block_at(x, y, z, height)
        
        if block is None:
            return True, distance
        
        for bbox in block.get_bounding_box():
            exit_point = find_exit_point(x, y, z, dir_x, dir_y, dir_z, bbox)
            if exit_point is None:
                print("what?")
                continue
            
            next_x = exit_point[0] + dir_x * INVERTED_RAYCAST_STEP
            next_y = exit_point[1] + dir_y * INVERTED_RAYCAST_STEP
            next_z = exit_point[2] + dir_z * INVERTED_RAYCAST_STEP
                        
            return self.inverted_raycast(next_x, next_y, next_z, height, dir_x, dir_y, dir_z, distance + exit_point[3])
        
        return False, 0
            

    def find_adjacent_block(self, x, z, height, direction, blocks):        
        search_x = x + direction[0]
        search_z = z + direction[1]
        
        for block in blocks:
            for bbox in block.get_bounding_box():
                if point_in_bbox(search_x, 0, search_z, bbox, height):
                    return block
        
        return None
    
    def get_block_at(self, x, y, z, height = 0):
        if x < 0:
            search_x = math.floor(x-1)
        else:
            search_x = math.floor(x)
            
        if z < 0:
            search_z = math.floor(z-1)
        else:
            search_z = math.floor(z)
        
        search_y_min = math.floor(y)
        search_y_max = math.floor(y+height)
        
        for block in self.blocks:
            if block.x == search_x and (block.y == search_y_min or block.y == search_y_max) and block.z == search_z:
                return block
            
        return None
            
    def get_blocks_along_ray(self, start_x, start_y, start_z, end_x, end_y, end_z):
        min_x = min(start_x, end_x)
        max_x = max(start_x, end_x)
        min_y = min(start_y, end_y)
        max_y = max(start_y, end_y)
        min_z = min(start_z, end_z)
        max_z = max(start_z, end_z)
        
        return self.get_blocks_in_area(
            int(min_x), int(max_x),
            int(min_y), int(max_y),
            int(min_z), int(max_z)
        )

    def test(self):
        self.start_bounds = BoundingBox(-0.3, 1.3, 11, 11, -0.3, 1.3)
        self.blocks.append(StoneBlock(0, 10, 0))
        self.blocks.append(StoneBlock(0, 10, 1))
        self.blocks.append(StoneBlock(3, 11, 0))
        self.blocks.append(StoneBlock(-3, 12, 0))
        self.blocks.append(StoneBlock(0, 10, 5, goal=True))
